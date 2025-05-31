FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    build-essential \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets

# Create cache directories
RUN mkdir -p /app/.cache/huggingface/transformers /app/.cache/huggingface/datasets

# Clear any existing cache to avoid conflicts
RUN rm -rf /app/.cache/huggingface/* || true

# Pre-download models with better error handling and caching
COPY docker/download_models.py /tmp/download_models.py
RUN python /tmp/download_models.py

# Copy the entire application
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/backend/uploads \
    && chmod 755 /app/uploads /app/backend/uploads

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt')"

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV UPLOAD_FOLDER=/app/uploads

# Expose the port
EXPOSE 5001

# Create a startup script
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]