# config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Basic Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    # Defaults to False: this used to default True, which is harmless under `python app.py`
    # (app.run(debug=False) overrides it) but would expose the Werkzeug debugger and full
    # tracebacks the moment the app is served by gunicorn/uwsgi instead.
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # PostgreSQL database configuration
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or 'postgres'
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '5432'
    DB_NAME = os.environ.get('DB_NAME') or 'language_learning_app'
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sized against gunicorn's 72 threads (80 connections available, under Postgres' default
    # max_connections of 100), so a burst of page loads never waits on the pool. Requests that
    # are only WAITING for an analysis slot have already released their connection, so the pool
    # covers the threads doing work rather than the whole queue.
    # pre_ping costs one cheap round trip and avoids the
    # "server closed the connection unexpectedly" errors that otherwise appear after the DB is
    # restarted or a connection has been idle overnight.
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '20')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '60')),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        'pool_recycle': 1800,
        'pool_pre_ping': True,
    }
    
    # JWT configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload configuration. Must honour the env var: docker-compose mounts the
    # persistent volume at /app/uploads and sets UPLOAD_FOLDER to match, but this used to
    # hardcode <repo>/backend/uploads, so every uploaded task image was written into the
    # container's writable layer instead of the volume - and silently vanished the next time
    # the container was recreated (any rebuild/deploy).
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    # Reject oversized request bodies outright - task image uploads were unbounded, so one
    # request could have filled the server's disk.
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH_MB', '10')) * 1024 * 1024
    
    # Neural network model configuration
    NEURAL_NETWORK_MODEL_PATH = os.environ.get('NEURAL_NETWORK_MODEL_PATH') or 'Zlovoblachko/REAlEC_2step_model_testing'
    GED_MODEL_PATH = os.environ.get('GED_MODEL_PATH') or 'Zlovoblachko/11tag-electra-grammar-stage2'

    # DeepSeek API (used by backend/services/deepseek_service.py to generate example sentences
    # for practice sessions). Empty by default - that service degrades to no examples rather
    # than erroring when this isn't set.
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY') or ''
    DEEPSEEK_API_BASE = os.environ.get('DEEPSEEK_API_BASE') or 'https://api.deepseek.com'
    
    # AWS S3 configuration for file storage
    AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')
    AWS_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')