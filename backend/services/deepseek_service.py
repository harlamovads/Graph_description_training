# backend/services/deepseek_service.py
"""Generates short example sentences for a practice-session "create a sentence" round, via
DeepSeek's (OpenAI-compatible) chat completions API.

Two kinds of round need examples, and they need different ones:
  * the student must USE a corrected span ("shows") -> generate_similar_sentences
  * the student must avoid re-adding a span that was deleted, keeping the structure around where
    it used to be -> generate_structure_examples

Every call here degrades to an empty list rather than raising, so the practice flow works (just
without example sentences) whether the key is missing, invalid, or DeepSeek is unreachable.
"""
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

DEEPSEEK_MODEL = 'deepseek-chat'
REQUEST_TIMEOUT_SECONDS = 15


def _ask(system_prompt, user_prompt, count):
    """Shared call. Returns up to `count` sentence strings, or [] on any problem at all."""
    api_key = current_app.config.get('DEEPSEEK_API_KEY')
    if not api_key:
        return []

    base_url = current_app.config.get('DEEPSEEK_API_BASE', 'https://api.deepseek.com')

    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': DEEPSEEK_MODEL,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 200
            },
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        response.raise_for_status()
        content = response.json()['choices'][0]['message']['content']
        lines = [line.strip(' -•\t*') for line in content.strip().split('\n')]
        return [line for line in lines if line][:count]
    except Exception:
        logger.exception('DeepSeek example-sentence generation failed')
        return []


def generate_similar_sentences(context_sentence, target_span, count=3):
    """Examples that each CONTAIN `target_span`, styled after `context_sentence`."""
    system_prompt = (
        'You write short example sentences for a language-learning exercise. '
        f'Given a correctly-written context sentence and a target word or phrase, write exactly '
        f'{count} new sentences. Each must be grammatically correct English, contain the target '
        'word/phrase verbatim, and be a similar length and register to the context sentence. '
        'Reply with exactly one sentence per line - no numbering, no bullets, no quotation '
        'marks, no extra commentary.'
    )
    user_prompt = (
        f'Context sentence: "{context_sentence}"\n'
        f'Target word/phrase: "{target_span}"'
    )
    return _ask(system_prompt, user_prompt, count)


def generate_structure_examples(context_sentence, before, after, removed_text, count=3):
    """Examples for a DELETION round.

    Here the student's job is the opposite of the case above: something had to be removed, so a
    good example keeps the grammatical structure around the gap and simply does not contain the
    removed words. Passing the target span would be meaningless (there isn't one), which is why
    these rounds used to show no examples at all.
    """
    joined = ' '.join(part for part in (before, after) if part)
    system_prompt = (
        'You write short example sentences for a language-learning exercise. The student has '
        'just learned that some words had to be DELETED from a sentence to make it correct. '
        f'Write exactly {count} new, grammatically correct English sentences that use the same '
        'grammatical structure as the context sentence around the words shown, and that do NOT '
        'contain the removed words. Keep them a similar length and register to the context '
        'sentence. Reply with exactly one sentence per line - no numbering, no bullets, no '
        'quotation marks, no extra commentary.'
    )
    user_prompt = (
        f'Context sentence: "{context_sentence}"\n'
        f'Structure to keep (the words around the gap): "{joined}"\n'
        f'Words that must NOT appear: "{removed_text}"'
    )
    return _ask(system_prompt, user_prompt, count)
