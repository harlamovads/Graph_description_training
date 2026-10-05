# backend/routes/analysis.py
import os

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.neural_network_service import get_model, analyze_submission
from backend.services.load_manager import manager as load_manager, AtCapacity

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/text', methods=['POST'])
@jwt_required()
def analyze_text():
    """Analyze text using the enhanced neural network model."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({"error": "Text is required"}), 400
    
    text = data.get('text')

    # Cap the input: this endpoint runs the neural network once per sentence, so an
    # authenticated user could otherwise post a novel and tie up the server's CPU.
    max_chars = int(os.environ.get('MAX_ANALYSIS_CHARS', '10000'))
    if len(text) > max_chars:
        return jsonify({
            "error": f"Text is too long to analyse (limit {max_chars} characters)"
        }), 413

    try:
        # Queue behind the same analysis budget as submissions and practice rounds, so this
        # endpoint cannot starve them (see backend/services/load_manager.py).
        with load_manager.slot('analysis'):
            analysis_result = analyze_submission(text)
        
        # Check for errors
        if 'error' in analysis_result:
            return jsonify({"error": analysis_result['error']}), 500
        
        return jsonify({
            "sentences": analysis_result.get("sentences", []),
            "total_errors": analysis_result.get("total_errors", 0),
            "ged_error_types": analysis_result.get("ged_error_types", [])
        }), 200
        
    except AtCapacity as busy:
        response = jsonify({"error": busy.message, "load": busy.snapshot})
        response.status_code = 503
        response.headers['Retry-After'] = str(busy.retry_after)
        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500