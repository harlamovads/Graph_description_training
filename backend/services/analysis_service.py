# services/analysis_service.py
from flask import current_app
import json
import re

# This is a placeholder for the actual neural network integration
# In a real application, you would load the GEC/D model here
def load_model():
    """
    Load the GEC/D neural network model
    """
    # Placeholder - in a real app, you would load your model
    # For example:
    # import tensorflow as tf
    # model_path = current_app.config.get('MODEL_PATH')
    # model = tf.keras.models.load_model(model_path)
    # return model
    
    return "Placeholder Model"

# Placeholder for model inference
def analyze_submission(text):
    """
    Analyze a writing submission using the GEC/D model
    
    :param text: Text content to analyze
    :return: Analysis results with errors and suggestions
    """
    # This is a placeholder implementation for the actual neural network integration
    
    model = load_model()
    
    # Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result = {
        "sentences": [],
        "total_errors": 0
    }
    
    for i, sentence in enumerate(sentences):
        # Analyze each sentence
        sentence_analysis = analyze_sentence(sentence)
        
        # Add sentence analysis to result
        result["sentences"].append({
            "id": i,
            "content": sentence,
            "errors": sentence_analysis.get("errors", [])
        })
        
        # Count total errors
        result["total_errors"] += len(sentence_analysis.get("errors", []))
    
    return result

# services/analysis_service.py (partial update for analyze_sentence function)
def analyze_sentence(sentence):
    """
    Analyze a single sentence using the GEC/D model
    
    :param sentence: Sentence to analyze
    :return: Analysis result with errors and suggestions
    """
    # This is a placeholder for the actual neural network integration
    # In a real application, you would use your GEC/D model
    
    model = load_model()
    
    # Look for matching sentences in our database to find known errors
    from models.sentence import Sentence
    
    result = {
        "content": sentence,
        "errors": []
    }
    
    # Check our database for similar sentences
    db_sentences = Sentence.query.all()
    
    for db_sentence in db_sentences:
        # Very simple similarity check (in a real app, use better NLP)
        if len(sentence) > 10 and sentence.lower() in db_sentence.text.lower():
            # If we find a similar sentence, use its error tags
            error_tags = db_sentence.get_error_tags()
            for tag in error_tags:
                result["errors"].append({
                    "type": tag.get("native_tag") or tag.get("first_level_tag", "unknown"),
                    "start": int(tag.get("span_start", 0)),
                    "end": int(tag.get("span_end", 0)),
                    "original": tag.get("error_span", ""),
                    "suggestion": tag.get("correction", "")
                })
            return result
    
    # If no match found, fall back to simple error detection
    if "  " in sentence:  # Double space error
        result["errors"].append({
            "type": "spacing",
            "start": sentence.index("  "),
            "end": sentence.index("  ") + 2,
            "original": "  ",
            "suggestion": " "
        })
    
    # Common grammar errors
    if " i " in sentence.lower():
        position = sentence.lower().index(" i ")
        result["errors"].append({
            "type": "capitalization",
            "start": position + 1,
            "end": position + 2,
            "original": "i",
            "suggestion": "I"
        })
    
    # Missing period at the end
    if len(sentence) > 0 and not sentence.endswith(('.', '!', '?')):
        result["errors"].append({
            "type": "punctuation",
            "start": len(sentence),
            "end": len(sentence),
            "original": "",
            "suggestion": "."
        })
    
    # Common article errors (checking for a subset of the patterns in your sample data)
    article_patterns = [
        "amount of", "overall trend", "period", "total number", "rail category", "first 6 years"
    ]
    
    for pattern in article_patterns:
        if pattern in sentence.lower():
            position = sentence.lower().index(pattern)
            if position == 0 or sentence[position-1] != 'e':  # Check if "the" is not already there
                result["errors"].append({
                    "type": "Articles",
                    "start": position,
                    "end": position + len(pattern),
                    "original": pattern,
                    "suggestion": "the " + pattern
                })
    
    # Spelling errors (checking for specific misspellings from your sample data)
    spelling_errors = {
        "regulary": "regularly",
        "quater": "quarter",
        "thoughout": "throughout",
        "dramaticly": "dramatically",
        "bilion": "billion"
    }
    
    for error, correction in spelling_errors.items():
        if error in sentence.lower():
            position = sentence.lower().index(error)
            result["errors"].append({
                "type": "Spelling",
                "start": position,
                "end": position + len(error),
                "original": error,
                "suggestion": correction
            })
    
    return result