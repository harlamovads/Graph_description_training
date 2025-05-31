# backend/routes/analysis.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.neural_network_service import get_model, analyze_submission

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/text', methods=['POST'])
@jwt_required()
def analyze_text():
    """Analyze text using the enhanced neural network model."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({"error": "Text is required"}), 400
    
    text = data.get('text')
    
    try:
        # Process text with enhanced neural network
        analysis_result = analyze_submission(text)
        
        # Check for errors
        if 'error' in analysis_result:
            return jsonify({"error": analysis_result['error']}), 500
        
        return jsonify({
            "results": analysis_result.get("results", []),
            "html_output": analysis_result.get("html_output", ""),
            "total_errors": analysis_result.get("total_errors", 0),
            "sentences": analysis_result.get("sentences", [])
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500