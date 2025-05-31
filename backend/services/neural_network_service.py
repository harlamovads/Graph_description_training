# backend/services/neural_network_service.py
import torch
import nltk
import re
import difflib
from transformers import (
    T5Tokenizer, 
    T5ForConditionalGeneration, 
    ElectraTokenizer, 
    ElectraForTokenClassification
)
import torch.nn as nn
from flask import current_app
import os
import json
import re

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class HuggingFaceT5GEDInference:
    def __init__(self, model_name="Zlovoblachko/REAlEC_2step_model_testing", 
                 ged_model_name="Zlovoblachko/11tag-electra-grammar-stage2", device=None):
        """
        Initialize the inference class for T5-GED model from HuggingFace
        """
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Correct id2label mapping from Gradio app
        self.id2label = {
            0: "correct",
            1: "ORTH",
            2: "FORM", 
            3: "MORPH",
            4: "DET",
            5: "POS",
            6: "VERB",
            7: "NUM",
            8: "WORD",
            9: "PUNCT",
            10: "RED",
            11: "MULTIWORD",
            12: "SPELL"
        }
        
        # Load GED model and tokenizer
        print(f"Loading GED model from HuggingFace: {ged_model_name}...")
        self.ged_model, self.ged_tokenizer = self._load_ged_model(ged_model_name)
        
        # Load T5 model and tokenizer from HuggingFace
        print(f"Loading T5 model from HuggingFace: {model_name}...")
        self.t5_tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.t5_model = T5ForConditionalGeneration.from_pretrained(model_name)
        self.t5_model.to(self.device)
        
        # Create GED encoder (copy of T5 encoder)
        self.ged_encoder = T5ForConditionalGeneration.from_pretrained(model_name).encoder
        self.ged_encoder.to(self.device)
        
        # Create gating mechanism
        encoder_hidden_size = self.t5_model.config.d_model
        self.gate = nn.Linear(2 * encoder_hidden_size, 1)
        self.gate.to(self.device)
        
        # Try to load GED components from HuggingFace
        try:
            print("Loading GED components...")
            from huggingface_hub import hf_hub_download
            ged_components_path = hf_hub_download(
                repo_id=model_name,
                filename="ged_components.pt",
                cache_dir=None
            )
            ged_components = torch.load(ged_components_path, map_location=self.device)
            self.ged_encoder.load_state_dict(ged_components["ged_encoder"])
            self.gate.load_state_dict(ged_components["gate"])
            print("GED components loaded successfully!")
        except Exception as e:
            print(f"Warning: Could not load GED components: {e}")
            print("Using default initialization for GED encoder and gate.")
        
        # Set to evaluation mode
        self.t5_model.eval()
        self.ged_encoder.eval()
        self.gate.eval()
        
    def _load_ged_model(self, model_name):
        """Load GED model and tokenizer from HuggingFace"""
        tokenizer = ElectraTokenizer.from_pretrained(model_name)
        model = ElectraForTokenClassification.from_pretrained(model_name)
        model.to(self.device)
        model.eval()
        return model, tokenizer
    
    def _get_ged_predictions(self, text):
        """Get GED predictions for input text"""
        inputs = self.ged_tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.ged_model(**inputs)
            logits = outputs.logits
        predictions = torch.argmax(logits, dim=2)
        token_predictions = predictions[0].cpu().numpy().tolist()
        tokens = self.ged_tokenizer.convert_ids_to_tokens(inputs.input_ids[0])
        
        ged_tags = []
        for token, pred in zip(tokens, token_predictions):
            if token.startswith("##") or token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            ged_tags.append(str(pred))
        
        return " ".join(ged_tags), tokens, token_predictions
    
    def _get_error_spans_detailed(self, text):
        """Extract error spans with detailed second_level_tag categories - CORRECT VERSION"""
        ged_tags_str, tokens, predictions = self._get_ged_predictions(text)
        
        error_spans = []
        error_types = []
        clean_tokens = []
        
        for token, pred in zip(tokens, predictions):
            if token.startswith("##") or token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            clean_tokens.append(token)
            
            if pred != 0:  # 0 is correct, others are various error types
                error_type = self.id2label.get(pred, "OTHER")
                error_types.append(error_type)
                
                error_spans.append({
                    "token": token,
                    "type": error_type,
                    "position": len(clean_tokens) - 1
                })
        
        return error_spans, list(set(error_types))
    
    def _preprocess_inputs(self, text, max_length=128):
        """Preprocess input text exactly as during training"""
        # Get GED predictions
        ged_tags, _, _ = self._get_ged_predictions(text)
        
        # Tokenize source text
        src_tokens = self.t5_tokenizer(
            text, 
            truncation=True, 
            max_length=max_length, 
            return_tensors="pt"
        )
        
        # Tokenize GED tags
        ged_tokens = self.t5_tokenizer(
            ged_tags, 
            truncation=True, 
            max_length=max_length, 
            return_tensors="pt"
        )
        
        return {
            "input_ids": src_tokens.input_ids.to(self.device),
            "attention_mask": src_tokens.attention_mask.to(self.device),
            "ged_input_ids": ged_tokens.input_ids.to(self.device),
            "ged_attention_mask": ged_tokens.attention_mask.to(self.device)
        }
    
    def _forward_with_ged(self, input_ids, attention_mask, ged_input_ids, ged_attention_mask, max_length=200):
        """Forward pass with GED integration"""
        # Get source encoder outputs
        src_encoder_outputs = self.t5_model.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=True
        )
        
        # Get GED encoder outputs
        ged_encoder_outputs = self.ged_encoder(
            input_ids=ged_input_ids,
            attention_mask=ged_attention_mask,
            return_dict=True
        )
        
        # Get hidden states
        src_hidden_states = src_encoder_outputs.last_hidden_state
        ged_hidden_states = ged_encoder_outputs.last_hidden_state
        
        # Combine hidden states
        min_len = min(src_hidden_states.size(1), ged_hidden_states.size(1))
        combined = torch.cat([
            src_hidden_states[:, :min_len, :],
            ged_hidden_states[:, :min_len, :]
        ], dim=2)
        
        # Apply gating mechanism
        gate_scores = torch.sigmoid(self.gate(combined))
        combined_hidden = (
            gate_scores * src_hidden_states[:, :min_len, :] +
            (1 - gate_scores) * ged_hidden_states[:, :min_len, :]
        )
        
        # Update encoder outputs
        src_encoder_outputs.last_hidden_state = combined_hidden
        
        # Generate using T5 decoder
        decoder_outputs = self.t5_model.generate(
            encoder_outputs=src_encoder_outputs,
            max_length=max_length,
            do_sample=False,
            num_beams=1
        )
        
        return decoder_outputs
    
    def correct_text(self, text, max_length=200):
        """Correct grammatical errors in input text"""
        # Preprocess inputs
        inputs = self._preprocess_inputs(text)
        
        # Generate correction using GED-enhanced model
        with torch.no_grad():
            generated_ids = self._forward_with_ged(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                ged_input_ids=inputs["ged_input_ids"],
                ged_attention_mask=inputs["ged_attention_mask"],
                max_length=max_length
            )
        
        # Decode output
        corrected_text = self.t5_tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        return corrected_text
    
    def analyze_text(self, text):
        """Enhanced analysis method for Flask integration"""
        if not text.strip():
            return {"error": "Please enter some text."}

        try:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if not clean_text:
                return {"error": "Please enter some text."}
            corrected_text = self.correct_text(clean_text)
            error_spans, error_types = self._get_error_spans_detailed(clean_text)
            html_output = self.generate_html_analysis(clean_text, corrected_text, error_spans)
            return {
                "corrected_text": corrected_text,
                "error_spans": error_spans,
                "error_types": error_types,  # Add this for compatibility
                "html_output": html_output
            }
        
        except Exception as e:
            return {"error": f"Error during analysis: {str(e)}"}
    
    def generate_html_analysis(self, original, corrected, error_spans):
        """Generate enhanced HTML analysis output with correct error types"""
        # Create highlighted original text
        highlighted_original = original
        if error_spans:
            # Sort by position in reverse to avoid index shifting
            sorted_spans = sorted(error_spans, key=lambda x: x['position'], reverse=True)
            
            # Color coding for different error types - using actual GED tags
            color_map = {
                "ORTH": "#ffebee",      # Light red - Orthography
                "FORM": "#e8f5e8",      # Light green - Word form
                "MORPH": "#fff3e0",     # Light orange - Morphology
                "DET": "#e3f2fd",       # Light blue - Determiners
                "POS": "#f3e5f5",       # Light purple - Part of speech
                "VERB": "#fce4ec",      # Light pink - Verb errors
                "NUM": "#e0f2f1",       # Light teal - Number
                "WORD": "#fff8e1",      # Light yellow - Word choice
                "PUNCT": "#efebe9",     # Light brown - Punctuation
                "RED": "#ffebee",       # Light red - Redundancy
                "MULTIWORD": "#e8eaf6", # Light indigo - Multi-word
                "SPELL": "#fcf4ff"      # Light magenta - Spelling
            }
            
            # Simple highlighting
            for span in sorted_spans:
                token = span['token']
                error_type = span['type']
                
                color = color_map.get(error_type, "#f5f5f5")
                
                # Simple token replacement (basic highlighting)
                if token in highlighted_original:
                    highlighted_original = highlighted_original.replace(
                        token, 
                        f"<span style='background-color: {color}; padding: 1px 3px; border-radius: 3px; margin: 0 1px;' title='{error_type}: {token}'>{token}</span>",
                        1
                    )
        
        html = f"""
        <div style='font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9;'>
            <h3 style='color: #333; margin-top: 0;'>Enhanced Grammar Analysis Results</h3>
            
            <div style='margin: 15px 0;'>
                <h4 style='color: #555;'>Original Text with Error Highlighting:</h4>
                <div style='padding: 10px; background-color: #fff; border: 1px solid #ddd; border-radius: 4px;'>{highlighted_original}</div>
            </div>
            
            <div style='margin: 15px 0;'>
                <h4 style='color: #28a745;'>Corrected Text:</h4>
                <p style='padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px;'>{corrected}</p>
            </div>
            
            <div style='margin: 15px 0;'>
                <h4 style='color: #333;'>Error Summary:</h4>
                <p style='color: #666;'>Found {len(error_spans)} potential issues</p>
                
                <div style='margin-top: 10px;'>
                    <span style='display: inline-block; margin: 2px 5px; padding: 2px 8px; background-color: #ffebee; border-radius: 12px; font-size: 12px;'>ORTH - Orthography</span>
                    <span style='display: inline-block; margin: 2px 5px; padding: 2px 8px; background-color: #e8f5e8; border-radius: 12px; font-size: 12px;'>FORM - Word Form</span>
                    <span style='display: inline-block; margin: 2px 5px; padding: 2px 8px; background-color: #fff3e0; border-radius: 12px; font-size: 12px;'>MORPH - Morphology</span>
                    <span style='display: inline-block; margin: 2px 5px; padding: 2px 8px; background-color: #e3f2fd; border-radius: 12px; font-size: 12px;'>DET - Determiners</span>
                    <span style='display: inline-block; margin: 2px 5px; padding: 2px 8px; background-color: #fcf4ff; border-radius: 12px; font-size: 12px;'>SPELL - Spelling</span>
                </div>
            </div>
        </div>
        """
        return html


