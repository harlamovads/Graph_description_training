# backend/services/neural_network_service.py
import torch
import nltk
import re
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
        """Enhanced analysis method for Flask integration.

        Note: `error_spans`/`error_types` here are the internal ELECTRA GED tagger's own
        token-level predictions on the *original* text - kept around for reference/debugging
        only. They are NOT used to drive the user-facing highlight - that comes from
        errant_service.compute_edits(text, corrected_text), diffing against what this method
        actually corrected. See routes/submissions.py and backend/services/practice_service.py.
        """
        if not text.strip():
            return {"error": "Please enter some text."}

        try:
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            if not clean_text:
                return {"error": "Please enter some text."}
            corrected_text = self.correct_text(clean_text)
            error_spans, error_types = self._get_error_spans_detailed(clean_text)
            return {
                "corrected_text": corrected_text,
                "ged_error_spans": error_spans,
                "ged_error_types": error_types
            }

        except Exception as e:
            return {"error": f"Error during analysis: {str(e)}"}


def analyze_and_diff(sentence, model=None):
    """Analyze a single sentence and diff it against its own correction.

    This is the one place a sentence gets run through the model and typed via ERRANT - shared
    by process_text()'s per-sentence loop (task submissions) and
    backend/services/practice_service.py's practice-item rounds (see start_session's note on
    reusing this instead of a second inline copy), so both go through the exact same analysis
    path.

    Returns {"original", "corrected", "errant_edits", "ged_error_spans", "ged_error_types"}.
    On a model error, degrades to a no-op result (corrected == original, no edits) rather than
    raising, matching process_text's existing per-sentence fallback behavior.
    """
    from backend.services import errant_service

    if model is None:
        model = get_model()

    analysis = model.analyze_text(sentence)

    if "error" in analysis:
        return {
            "original": sentence,
            "corrected": sentence,
            "errant_edits": [],
            "ged_error_spans": [],
            "ged_error_types": []
        }

    corrected = analysis["corrected_text"]
    return {
        "original": sentence,
        "corrected": corrected,
        "errant_edits": errant_service.compute_edits(sentence, corrected),
        "ged_error_spans": analysis.get("ged_error_spans", []),
        "ged_error_types": analysis.get("ged_error_types", [])
    }


def process_text(text, model):
    """Process input text by splitting into sentences and applying the model.

    Each sentence result carries the NN's `corrected` text plus `errant_edits` - the typed
    diff between `original` and `corrected` (see backend/services/errant_service.py) - which
    is what drives the displayed highlight. `ged_error_types`/`ged_error_spans` are kept
    around for reference/debugging only, not used elsewhere.
    """
    if not text.strip():
        return {"error": "Please enter some text."}

    # Strip rich-text markup (RichTextEditor stores submissions as HTML) before sentence
    # tokenization, not just inside model.analyze_text(). Tokenizing on the raw HTML let tags
    # merge into the first "sentence" (e.g. "<p>I have"), which then leaked into the ERRANT
    # diff as if it were part of the student's original text. Replace tags with a space
    # (not '') so adjacent block elements like </p><p> don't fuse two words together.
    clean_text = re.sub(r'<[^>]+>', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    if not clean_text:
        return {"error": "Please enter some text."}

    try:
        sentences = nltk.sent_tokenize(clean_text)
    except LookupError:
        nltk.download('punkt')
        sentences = nltk.sent_tokenize(clean_text)

    # analyze_and_diff is the same per-sentence analyze-then-diff step practice_service reuses
    # for practice-item rounds, so a submission's sentences and a practice round go through the
    # exact same analysis path.
    return [analyze_and_diff(sentence, model) for sentence in sentences]


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
    """Analyze a student submission using the enhanced neural network model.

    Returns a JSON-serializable dict (this is what's stored in Submission.analysis_result):
    {
      "sentences": [
        {
          "id": i, "original": ..., "corrected": ...,   # the NN's correction
          "teacher_corrected": None,                    # settable later, see submissions.py
          "errant_edits": [...],                        # diff(original, corrected) - drives the highlight
          "ged_error_types": [...]                       # reference/debugging only
        }, ...
      ],
      "total_errors": N,          # sum of errant_edits across sentences
      "ged_error_types": [...]    # union across sentences, reference/debugging only
    }
    """
    model = get_model()
    results = process_text(text, model)

    # Check if the model returned an error
    if isinstance(results, dict) and 'error' in results:
        return {'error': results['error']}

    sentences = []
    all_ged_types = set()
    total_errors = 0

    for i, result in enumerate(results):
        errant_edits = result.get("errant_edits", [])
        ged_types = result.get("ged_error_types", [])
        all_ged_types.update(ged_types)
        total_errors += len(errant_edits)

        sentences.append({
            "id": i,
            "original": result["original"],
            "corrected": result["corrected"],
            "teacher_corrected": None,
            "errant_edits": errant_edits,
            "ged_error_types": ged_types
        })

    return {
        "sentences": sentences,
        "total_errors": total_errors,
        "ged_error_types": list(all_ged_types)
    }
