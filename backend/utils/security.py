# utils/security.py
import hashlib
import secrets
import re
import bleach
from flask import request, current_app, abort
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.models.user import User

# Allowlist for rich-text submission/feedback content. Matches the formatting options the
# RichTextEditor toolbar actually exposes (bold/italic/underline/lists/links/headers) —
# everything else (script tags, event-handler attributes, iframes, ...) is stripped.
ALLOWED_TAGS = [
    'p', 'br', 'b', 'i', 'u', 'strong', 'em', 'ul', 'ol', 'li', 'a',
    'h1', 'h2', 'h3', 'h4', 'blockquote', 'span'
]
# No `style` attribute here: sanitizing inline CSS safely needs bleach's separate
# css_sanitizer add-on, and the RichTextEditor toolbar (bold/italic/underline/lists/
# link/history) never emits one anyway - so it's not worth allowlisting.
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'target', 'rel']
}

def generate_secure_token(length=32):
    """
    Generate a secure random token
    
    :param length: Length of the token in bytes
    :return: Random token string
    """
    return secrets.token_hex(length)

def hash_password(password, salt=None):
    """
    Hash a password using SHA-256
    
    :param password: Password to hash
    :param salt: Salt to use (generated if None)
    :return: (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    hash_obj = hashlib.sha256((password + salt).encode())
    return hash_obj.hexdigest(), salt

def check_content_type(mimetype):
    """
    Decorator to check content type
    
    :param mimetype: Expected mimetype
    :return: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.mimetype != mimetype:
                return {'error': f'Expected Content-Type: {mimetype}'}, 415
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def teacher_required(f):
    """
    Decorator to restrict access to teachers only
    
    :param f: Function to wrap
    :return: Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != 'teacher':
            return {'error': 'This endpoint is restricted to teachers'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """
    Decorator to restrict access to students only
    
    :param f: Function to wrap
    :return: Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        if not user or user.role != 'student':
            return {'error': 'This endpoint is restricted to students'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def sanitize_input(text):
    """
    Sanitize rich-text HTML (student submissions, teacher corrections/feedback) to an
    allowlist of safe formatting tags, stripping everything else - <script>, event-handler
    attributes, iframes, etc. Used instead of storing student-controlled HTML verbatim,
    since it is later rendered client-side.

    :param text: HTML text to sanitize
    :return: Sanitized HTML text
    """
    if not text:
        return text
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)