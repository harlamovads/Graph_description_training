# backend/routes/pages.py
from flask import Blueprint, render_template, send_from_directory, current_app
import os

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/test-neural-network')
def test_neural_network():
    """Serve the neural network test page."""
    # Path to the HTML file
    html_path = os.path.join(current_app.root_path, 'templates', 'test_neural_network.html')
    
    # If the file exists, serve it
    if os.path.exists(html_path):
        return send_from_directory(os.path.join(current_app.root_path, 'templates'), 'test_neural_network.html')
    
    # Otherwise, return a simple placeholder
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Neural Network Test</title>
    </head>
    <body>
        <h1>Neural Network Test</h1>
        <p>The test page is not available. Please create the templates directory and add the test_neural_network.html file.</p>
    </body>
    </html>
    """