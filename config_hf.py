# config_hf.py - Configuration for Hugging Face Spaces deployment
import os
from datetime import timedelta

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hf-spaces-secret-key'
    DEBUG = False  # Always False for HF Spaces
    
    # SQLite database configuration for HF Spaces
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:////app/data/language_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'hf-spaces-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)  # Longer for demo
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # File upload configuration
    UPLOAD_FOLDER = '/app/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Neural network model configuration
    NEURAL_NETWORK_MODEL_PATH = os.environ.get('NEURAL_NETWORK_MODEL_PATH') or 'Zlovoblachko/Realec-2step-ft-realec'
    GED_MODEL_PATH = os.environ.get('GED_MODEL_PATH') or 'Zlovoblachko/4tag-electra-grammar-error-detection'
    
    # HF Spaces specific settings
    HUGGINGFACE_SPACES = True
    
    # Disable external integrations for HF Spaces
    AWS_ACCESS_KEY = None
    AWS_SECRET_KEY = None
    AWS_BUCKET_NAME = None