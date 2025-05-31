#!/bin/bash

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U app_user; do
  sleep 1
done

echo "PostgreSQL is ready!"

# Test model loading first
echo "Testing model loading..."
python test_models.py

# Initialize database
python init_db.py

# Start the Flask application
echo "Starting Flask application..."
python app.py