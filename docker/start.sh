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

# Start the application under gunicorn. The Flask development server was never meant to face
# users: no request timeouts, single-threaded accept loop, and it prints tracebacks on error.
# See gunicorn.conf.py for why it's one worker with threads and a long timeout.
echo "Starting application (gunicorn)..."
exec gunicorn --config gunicorn.conf.py app:app