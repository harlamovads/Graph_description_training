# backend/services/neural_network_service.py
import torch
import nltk
import re
import difflib
from transformers import (
    AutoModelForSeq2SeqLM, 
    AutoTokenizer, 
    ElectraTokenizer, 
    ElectraForTokenClassification
)
import torch.nn as nn
from flask import current_app
import os
import json
from huggingface_hub import hf_hub_download

# Download NLTK data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class T5WithGED(nn.Module):
    def __init__(self, model_path, ged_model_path="Zlovoblachko/4tag-electra-grammar-error-detection"):
        super().__init__()
        # Load T5 model and tokenizer
        self.t5 = AutoModelForSeq2SeqLM.from_pretrained(model_path)
        self.t5_tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Download and load GED components from Hugging Face
        try:
            # Download the ged_components.pt file from your repository
            ged_components_path = hf_hub_download(
                repo_id=model_path,
                filename="ged_components.pt",
                cache_dir=None
            )
            
            self.ged_encoder = self.t5.encoder  # Initialize with a copy of the regular encoder
            self.gate = nn.Linear(2 * self.t5.config.d_model, 1)

            # Load saved GED components
            ged_components = torch.load(ged_components_path, map_location=torch.device('cpu'))
            self.ged_encoder.load_state_dict(ged_components["ged_encoder"])
            self.gate.load_state_dict(ged_components["gate"])

            self.has_ged = True
            print("Loaded GED components successfully from Hugging Face")
        except Exception as e:
            print(f"Could not load GED components: {e}")
            print("Falling back to standard T5 model without GED integration")
            self.has_ged = False

        # Load GED model from Hugging Face
        self.ged_model = None
        self.ged_tokenizer = None
        try:
            print(f"Loading GED model from Hugging Face: {ged_model_path}")
            self.ged_tokenizer = ElectraTokenizer.from_pretrained(ged_model_path)
            self.ged_model = ElectraForTokenClassification.from_pretrained(ged_model_path)
            print("Loaded GED model successfully")
        except Exception as e:
            print(f"Could not load GED model from {ged_model_path}: {e}")
            print("Will use model without GED predictions")

    def get_ged_predictions(self, text):
        """Get GED predictions for a sentence."""
        if self.ged_model is None or self.ged_tokenizer is None:
            return None

        inputs = self.ged_tokenizer(text, return_tensors="pt", truncation=True, padding=True)

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

            if pred == 0:
                ged_tags.append("C")
            elif pred == 1:
                ged_tags.append("R")
            elif pred == 2:
                ged_tags.append("M")
            elif pred == 3:
                ged_tags.append("U")

        return " ".join(ged_tags)

    def extract_error_spans(self, text, ged_tags):
        """Extract error spans from text based on GED tags."""
        if not ged_tags:
            return []

        # Tokenize the input text
        tokens = self.ged_tokenizer.tokenize(text)
        clean_tokens = []
        
        # Remove special tokens and subtokens
        for token in tokens:
            if token.startswith("##") or token in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            clean_tokens.append(token)
        
        # Split GED tags string into individual tags
        tag_list = ged_tags.split()
        
        # Ensure we have the same number of tokens and tags
        min_len = min(len(clean_tokens), len(tag_list))
        clean_tokens = clean_tokens[:min_len]
        tag_list = tag_list[:min_len]
        
        # Find error spans
        error_spans = []
        i = 0
        while i < len(tag_list):
            if tag_list[i] != "C":  # If this is an error
                error_type = tag_list[i]
                start_idx = i
                
                # Find the end of this error span
                j = i
                while j < len(tag_list) and tag_list[j] == error_type:
                    j += 1
                end_idx = j
                
                # Extract the text of the error span
                span_tokens = clean_tokens[start_idx:end_idx]
                span_text = " ".join(span_tokens).replace(" ##", "")
                
                # Find the position in the original text
                # This is a simple approximation
                text_lower = text.lower()
                span_text_lower = span_text.lower()
                
                # Try to find the actual position in the text
                token_indices = list(range(start_idx, end_idx))
                
                error_spans.append({
                    "text": span_text,
                    "type": error_type,
                    "token_indices": token_indices
                })
                
                i = end_idx
            else:
                i += 1
                
        return error_spans

    def correct(self, text, use_ged=True, max_length=128):
        """Correct grammatical errors in text and return the corrected text, GED tags, and error spans."""
        # Process text with the model
        inputs = self.t5_tokenizer(text, return_tensors="pt", truncation=True, max_length=max_length)

        if self.has_ged and use_ged and self.ged_model is not None:
            # Get GED predictions
            ged_tags = self.get_ged_predictions(text)
            if ged_tags is None:
                # Fallback to standard model if GED predictions failed
                output_ids = self.t5.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=max_length
                )
                corrected_text = self.t5_tokenizer.decode(output_ids[0], skip_special_tokens=True)
                return corrected_text, "", []

            # Extract error spans
            error_spans = self.extract_error_spans(text, ged_tags)

            ged_inputs = self.t5_tokenizer(ged_tags, return_tensors="pt", truncation=True, max_length=max_length)

            # Encode source and GED inputs
            src_encoder_outputs = self.t5.encoder(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                return_dict=True
            )

            ged_encoder_outputs = self.ged_encoder(
                input_ids=ged_inputs.input_ids,
                attention_mask=ged_inputs.attention_mask,
                return_dict=True
            )

            # Apply gating mechanism
            src_hidden_states = src_encoder_outputs.last_hidden_state
            ged_hidden_states = ged_encoder_outputs.last_hidden_state

            # Ensure sequences have the same length for concatenation
            min_len = min(src_hidden_states.size(1), ged_hidden_states.size(1))
            combined = torch.cat([
                src_hidden_states[:, :min_len, :],
                ged_hidden_states[:, :min_len, :]
            ], dim=2)

            gate_scores = torch.sigmoid(self.gate(combined))

            # Apply gating: λ*src_hidden + (1-λ)*ged_hidden
            combined_hidden = (
                gate_scores * src_hidden_states[:, :min_len, :] +
                (1 - gate_scores) * ged_hidden_states[:, :min_len, :]
            )

            # Update encoder outputs
            src_encoder_outputs.last_hidden_state = combined_hidden

            # Generate with the enhanced encoder outputs
            output_ids = self.t5.generate(
                encoder_outputs=src_encoder_outputs,
                max_length=max_length
            )
        else:
            # Use standard T5 model
            output_ids = self.t5.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=max_length
            )
            corrected_text = self.t5_tokenizer.decode(output_ids[0], skip_special_tokens=True)
            # No GED predictions in this case
            ged_tags = ""
            error_spans = []
            return corrected_text, ged_tags, error_spans

        corrected_text = self.t5_tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return corrected_text, ged_tags, error_spans


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
        corrected, ged_tags, error_spans = model.correct(sentence)
        
        # Create result dictionary
        result = {
            "original": sentence,
            "corrected": corrected,
            "ged_tags": ged_tags,
            "error_spans": error_spans,
            "changes": find_differences(sentence, corrected)
        }
        results.append(result)
    
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
            # Create highlighted version of original text
            marked_original = original
            replacements = []
            
            for span in error_spans:
                error_type = span["type"]
                span_text = span["text"]
                
                # Set color and label based on error type
                if error_type == "R":
                    color = "#ffebee"  # Light red background
                    border_color = "#f44336"  # Red border
                    label = "Replace"
                    icon = "🔄"
                elif error_type == "M":
                    color = "#e8f5e8"  # Light green background
                    border_color = "#4caf50"  # Green border
                    label = "Missing word"
                    icon = "➕"
                elif error_type == "U":
                    color = "#fff3e0"  # Light orange background
                    border_color = "#ff9800"  # Orange border
                    label = "Unnecessary"
                    icon = "❌"
                else:
                    color = "#f3e5f5"  # Light purple background
                    border_color = "#9c27b0"  # Purple border
                    label = "Error"
                    icon = "⚠️"
                
                # Find the span in the original text and mark it
                try:
                    # Simple text replacement - find the span text in original
                    span_index = marked_original.find(span_text)
                    if span_index != -1:
                        replacements.append((
                            span_index,
                            span_index + len(span_text),
                            f"<span style='background-color: {color}; border: 1px solid {border_color}; padding: 2px 4px; border-radius: 3px; margin: 0 1px;' title='{label}: {span_text}'>{icon} {span_text}</span>"
                        ))
                except:
                    continue
            
            # Apply replacements from end to start to avoid index shifting
            replacements.sort(key=lambda x: x[0], reverse=True)
            for start, end, replacement in replacements:
                marked_original = marked_original[:start] + replacement + marked_original[end:]
            
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
        
        # Summary of changes (if any)
        changes = result["changes"]
        if changes and len(error_spans) > 0:
            html_output += f"<div style='margin-top: 15px; padding: 10px; background-color: #e9ecef; border-radius: 5px;'>"
            html_output += f"<p style='margin: 0 0 10px 0; font-weight: bold; color: #333;'>Summary of changes:</p>"
            html_output += "<ul style='margin: 0; padding-left: 20px;'>"
            
            for change in changes:
                if change["type"] == "deletion":
                    html_output += f"<li style='color: #dc3545; margin: 5px 0;'>Removed: <strong>'{change['text']}'</strong></li>"
                elif change["type"] == "addition":
                    html_output += f"<li style='color: #28a745; margin: 5px 0;'>Added: <strong>'{change['text']}'</strong></li>"
            
            html_output += "</ul>"
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
        model_path = current_app.config.get('NEURAL_NETWORK_MODEL_PATH', 'Zlovoblachko/REAEC_GEC_2step_test')
        ged_model_path = current_app.config.get('GED_MODEL_PATH', 'Zlovoblachko/4tag-electra-grammar-error-detection')
        _model = T5WithGED(model_path, ged_model_path)
    return _model

