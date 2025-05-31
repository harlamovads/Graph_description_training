# Test preview version link available [here](https://huggingface.co/spaces/Zlovoblachko/lang_learn_app)

# Language Learning Application - AI-Powered Grammar Correction & Exercise Generation

## Overview

This is a comprehensive language learning application designed for teachers and students, featuring AI-powered grammar error detection and correction using state-of-the-art neural networks. The application provides an interactive platform where teachers can create writing assignments, students can submit their work for automated analysis, and personalized grammar exercises are generated based on detected errors.

### Key Features

**For Teachers:**
- Create and assign writing tasks with visual prompts (charts, graphs, images)
- Generate invitation codes for student enrollment
- Review student submissions with AI-generated error analysis
- Create targeted grammar exercises from student errors
- Monitor student progress and performance analytics

**For Students:**
- Complete writing assignments with rich text editing
- Receive immediate AI-powered grammar feedback
- Practice with personalized exercises based on their errors
- Track improvement over time with detailed analytics

**AI-Powered Analysis:**
- Advanced T5-based grammar error correction model
- ELECTRA-based error detection with 11-category classification
- Real-time text analysis with visual error highlighting
- Intelligent exercise generation from error patterns

## Architecture

The application follows a modern full-stack architecture:

- **Backend:** Flask-based REST API with PostgreSQL database
- **Frontend:** React.js with Material-UI components (pre-built and included)
- **AI Models:** HuggingFace Transformers integration with custom T5-GED architecture
- **Deployment:** Docker containerization with multi-service orchestration
- **Database:** PostgreSQL with comprehensive relational schema
- **File Management:** Git LFS for large model files and assets

## Prerequisites

- Docker and Docker Compose
- Git with Git LFS support
- At least 6GB RAM (for AI model loading)
- 10GB+ available disk space

## Installation & Setup

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/harlamovads-graph_description_training.git
cd harlamovads-graph_description_training

# Initialize Git LFS (if not already done)
git lfs install
git lfs pull
```

### Step 2: Environment Configuration

Create the required environment file by copying the template:

```bash
# Copy the environment template
cp .env.template .env
```

Edit the `.env` file with your specific configuration:

```bash
# Database Configuration
DB_USER=app_user
DB_PASSWORD=your_secure_password_here
DB_HOST=postgres
DB_PORT=5432
DB_NAME=language_learning_app
DATABASE_URL=postgresql://app_user:your_secure_password_here@postgres:5432/language_learning_app

# Flask Configuration
SECRET_KEY=your-production-secret-key-here
JWT_SECRET_KEY=your-production-jwt-secret-here
FLASK_ENV=production
FLASK_APP=app.py

# File Upload Configuration
UPLOAD_FOLDER=/app/uploads

# AI Model Configuration
NEURAL_NETWORK_MODEL_PATH=Zlovoblachko/REAlEC_2step_model_testing
GED_MODEL_PATH=Zlovoblachko/11tag-electra-grammar-stage2

# Optional: AWS S3 Configuration (for production file storage)
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_BUCKET_NAME=your_bucket_name
```

**Important:** Generate secure keys for production:

```bash
# Generate secure keys
python gen_script.py
```

### Step 3: Prepare Required Files

The application requires a sentence database file for exercise generation. Ensure `sentencewise_full.jsonl` is present in the root directory (it should be automatically downloaded via Git LFS).

If the file is missing, you can:
1. Check Git LFS status: `git lfs ls-files`
2. Pull LFS files: `git lfs pull`
3. Or obtain the file from your data source and place it in the root directory

## Running the Application

### Option 1: Full Docker Deployment (Recommended)

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

The application will be available at:
- **Main Application:** http://localhost:5001
- **Database:** localhost:5432 (PostgreSQL)

### Option 2: Development Mode

For development with hot-reload capabilities:

```bash
# Start only the database
docker-compose up postgres -d

# Install Python dependencies
pip install -r backend/requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development
export DATABASE_URL=postgresql://app_user:your_password@localhost:5432/language_learning_app

# Initialize the database
python init_db.py

# Run the Flask application
python app.py
```

## Initial Setup and Usage

### First Time Setup

1. **Access the Application:** Navigate to http://localhost:5001
2. **Create Teacher Account:** Register as a teacher
3. **Generate Invitation Code:** Use the teacher dashboard to create student invitation codes
4. **Student Registration:** Students can register independently or use invitation codes

### Sample Accounts (Development)

If you run the database initialization script, sample accounts are created:

```
Teacher Account:
- Email: teacher@example.com
- Password: password123

Student Accounts:
- Email: student1@example.com / Password: password123
- Email: student2@example.com / Password: password123
```

### Typical Workflow

1. **Teacher creates writing tasks** with visual prompts (charts, graphs, images)
2. **Teacher assigns tasks to students** with optional due dates
3. **Students complete assignments** using the rich text editor
4. **AI analyzes submissions** for grammar errors and provides detailed feedback
5. **Teacher reviews submissions** with AI-generated analysis
6. **Exercises are generated** from error patterns for targeted practice
7. **Students practice** with personalized exercises and receive immediate feedback

## System Requirements

### Minimum Requirements
- **RAM:** 4GB (6GB+ recommended for smooth operation)
- **Storage:** 8GB available space
- **CPU:** 2+ cores (4+ cores recommended)
- **Network:** Stable internet connection for initial model download

### Production Requirements
- **RAM:** 8GB+ (for handling multiple concurrent users)
- **Storage:** 20GB+ (for user data and model caching)
- **CPU:** 4+ cores
- **Database:** Separate PostgreSQL instance recommended

## Troubleshooting

### Common Issues

**1. Out of Memory Errors:**
```bash
# Increase Docker memory allocation or system swap
# In docker-compose.yml, memory limits are set to 6GB
```

**2. Model Download Issues:**
```bash
# Clear model cache and re-download
docker-compose down
docker system prune -f
docker-compose up --build
```

**3. Database Connection Issues:**
```bash
# Check database container status
docker-compose ps
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres -d
```

**4. Large File Issues (Git LFS):**
```bash
# Ensure Git LFS is properly set up
git lfs install
git lfs pull

# Check LFS file status
git lfs ls-files
```

### Health Checks

The application includes health check endpoints:

```bash
# Check application health
curl http://localhost:5001/health

# Check database connectivity
docker-compose exec postgres pg_isready
```

## File Structure Explanation

- **`app.py`** - Main Flask application entry point
- **`backend/`** - Core application backend
  - **`models/`** - Database models (User, Task, Submission, Exercise, Sentence)
  - **`routes/`** - API endpoints for different functionalities
  - **`services/`** - Business logic and AI model integration
  - **`static/`** - Pre-built React frontend files
- **`docker/`** - Docker configuration and deployment scripts
- **`frontend/`** - React.js source code (for development)
- **`sentencewise_full.jsonl`** - Sentence database for exercise generation (Git LFS)
- **`.env.template`** - Environment configuration template
- **`init_db.py`** - Database initialization script
- **`docker-compose.yml`** - Multi-service orchestration

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Commit with descriptive messages
6. Push to your fork and create a pull request

## License

This project is licensed under the CC-BY-4.0 - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Docker logs: `docker-compose logs`
3. Create an issue in the GitHub repository with detailed error messages and steps to reproduce
