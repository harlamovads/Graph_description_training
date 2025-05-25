# backend/routes/analysis.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.services.neural_network_service import process_text, get_model, generate_html_output

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/text', methods=['POST'])
@jwt_required()
def analyze_text():
    """Analyze text using the neural network model."""
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({"error": "Text is required"}), 400
    
    text = data.get('text')
    
    try:
        # Process text with neural network
        model = get_model()
        results = process_text(text, model)
        
        # Generate HTML output
        html_output = generate_html_output(results)
        
        return jsonify({
            "results": results,
            "html_output": html_output,
            "total_errors": sum(len(result["error_spans"]) for result in results)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500