# Utility functions for finding differences
def find_differences(source, corrected):
    """Find differences between source and corrected text."""
    diff = difflib.ndiff(source.split(), corrected.split())
    changes = []
    for i, s in enumerate(diff):
        if s.startswith('- '):
            changes.append({"type": "deletion", "text": s[2:], "position": i})
        elif s.startswith('+ '):
            changes.append({"type": "addition", "text": s[2:], "position": i})
    return changes


def process_text(text, model):
    """Process input text by splitting into sentences and applying the model."""
    if not text.strip():
        return {"error": "Please enter some text."}
    
    try:
        sentences = nltk.sent_tokenize(text)
    except LookupError:
        nltk.download('punkt')
        sentences = nltk.sent_tokenize(text)
    
    results = []
    for sentence in sentences:
        # Use the enhanced model's analyze_text method
        analysis = model.analyze_text(sentence)
        
        if "error" in analysis:
            results.append({
                "original": sentence,
                "corrected": sentence,
                "error_spans": [],
                "error_types": [],
                "changes": []
            })
        else:
            corrected = analysis["corrected_text"]
            error_spans = analysis["error_spans"]
            error_types = analysis.get("error_types", [])
            changes = find_differences(sentence, corrected)
            
            results.append({
                "original": sentence,
                "corrected": corrected,
                "error_spans": error_spans,
                "error_types": error_types,
                "changes": changes
            })
    
    return results


