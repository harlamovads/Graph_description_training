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

# Apply pending schema migrations (this owns the schema now - init_db.py below only seeds
# sample data, and only if the database is empty, so restarts never wipe real data)
echo "Applying database migrations..."
flask db upgrade

# Seed sample data (idempotent - no-op if the database already has data)
python init_db.py

# Start the Flask application
echo "Starting Flask application..."
python app.py