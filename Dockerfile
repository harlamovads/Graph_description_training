# Multi-stage Dockerfile for Hugging Face Spaces
FROM node:18-alpine as frontend-build

# Build React frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# Main application stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-server-dev-all \
    postgresql-client \
    build-essential \
    curl \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir gunicorn psycopg2-binary

# Copy application code
COPY . .

# Copy built frontend
COPY --from=frontend-build /app/frontend/build ./backend/static

# Create necessary directories
RUN mkdir -p uploads logs

# Copy configuration files
COPY docker/nginx-hf.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create database directory for SQLite (fallback)
RUN mkdir -p /app/data

# Create startup script
COPY docker/start-hf.sh /start.sh
RUN chmod +x /start.sh

# Expose port 7860 (required by HF Spaces)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Start the application
CMD ["/start.sh"]