def generate_html_output(results):
    """Generate HTML output from analysis results with highlighted errors and corrections."""
    html_output = "<div style='font-family: Arial, sans-serif; line-height: 1.6;'>"
    
    for i, result in enumerate(results):
        html_output += f"<div style='margin-bottom: 25px; padding: 20px; border-radius: 8px; background-color: #f8f9fa; border-left: 4px solid #007bff;'>"
        
        # Sentence number
        html_output += f"<h4 style='margin-top: 0; color: #333;'>Sentence {i + 1}</h4>"
        
        # Original sentence with highlighted errors
        original = result["original"]
        error_spans = result["error_spans"]
        
        if error_spans:
            # Create highlighted version
            marked_original = original
            
            # Color mapping for actual GED tags
            color_map = {
                "ORTH": "#ffebee",      # Light red - Orthography
                "FORM": "#e8f5e8",      # Light green - Word form
                "MORPH": "#fff3e0",     # Light orange - Morphology
                "DET": "#e3f2fd",       # Light blue - Determiners
                "POS": "#f3e5f5",       # Light purple - Part of speech
                "VERB": "#fce4ec",      # Light pink - Verb errors
                "NUM": "#e0f2f1",       # Light teal - Number
                "WORD": "#fff8e1",      # Light yellow - Word choice
                "PUNCT": "#efebe9",     # Light brown - Punctuation
                "RED": "#ffebee",       # Light red - Redundancy
                "MULTIWORD": "#e8eaf6", # Light indigo - Multi-word
                "SPELL": "#fcf4ff"      # Light magenta - Spelling
            }
            
            for span in error_spans:
                error_type = span["type"]
                span_text = span["token"]
                
                color = color_map.get(error_type, "#f3e5f5")
                
                # Find and mark the span
                if span_text in marked_original:
                    marked_original = marked_original.replace(
                        span_text,
                        f"<span style='background-color: {color}; border: 1px solid #ddd; padding: 2px 4px; border-radius: 3px; margin: 0 1px;' title='{error_type}: {span_text}'>{span_text}</span>",
                        1
                    )
            
            html_output += f"<div style='margin: 15px 0;'>"
            html_output += f"<p style='margin: 5px 0; font-weight: bold; color: #555;'>Original (with errors highlighted):</p>"
            html_output += f"<p style='margin: 10px 0; padding: 15px; background-color: white; border: 1px solid #ddd; border-radius: 5px; font-size: 16px;'>{marked_original}</p>"
            html_output += f"</div>"
        else:
            html_output += f"<div style='margin: 15px 0;'>"
            html_output += f"<p style='margin: 5px 0; font-weight: bold; color: #555;'>Original:</p>"
            html_output += f"<p style='margin: 10px 0; padding: 15px; background-color: white; border: 1px solid #ddd; border-radius: 5px; font-size: 16px;'>{original}</p>"
            html_output += f"</div>"
        
        # Corrected sentence
        corrected = result["corrected"]
        if corrected != original:
            html_output += f"<div style='margin: 15px 0;'>"
            html_output += f"<p style='margin: 5px 0; font-weight: bold; color: #28a745;'>Corrected version:</p>"
            html_output += f"<p style='margin: 10px 0; padding: 15px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; font-size: 16px;'>{corrected}</p>"
            html_output += f"</div>"
        else:
            html_output += f"<div style='margin: 15px 0;'>"
            html_output += f"<p style='margin: 5px 0; font-weight: bold; color: #28a745;'>✅ No errors detected - sentence is correct!</p>"
            html_output += f"</div>"
        
        html_output += "</div>"
    
    html_output += "</div>"
    return html_output


