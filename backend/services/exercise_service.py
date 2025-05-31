# backend/services/exercise_service.py
from backend.models.sentence import Sentence
from backend.models import db
import random
import json

def find_similar_sentences_by_error_types(error_types, limit=5):
    """
    Find sentences with similar error types from the sentence database
    Uses the correct GED tag system: ORTH, FORM, MORPH, DET, POS, VERB, NUM, WORD, PUNCT, RED, MULTIWORD, SPELL
    
    :param error_types: List of error types to match (GED tags like 'ORTH', 'FORM', etc.)
    :param limit: Maximum number of sentences to return
    :return: List of sentence dictionaries
    """
    if not error_types:
        return []
    
    similar_sentences = []
    
    # Query sentences that contain any of the specified error types
    for error_type in error_types:
        # Search for sentences where the error_tags JSON contains the error type in second_level_tag
        sentences = db.session.query(Sentence).filter(
            Sentence.error_tags.like(f'%"second_level_tag": "{error_type}"%')
        ).order_by(db.func.random()).limit(limit).all()
        
        for sentence in sentences:
            error_tags = sentence.get_error_tags()
            
            # Verify the sentence actually contains the error type
            sentence_error_types = set()
            for tag in error_tags:
                second_level_tag = tag.get('second_level_tag')
                if second_level_tag:
                    sentence_error_types.add(second_level_tag)
            
            # Check if any of our target error types are present
            if any(et in sentence_error_types for et in error_types):
                similar_sentences.append({
                    'id': sentence.id,
                    'text': sentence.text,
                    'error_tags': error_tags,
                    'error_types': list(sentence_error_types)
                })
    
    # Remove duplicates and limit results
    seen_texts = set()
    unique_sentences = []
    for sentence in similar_sentences:
        if sentence['text'] not in seen_texts:
            seen_texts.add(sentence['text'])
            unique_sentences.append(sentence)
            if len(unique_sentences) >= limit:
                break
    
    return unique_sentences

def generate_exercise_sentences(error_types, count=4):
    """
    Generate exercise sentences from the database based on error types
    
    :param error_types: List of error types to match (using second_level_tag)
    :param count: Number of sentences to generate (default: 4)
    :return: List of sentences
    """
    sentences = []
    all_sentences = Sentence.query.all()
    matching_sentences = []
    
    # Find sentences with similar error types using second_level_tag
    for sentence in all_sentences:
        error_tags = sentence.get_error_tags()
        for tag in error_tags:
            tag_type = tag.get("second_level_tag", "")
            if tag_type and any(error_type in tag_type for error_type in error_types):
                matching_sentences.append(sentence)
                break
    
    # If we have matching sentences, select some randomly
    if matching_sentences:
        selected_sentences = random.sample(matching_sentences, min(count, len(matching_sentences)))
        sentences = [s.text for s in selected_sentences]
    
    # If we don't have enough sentences, add some random ones
    if len(sentences) < count and all_sentences:
        remaining_count = count - len(sentences)
        random_sentences = random.sample(all_sentences, min(remaining_count, len(all_sentences)))
        sentences.extend([s.text for s in random_sentences if s.text not in sentences])
    
    # Ensure we only return the requested count
    return sentences[:count]

def get_error_types_from_sentence_analysis(analysis_result):
    """
    Extract error types from neural network analysis result
    Now returns the correct GED tags
    
    :param analysis_result: Result from neural network analysis
    :return: List of GED error types (ORTH, FORM, etc.)
    """
    error_types = []
    
    if isinstance(analysis_result, dict):
        # Handle different analysis result formats
        if 'error_types' in analysis_result:
            # Direct error types from enhanced model
            error_types.extend(analysis_result['error_types'])
        elif 'error_spans' in analysis_result:
            # Enhanced neural network format
            for span in analysis_result['error_spans']:
                if 'type' in span:
                    error_types.append(span['type'])
        elif 'sentences' in analysis_result:
            # Original format
            for sentence in analysis_result['sentences']:
                for error in sentence.get('errors', []):
                    if 'type' in error:
                        error_types.append(error['type'])
        elif 'errors' in analysis_result:
            # Direct error list format
            for error in analysis_result['errors']:
                if 'type' in error:
                    error_types.append(error['type'])
    
    return list(set(error_types))  # Remove duplicates

def create_enhanced_exercise_from_analysis(original_sentence, analysis_result, additional_count=4):
    """
    Create an enhanced exercise using both the original sentence and similar sentences from database
    Now uses correct GED error types
    
    :param original_sentence: The original sentence with errors
    :param analysis_result: Neural network analysis result with GED tags
    :param additional_count: Number of additional sentences to include
    :return: List of exercise sentences with metadata
    """
    exercise_sentences = []
    
    # Add the original sentence
    error_types = get_error_types_from_sentence_analysis(analysis_result)
    
    exercise_sentences.append({
        'id': 0,
        'content': original_sentence,
        'source': 'original',
        'error_types': error_types
    })
    
    # Find similar sentences from database using correct GED tags
    similar_sentences = find_similar_sentences_by_error_types(error_types, additional_count)
    
    # Add similar sentences
    for i, sentence_data in enumerate(similar_sentences, 1):
        exercise_sentences.append({
            'id': i,
            'content': sentence_data['text'],
            'source': 'database',
            'error_types': sentence_data['error_types'],
            'database_id': sentence_data['id']
       })
    return exercise_sentences

def get_sentence_database_stats():
   """Get statistics about the sentence database"""
   total_count = Sentence.query.count()
   
   if total_count == 0:
       return {
           'total_sentences': 0,
           'error_types': [],
           'status': 'empty'
       }
   
   # Sample sentences to get error type distribution
   sample_size = min(1000, total_count)
   sample_sentences = Sentence.query.order_by(db.func.random()).limit(sample_size).all()
   
   error_type_counts = {}
   for sentence in sample_sentences:
       error_tags = sentence.get_error_tags()
       for tag in error_tags:
           # Use second_level_tag which corresponds to GED tags
           error_type = tag.get('second_level_tag')
           if error_type:
               error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1
   
   return {
       'total_sentences': total_count,
       'error_types': list(error_type_counts.keys()),
       'error_type_distribution': error_type_counts,
       'sample_size': sample_size,
       'status': 'loaded'
   }