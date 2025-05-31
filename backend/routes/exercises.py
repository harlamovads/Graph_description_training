# routes/exercises.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db
from backend.models.user import User
from backend.models.submission import Submission
from backend.models.exercise import Exercise, ExerciseAttempt
from backend.models.sentence import Sentence
from backend.models.task import TaskAssignment, Task
from backend.services.exercise_service import generate_exercise_sentences
from backend.services.neural_network_service import analyze_sentence as neural_analyze_sentence
from backend.services.neural_network_service import get_model

exercises_bp = Blueprint('exercises', __name__)

@exercises_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_exercise():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('submission_id') or not data.get('sentence'):
        return jsonify({"error": "Submission ID and sentence are required"}), 400
    
    submission_id = data.get('submission_id')
    original_sentence = data.get('sentence')
    image_url = data.get('image_url')
    
    # Get the submission and verify access (existing access control code)
    submission = Submission.query.get_or_404(submission_id)
    
    if user.role == 'student':
        if submission.student_id != int(current_user_id):
            return jsonify({"error": "You don't have access to this submission"}), 403
    else:  # Teacher
        assignment = TaskAssignment.query.get(submission.assignment_id)
        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404
        task = Task.query.get(assignment.task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        if task.creator_id != int(current_user_id):
            return jsonify({"error": "You don't have access to this submission"}), 403
    
    # Analyze the original sentence using enhanced neural network with correct tags
    try:
        model = get_model()
        analysis_result = model.analyze_text(original_sentence)
        
        if 'error' in analysis_result:
            return jsonify({"error": "Analysis failed or no errors found in the sentence"}), 400
        
        # Get error types - these are now the correct GED tags
        error_types = analysis_result.get('error_types', [])
        error_spans = analysis_result.get('error_spans', [])
        
        if not error_spans and not error_types:
            return jsonify({"error": "No errors found in the sentence"}), 400
        
        print(f"DEBUG: Detected error types: {error_types}")  # Debug logging
            
    except Exception as e:
        return jsonify({"error": f"Neural network analysis failed: {str(e)}"}), 500
    
    # Create enhanced exercise using sentence database with correct tags
    from backend.services.exercise_service import create_enhanced_exercise_from_analysis
    
    try:
        exercise_sentences = create_enhanced_exercise_from_analysis(
            original_sentence, 
            analysis_result, 
            additional_count=4
        )
        
        if len(exercise_sentences) <= 1:
            return jsonify({"error": "Could not find enough similar sentences in database"}), 400
        
        print(f"DEBUG: Generated {len(exercise_sentences)} sentences")  # Debug logging
        
    except Exception as e:
        return jsonify({"error": f"Failed to generate exercise sentences: {str(e)}"}), 500
    
    # Create the exercise
    title = f"Enhanced exercise based on submission #{submission_id}"
    instructions = "Correct the following sentences focusing on the identified error types"
    
    new_exercise = Exercise(
        creator_id=current_user_id,
        title=title,
        instructions=instructions,
        image_url=image_url
    )
    
    # Set sentences with enhanced metadata
    new_exercise.set_sentences(exercise_sentences)
    
    db.session.add(new_exercise)
    db.session.commit()
    
    submission = Submission.query.get_or_404(submission_id)
    student = User.query.get(submission.student_id)

    return jsonify({
        "message": f"Enhanced exercise generated successfully for {student.username}",
        "exercise": new_exercise.to_dict(),
        "assigned_to": student.to_dict(),
        "sentences_from_database": len([s for s in exercise_sentences if s.get('source') == 'database']),
        "total_sentences": len(exercise_sentences),
        "detected_error_types": error_types,  # Include detected error types in response
        "database_sentences_found": len([s for s in exercise_sentences if s.get('source') == 'database']) > 0
    }), 201

@exercises_bp.route('/<int:exercise_id>/attempt', methods=['POST'])
@jwt_required()
def submit_exercise_attempt(exercise_id):
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    # Only students can attempt exercises
    if user.role != 'student':
        return jsonify({"error": "Only students can attempt exercises"}), 403
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('responses'):
        return jsonify({"error": "Responses are required"}), 400
    
    responses = data.get('responses')
    
    # Analyze each response using enhanced neural network with correct tags
    analysis_results = {}
    correct_count = 0
    total_count = len(responses)
    
    for sentence_id, response in responses.items():
        try:
            # Use enhanced neural network analysis
            model = get_model()
            result = model.analyze_text(response)
            
            if 'error' in result:
                # Fallback to simpler analysis
                from backend.services.analysis_service import analyze_sentence
                result = analyze_sentence(response)
            else:
                # Convert enhanced analysis to expected format with correct tags
                error_spans = result.get('error_spans', [])
                formatted_result = {
                    'errors': []
                }
                
                for span in error_spans:
                    formatted_result['errors'].append({
                        'type': span['type'],  # This is now correct GED tag
                        'start': span.get('position', -1),
                        'end': span.get('position', -1) + 1,
                        'original': span['token'],
                        'suggestion': ""
                    })
                
                result = formatted_result
            
            analysis_results[sentence_id] = result
            
            # Count correct responses (no errors)
            if not result.get('errors') or len(result.get('errors', [])) == 0:
                correct_count += 1
                
        except Exception as e:
            # Fallback to simpler analysis
            from backend.services.analysis_service import analyze_sentence
            result = analyze_sentence(response)
            analysis_results[sentence_id] = result
            
            # Count correct responses (no errors)
            if not result.get('errors') or len(result.get('errors', [])) == 0:
                correct_count += 1
    
    # Calculate score
    score = (correct_count / total_count) * 100 if total_count > 0 else 0
    
    # Create a new attempt
    new_attempt = ExerciseAttempt(
        exercise_id=exercise_id,
        student_id=current_user_id,
        score=score
    )
    
    # Set responses and analysis results
    new_attempt.set_responses(responses)
    new_attempt.set_analysis_result(analysis_results)
    
    db.session.add(new_attempt)
    db.session.commit()
    
    return jsonify({
        "message": "Exercise attempt submitted successfully",
        "score": score,
        "analysis": analysis_results
    }), 201

@exercises_bp.route('/', methods=['GET'])
@jwt_required()
def get_exercises():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    # Different logic for teachers and students
    if user.role == 'teacher':
        # Teachers see all their exercises (draft and published)
        exercises = Exercise.query.filter_by(creator_id=current_user_id).all()
    else:  # Student
        # Students only see published exercises from their submissions
        submissions = Submission.query.filter_by(student_id=current_user_id).all()
        submission_ids = [sub.id for sub in submissions]
        # Only show published exercises
        exercises = Exercise.query.filter(
            Exercise.id.in_(submission_ids),
            Exercise.status == 'published'
        ).all()
    
    # Add attempts for each exercise (existing logic)
    result = []
    for exercise in exercises:
        exercise_dict = exercise.to_dict()
        
        # Get attempts for this exercise by the current student
        if user.role == 'student':
            attempts = ExerciseAttempt.query.filter_by(
                exercise_id=exercise.id, 
                student_id=current_user_id
            ).all()
        else:
            # For teachers, get all attempts
            attempts = ExerciseAttempt.query.filter_by(exercise_id=exercise.id).all()
        
        # Add attempts data to the exercise
        exercise_dict['attempts'] = []
        for attempt in attempts:
            attempt_dict = {
                'id': attempt.id,
                'student_id': attempt.student_id,
                'score': attempt.score,
                'completed_at': attempt.completed_at.isoformat(),
                'responses': attempt.get_responses(),
                'analysis_result': attempt.get_analysis_result()
            }
            exercise_dict['attempts'].append(attempt_dict)
        
        result.append(exercise_dict)

    return jsonify({
        "exercises": result
    }), 200

@exercises_bp.route('/<int:exercise_id>', methods=['GET'])
@jwt_required()
def get_exercise(exercise_id):
    current_user_id = get_jwt_identity()
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if user has access to this exercise
    if int(exercise.creator_id) != int(current_user_id):
        submission = Submission.query.get(exercise.id)
        if int(submission.student_id) != int(current_user_id):
            return jsonify({"error": "You don't have access to this exercise"}), 403
    
    return jsonify(exercise.to_dict()), 200

@exercises_bp.route('/<int:exercise_id>/attempts', methods=['GET'])
@jwt_required()
def get_exercise_attempts(exercise_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(int(current_user_id))
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if user has access to this exercise
    if exercise.creator_id != current_user_id and user.role == 'student':
        # For students, they can only see their own attempts
        attempts = ExerciseAttempt.query.filter_by(
            exercise_id=exercise_id, student_id=current_user_id).all()
    else:
        # For teachers or exercise creators, they can see all attempts
        attempts = ExerciseAttempt.query.filter_by(exercise_id=exercise_id).all()
    
    result = []
    for attempt in attempts:
        attempt_dict = {
            'id': attempt.id,
            'student_id': attempt.student_id,
            'score': attempt.score,
            'responses': attempt.get_responses(),
            'analysis_result': attempt.get_analysis_result(),
            'completed_at': attempt.completed_at.isoformat()
        }
        
        # Add student info for teachers
        if user.role == 'teacher':
            student = User.query.get(attempt.student_id)
            attempt_dict['student'] = student.to_dict()
        
        result.append(attempt_dict)
    
    return jsonify({
        "attempts": result
    }), 200

@exercises_bp.route('/sentence-database', methods=['GET'])
@jwt_required()
def get_sentence_database():
    """Endpoint to retrieve sentences from the database for exercise creation"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Get query parameters for filtering
    error_type = request.args.get('error_type')
    
    # Basic query
    query = Sentence.query
    
    # Apply filters if provided
    if error_type:
        # This is a simple implementation - in a real app, you would need more sophisticated filtering
        # based on the JSON error_tags field
        sentences = []
        all_sentences = query.all()
        
        for sentence in all_sentences:
            tags = sentence.get_error_tags()
            for tag in tags:
                tag_type = tag.get('native_tag') or tag.get('first_level_tag')
                if tag_type and error_type.lower() in tag_type.lower():
                    sentences.append(sentence)
                    break
    else:
        # No filters, get all sentences
        sentences = query.all()
    
    # Format the response
    result = []
    for sentence in sentences:
        result.append({
            'id': sentence.id,
            'text': sentence.text,
            'error_tags': sentence.get_error_tags()
        })
    
    return jsonify({
        'sentences': result
    }), 200

@exercises_bp.route('/<int:exercise_id>/publish', methods=['POST'])
@jwt_required()
def publish_exercise(exercise_id):
    """Publish a draft exercise to make it available to students"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    # Only teachers can publish exercises
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can publish exercises"}), 403
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if teacher owns this exercise
    if exercise.creator_id != int(current_user_id):
        return jsonify({"error": "You can only publish your own exercises"}), 403
    
    # Update status to published
    exercise.status = 'published'
    db.session.commit()
    
    return jsonify({
        "message": "Exercise published successfully",
        "exercise": exercise.to_dict()
    }), 200


@exercises_bp.route('/<int:exercise_id>/update', methods=['PUT'])
@jwt_required()
def update_exercise(exercise_id):
    """Update exercise title, instructions, or sentences before publishing"""
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    # Only teachers can update exercises
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can update exercises"}), 403
    
    exercise = Exercise.query.get_or_404(exercise_id)
    
    # Check if teacher owns this exercise
    if exercise.creator_id != int(current_user_id):
        return jsonify({"error": "You can only update your own exercises"}), 403
    
    data = request.get_json()
    
    # Update fields if provided
    if 'title' in data:
        exercise.title = data['title']
    if 'instructions' in data:
        exercise.instructions = data['instructions']
    if 'sentences' in data:
        exercise.set_sentences(data['sentences'])
    
    db.session.commit()
    
    return jsonify({
        "message": "Exercise updated successfully",
        "exercise": exercise.to_dict()
    }), 200

@exercises_bp.route('/sentence-database/status', methods=['GET'])
@jwt_required()
def get_sentence_database_status():
    """Get status and statistics about the sentence database"""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    from backend.services.exercise_service import get_sentence_database_stats
    
    try:
        stats = get_sentence_database_stats()
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": f"Failed to get database stats: {str(e)}"}), 500