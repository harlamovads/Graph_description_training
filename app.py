# app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask import send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from backend.config import Config
from backend.models import db
from backend.routes.auth import auth_bp
from backend.routes.tasks import tasks_bp
from backend.routes.submissions import submissions_bp
from backend.routes.practice import practice_bp
from backend.routes.analysis import analysis_bp
from backend.routes.pages import pages_bp
from backend.routes.activity import activity_bp
from backend.routes.stats import stats_bp
from backend.services.load_manager import manager as load_manager
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
    Migrate(app, db, directory='database/migrations')
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
    
    # Behind nginx, so trust one hop of X-Forwarded-* headers. Without this every request
    # looks like it came from the proxy, which would make the rate limiter below throttle all
    # users as if they shared one IP, and would report the wrong scheme in redirects.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # CORS: pin this to your domain in production via CORS_ORIGINS (comma-separated). The old
    # "*" let any site on the internet call the API with a token it had got hold of.
    cors_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '*').split(',') if o.strip()]
    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # Rate limiting. Login/registration are the brute-forceable endpoints, so they get tight
    # per-IP limits; everything else gets a generous default that only catches runaway clients.
    # Storage is in-process, which is correct for the single gunicorn worker this app runs
    # (see gunicorn.conf.py) - add RATELIMIT_STORAGE_URI=redis://... if that ever changes.
    limiter = Limiter(
        get_remote_address,
        app=app,
        # Deliberately generous: this is a per-IP backstop against a runaway client, and a
        # whole class shares one NAT address. The activity heartbeat alone is ~180 requests an
        # hour per student, so 20 students are already ~3600/h before anything else.
        default_limits=[os.environ.get('RATELIMIT_DEFAULT', '10000 per hour')],
        storage_uri=os.environ.get('RATELIMIT_STORAGE_URI', 'memory://'),
        strategy='fixed-window'
    )
    app.extensions['limiter'] = limiter
    
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
    app.register_blueprint(practice_bp, url_prefix='/api/practice')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    app.register_blueprint(activity_bp, url_prefix='/api/activity')
    app.register_blueprint(stats_bp, url_prefix='/api/stats')
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
    
    @app.errorhandler(429)
    def rate_limited(error):
        # Flask-Limiter otherwise returns Werkzeug's HTML page, which the frontend can't read
        # (it looks for .error in a JSON body) - the student would just see "Login failed" with
        # no clue that waiting fixes it. Nothing is locked: the counter simply expires.
        retry_after = getattr(error, 'retry_after', None)
        description = getattr(error, 'description', '') or ''
        response = jsonify({
            "error": "Too many attempts. Please wait a few minutes and try again.",
            "limit": str(description)
        })
        response.status_code = 429
        response.headers['Retry-After'] = str(retry_after or 300)
        return response

    @app.errorhandler(413)
    def too_large(error):
        return jsonify({"error": "That file is too large (limit 10 MB)."}), 413

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    # Limits are attached here, after every route exists.
    #
    # A whole class typically shares one NAT address, so purely per-IP limits on login and
    # registration would lock out 20 students signing in together - the limit has to be loose
    # per IP. The protection that actually matters against credential stuffing is per-ACCOUNT,
    # so login carries a second, strict limit keyed on the submitted email. Note clients can't
    # game this: nginx appends the real peer to X-Forwarded-For and ProxyFix(x_for=1) reads
    # that rightmost hop, so a spoofed header doesn't buy a fresh bucket.
    def _login_email_key():
        body = request.get_json(silent=True) or {}
        return (body.get('email') or get_remote_address() or '')[:120].lower()

    login_view = app.view_functions.get('auth.login')
    if login_view is not None:
        per_account = limiter.limit(
            os.environ.get('RATELIMIT_LOGIN_ACCOUNT', '10 per 5 minutes'),
            key_func=_login_email_key)
        per_ip = limiter.limit(os.environ.get('RATELIMIT_LOGIN_IP', '60 per minute'))
        app.view_functions['auth.login'] = per_ip(per_account(login_view))

    # Changing a password verifies the current one, so throttle it to slow guessing.
    change_view = app.view_functions.get('auth.change_password')
    if change_view is not None:
        app.view_functions['auth.change_password'] = limiter.limit(
            os.environ.get('RATELIMIT_PASSWORD_CHANGE', '20 per hour'))(change_view)

    register_view = app.view_functions.get('auth.register')
    if register_view is not None:
        app.view_functions['auth.register'] = limiter.limit(
            os.environ.get('RATELIMIT_REGISTER', '30 per minute;200 per hour'))(register_view)

    # activity.heartbeat is exempt as well: it fires every 20s per active student and
    # throttling it would silently corrupt the time-spent statistics.
    for endpoint in ('serve_react', 'catch_all', 'serve_uploads', 'health_check',
                     'activity.heartbeat'):
        view = app.view_functions.get(endpoint)
        if view is not None:
            app.view_functions[endpoint] = limiter.exempt(view)

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

@app.route('/health')
def health_check():
    """Health check endpoint for Docker"""
    return jsonify({"status": "healthy"}), 200

@app.route('/health/load')
def load_status():
    """Current analysis load: how many are running, how many waiting, how long a new one waits.

    Unauthenticated on purpose - it exposes no student data, and it is what a monitoring check
    or the operator can poll while a class is submitting. The frontend also reads it to warn
    students before they start writing that the server is busy.
    """
    snap = load_manager.snapshot()
    if snap['queued'] >= snap['queue_limit']:
        level = 'overloaded'
    elif snap['saturated'] or snap['queued'] > snap['capacity']:
        level = 'busy'
    else:
        level = 'ok'
    snap['level'] = level
    return jsonify(snap), 200

# These two routes are defined after create_app() has run, so the exemption loop inside it never
# saw them (app.view_functions had no entry yet). Exempt them here: a health probe every few
# seconds must never be rate-limited, or monitoring itself would mark the app down.
for _endpoint in ('health_check', 'load_status'):
    _view = app.view_functions.get(_endpoint)
    if _view is not None:
        app.view_functions[_endpoint] = app.extensions['limiter'].exempt(_view)

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()

        # Load the neural network and the ERRANT annotator before accepting traffic. Loading
        # them lazily on first request meant a burst of simultaneous first requests each
        # triggered their own load (~2.4 GB apiece) - enough to OOM an 8 GB server within
        # seconds, which is exactly what a class all submitting at 9am looks like. Also pins
        # torch's thread count; see configure_cpu_threads().
        try:
            from backend.services.neural_network_service import get_model, configure_cpu_threads
            from backend.services import errant_service
            configure_cpu_threads()
            print("Warming up neural network and ERRANT ...")
            get_model()
            errant_service.get_annotator()
            print("Models ready.")
        except Exception as warm_err:
            print(f"Warning: model warm-up failed ({warm_err}); will load on first request.")
    
    # Make sure to bind to all interfaces, not just localhost
    app.run(host='0.0.0.0', port=5001, debug=False)