# Global model instance
_model = None

def get_model():
    """Get the model instance, creating it if it doesn't exist."""
    global _model
    if _model is None:
        model_path = current_app.config.get('NEURAL_NETWORK_MODEL_PATH', 'Zlovoblachko/REAlEC_2step_model_testing')
        ged_model_path = current_app.config.get('GED_MODEL_PATH', 'Zlovoblachko/11tag-electra-grammar-stage2')
        _model = HuggingFaceT5GEDInference(model_path, ged_model_path)
    return _model

def analyze_submission(text):
    """Analyze a student submission using the enhanced neural network model."""
    model = get_model()
    results = process_text(text, model)
    
    # Check if the model returned an error
    if isinstance(results, dict) and 'error' in results:
        return {'error': results['error']}
    
    # Generate analysis result
    analysis_result = {
        "results": results,
        "html_output": generate_html_output(results),
        "total_errors": sum(len(result["error_spans"]) for result in results),
        "sentences": []
    }
    
    # Prepare results in format compatible with submission model
    for i, result in enumerate(results):
        sentence_analysis = {
            "id": i,
            "content": result["original"],
            "errors": []
        }
        
        # Convert error spans to expected format - USE CORRECT TAGS
        for span in result["error_spans"]:
            sentence_analysis["errors"].append({
                "type": span["type"],  # This is now the correct GED tag (ORTH, FORM, etc.)
                "start": span.get("position", -1),
                "end": span.get("position", -1) + 1,
                "original": span["token"],
                "suggestion": ""
            })
        
        analysis_result["sentences"].append(sentence_analysis)
    
    return analysis_result


def analyze_sentence(sentence):
    """Analyze a single sentence using the enhanced neural network model."""
    model = get_model()
    analysis = model.analyze_text(sentence)
    
    # Check if the model returned an error
    if 'error' in analysis:
        return {'error': analysis['error']}
    
    # Return formatted result with correct tags
    result = {
        "content": sentence,
        "errors": [],
        "error_types": analysis.get("error_types", [])  # Include actual error types
    }
    
    # Convert error spans to expected format - USE CORRECT TAGS
    for span in analysis["error_spans"]:
        result["errors"].append({
            "type": span["type"],  # This is now the correct GED tag
            "start": span.get("position", -1),
            "end": span.get("position", -1) + 1,
            "original": span["token"],
            "suggestion": ""
        })
    
    return result