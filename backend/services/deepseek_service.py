# backend/services/deepseek_service.py
"""Generates short example sentences for a practice-session "create a sentence" round, via
DeepSeek's (OpenAI-compatible) chat completions API.

No key configured yet in this environment - `DEEPSEEK_API_KEY` is a placeholder in .env/
.env.template/docker-compose.yml until a real one is added. Every call here degrades to an
empty list rather than raising, so the practice flow works (just without example sentences)
whether the key is missing, invalid, or DeepSeek is unreachable.
"""
import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)

DEEPSEEK_MODEL = 'deepseek-chat'
REQUEST_TIMEOUT_SECONDS = 15


def generate_similar_sentences(context_sentence, target_span, count=3):
    """Ask DeepSeek for `count` new sentences, each containing `target_span`, styled after
    `context_sentence` (the practice session's already-corrected sentence). Returns a list of
    up to `count` plain sentence strings - [] if no API key is configured or the call fails.
    """
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
                    {
                        'role': 'system',
                        'content': (
                            'You write short example sentences for a language-learning exercise. '
                            f'Given a correctly-written context sentence and a target word or '
                            f'phrase, write exactly {count} new sentences. Each must be '
                            'grammatically correct English, contain the target word/phrase '
                            'verbatim, and be a similar length and register to the context '
                            'sentence. Reply with exactly one sentence per line - no numbering, '
                            'no bullets, no quotation marks, no extra commentary.'
                        )
                    },
                    {
                        'role': 'user',
                        'content': (
                            f'Context sentence: "{context_sentence}"\n'
                            f'Target word/phrase: "{target_span}"'
                        )
                    }
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
