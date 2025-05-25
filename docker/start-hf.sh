#!/bin/bash

# Startup script for Hugging Face Spaces deployment

set -e

echo "🚀 Starting Language Learning App on Hugging Face Spaces..."

# Create logs directory
mkdir -p /app/logs

# Set environment variables for HF Spaces
export FLASK_ENV=production
export SECRET_KEY=${SECRET_KEY:-$(python -c "import secrets; print(secrets.token_hex(32))")}
export JWT_SECRET_KEY=${JWT_SECRET_KEY:-$(python -c "import secrets; print(secrets.token_hex(32))")}

# Database configuration - Use SQLite for HF Spaces
export DB_HOST=""
export DB_PORT=""
export DB_NAME="/app/data/language_app.db"
export DB_USER=""
export DB_PASSWORD=""

# Create SQLite database directory
mkdir -p /app/data

echo "🔧 Initializing database..."
cd /app

# Modify app.py to use SQLite for HF Spaces
if [ ! -f "/app/data/language_app.db" ]; then
    echo "Creating SQLite database..."
    python -c "
import sqlite3
import os
from datetime import datetime

# Create SQLite database
conn = sqlite3.connect('/app/data/language_app.db')
c = conn.cursor()

# Create tables (simplified schema for HF Spaces)
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT,
    is_from_database BOOLEAN DEFAULT 0,
    creator_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS task_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    student_id INTEGER,
    due_date TIMESTAMP,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    exercise_id INTEGER,
    student_id INTEGER,
    content TEXT NOT NULL,
    analysis_result TEXT,
    analysis_html TEXT,
    teacher_feedback TEXT,
    status TEXT DEFAULT 'submitted',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    title TEXT NOT NULL,
    instructions TEXT NOT NULL,
    sentences TEXT NOT NULL,
    image_url TEXT,
    status TEXT DEFAULT 'published',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS exercise_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER,
    student_id INTEGER,
    responses TEXT,
    analysis_result TEXT,
    score REAL,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

c.execute('''CREATE TABLE IF NOT EXISTS sentences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    error_tags TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    teacher_id INTEGER,
    is_used BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Create demo users
from werkzeug.security import generate_password_hash

# Demo teacher
c.execute('''INSERT OR IGNORE INTO users (username, email, password_hash, role) 
             VALUES (?, ?, ?, ?)''', 
          ('demo_teacher', 'teacher@demo.com', generate_password_hash('demo123'), 'teacher'))

# Demo students  
c.execute('''INSERT OR IGNORE INTO users (username, email, password_hash, role) 
             VALUES (?, ?, ?, ?)''', 
          ('demo_student1', 'student1@demo.com', generate_password_hash('demo123'), 'student'))

c.execute('''INSERT OR IGNORE INTO users (username, email, password_hash, role) 
             VALUES (?, ?, ?, ?)''', 
          ('demo_student2', 'student2@demo.com', generate_password_hash('demo123'), 'student'))

# Sample task
c.execute('''INSERT OR IGNORE INTO tasks (title, description, image_url, creator_id) 
             VALUES (?, ?, ?, ?)''', 
          ('Chart Description', 'Describe the chart showing digital game sales', '/uploads/sample_chart.png', 1))

conn.commit()
conn.close()
print('✅ SQLite database created successfully')
"
fi

echo "📦 Installing additional dependencies..."
# Download NLTK data
python -c "import nltk; nltk.download('punkt', quiet=True)"

echo "🎯 Starting services with supervisor..."
# Start services using supervisor
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf