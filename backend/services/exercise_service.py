# services/exercise_service.py
from backend.models.sentence import Sentence
import random

def generate_exercise_sentences(error_types, count=4):
    """
    Generate exercise sentences from the database based on error types
    
    :param error_types: List of error types to match
    :param count: Number of sentences to generate (default: 4)
    :return: List of sentences
    """
    sentences = []
    all_sentences = Sentence.query.all()
    matching_sentences = []
    
    # Find sentences with similar error types
    for sentence in all_sentences:
        error_tags = sentence.get_error_tags()
        for tag in error_tags:
            tag_type = tag.get("native_tag") or tag.get("first_level_tag")
            if tag_type and any(error_type.lower() in tag_type.lower() for error_type in error_types):
                matching_sentences.append(sentence)
                break
    
    # If we have matching sentences, select some randomly
    if matching_sentences:
        selected_sentences = random.sample(matching_sentences, min(count, len(matching_sentences)))
        sentences = [s.text for s in selected_sentences]
    
    # If we don't have enough sentences, add some random ones
    if len(sentences) < count:
        random_sentences = random.sample(all_sentences, min(count - len(sentences), len(all_sentences)))
        sentences.extend([s.text for s in random_sentences])
    
    # Ensure we only return the requested count
    return sentences[:count]