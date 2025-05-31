#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/app')

from app import create_app

def test_model_loading():
    app = create_app()
    
    with app.app_context():
        print("Testing model loading in isolation...")
        
        try:
            from backend.services.neural_network_service import HuggingFaceT5GEDInference
            
            model_path = 'Zlovoblachko/REAlEC_2step_model_testing'
            ged_model_path = 'Zlovoblachko/11tag-electra-grammar-stage2'
            
            print(f"Loading models: {model_path}, {ged_model_path}")
            
            model = HuggingFaceT5GEDInference(model_path, ged_model_path)
            
            print("Model loaded successfully!")
            
            # Test a simple correction
            test_text = "I have went to store yesterday."
            result = model.analyze_text(test_text)
            print(f"Test analysis result: {result}")
            
        except Exception as e:
            print(f"Model loading failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_model_loading()