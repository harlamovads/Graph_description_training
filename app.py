# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask import send_from_directory
import os
from backend.config import Config
from backend.models import db
from backend.routes.auth import auth_bp
from backend.routes.tasks import tasks_bp
from backend.routes.submissions import submissions_bp
from backend.routes.exercises import exercises_bp
from backend.routes.analysis import analysis_bp
from backend.routes.pages import pages_bp
import nltk

def create_app(config_class=Config):
    """
    Application factory function
    """
    app = Flask(__name__, static_folder='backend/static', static_url_path='')
    app.config.from_object(config_class)
    
    # Print JWT configuration for debugging
    print(f"JWT_SECRET_KEY set: {'JWT_SECRET_KEY' in app.config}")
    print(f"JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Ensure JWT error handlers are defined
    @jwt.user_identity_loader
    def user_identity_lookup(identity):
    # Convert identity to string if it's not already
        return str(identity)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"Expired token: {jwt_payload}")
        return jsonify({
            'status': 401,
            'sub_status': 42,
            'msg': 'The token has expired'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"Invalid token error: {error}")
        return jsonify({
            'status': 422,
            'sub_status': 42,
            'msg': 'Invalid token'
        }), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"Missing token: {error}")
        return jsonify({
            'status': 401,
            'sub_status': 45,
            'msg': 'Missing token'
        }), 401
    
    # Enable CORS properly
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Create upload folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Download nltk data if needed
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    # Register API blueprints with /api prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(submissions_bp, url_prefix='/api/submissions')
    app.register_blueprint(exercises_bp, url_prefix='/api/exercises')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(pages_bp)
    
    # Root route to serve the React app
    @app.route('/')
    def serve_react():
        return send_from_directory(app.static_folder, 'index.html')
    
    # Catch-all route to handle React Router
    @app.route('/<path:path>')
    def catch_all(path):
        # First try to serve static files
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        # Otherwise, serve the React app and let it handle the routing
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        """Serve files from uploads directory"""
        uploads_path = app.config['UPLOAD_FOLDER']
        return send_from_directory(uploads_path, filename)
    
    # API error handlers
    @app.errorhandler(404)
    def not_found(error):
        # Only return JSON response for API routes
        if request.path.startswith('/api/'):
            return jsonify({"error": "Not found"}), 404
        # For non-API routes, serve the React app
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    return app

# Create the application instance
app = create_app(Config)

# CLI command to initialize the database
@app.cli.command("init-db")
def init_db_command():
    """Initialize the database."""
    with app.app_context():
        db.create_all()
    print("Initialized the database.")

# CLI command to test the neural network
@app.cli.command("test-nn")
def test_nn_command():
    """Test the neural network integration."""
    from backend.services.neural_network_service import get_model, process_text
    
    # Test sentence
    test_sentence = "I have went to the store yesterday."
    
    print(f"Testing neural network with: '{test_sentence}'")
    
    # Initialize and test the model
    with app.app_context():
        model = get_model()
        results = process_text(test_sentence, model)
    
        print(f"Original: {results[0]['original']}")
        print(f"Corrected: {results[0]['corrected']}")
        print("Error spans:")
        for span in results[0]['error_spans']:
            print(f"  - Type: {span['type']}, Text: '{span['text']}'")
    
        print("Neural network test completed successfully!")

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
    app.run(debug=True, port=5001)