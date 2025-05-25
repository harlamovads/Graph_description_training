#!/bin/bash
# build_frontend.sh

# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build the frontend
npm run build

# Create static folder in Flask app if it doesn't exist
mkdir -p ../backend/static

# Copy build files to Flask static folder
cp -r build/* ../backend/static/

echo "Frontend built and copied to Flask static folder!"