def analyze_submission(text):
    """Analyze a student submission using the neural network model."""
    model = get_model()
    results = process_text(text, model)
    
    # Check if the model returned an error
    if isinstance(results, dict) and 'error' in results:
        return {'error': results['error']}
    
    # Generate corrected text and analysis
    analysis_result = {
        "results": results,
        "html_output": generate_html_output(results),
        "total_errors": sum(len(result["error_spans"]) for result in results),
        "sentences": []
    }
    
    # Prepare results in a format compatible with our submission model
    for i, result in enumerate(results):
        sentence_analysis = {
            "id": i,
            "content": result["original"],
            "errors": []
        }
        
        # Convert error spans to the format expected by the submission model
        for span in result["error_spans"]:
            sentence_analysis["errors"].append({
                "type": span["type"],
                "start": -1,  # We don't have exact character positions
                "end": -1,    # We'll update these in the frontend
                "original": span["text"],
                "suggestion": ""  # The model doesn't provide specific suggestions for each span
            })
        
        analysis_result["sentences"].append(sentence_analysis)
    
    return analysis_result


def analyze_sentence(sentence):
    """Analyze a single sentence using the neural network model."""
    model = get_model()
    result = process_text(sentence, model)
    
    # Check if the model returned an error
    if isinstance(result, dict) and 'error' in result:
        return {'error': result['error']}
    
    # Return the first result since we only analyzed one sentence
    if result:
        return {
            "content": result[0]["original"],
            "errors": [
                {
                    "type": span["type"],
                    "start": -1,  # We don't have exact character positions
                    "end": -1,    # We'll update these in the frontend
                    "original": span["text"],
                    "suggestion": ""  # The model doesn't provide specific suggestions for each span
                }
                for span in result[0]["error_spans"]
            ]
        }
    
    return {
        "content": sentence,
        "errors": []
    }