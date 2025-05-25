# routes/submissions.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from backend.models import db
from backend.models.user import User
from backend.models.task import TaskAssignment
from backend.models.submission import Submission
from backend.services.neural_network_service import analyze_submission

submissions_bp = Blueprint('submissions', __name__)

@submissions_bp.route('/', methods=['POST'])
@jwt_required()
def create_submission():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only students can submit tasks
    if user.role != 'student':
        return jsonify({"error": "Only students can submit tasks"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('task_id') or not data.get('content'):
        return jsonify({"error": "Task ID and content are required"}), 400
    
    task_id = data.get('task_id')
    content = data.get('content')
    
    # Check if assignment exists and belongs to the student
    assignment = TaskAssignment.query.filter_by(
        task_id=task_id,
        student_id=current_user_id
    ).first()
    
    if not assignment:
        return jsonify({"error": "You don't have access to this task"}), 403
    
    # Check if submission already exists
    existing_submission = Submission.query.filter_by(assignment_id=assignment.id).first()
    if existing_submission:
        return jsonify({"error": "You've already submitted this assignment"}), 400
    
    # Create new submission
    new_submission = Submission(
        assignment_id=assignment.id,
        student_id=current_user_id,
        content=content,
        status='submitted'
    )
    
    db.session.add(new_submission)
    db.session.commit()
    
    # Analyze submission
    analysis_result = analyze_submission(content)
    
    if analysis_result:
        new_submission.set_analysis_result(analysis_result)
        db.session.commit()
    
    return jsonify({
        "message": "Submission created successfully",
        "submission": new_submission.to_dict()
    }), 201

@submissions_bp.route('/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Add these debug lines:
    print(f"DEBUG: JWT Identity: {get_jwt_identity()}")
    print(f"DEBUG: Current User ID: {current_user_id}")
    print(f"DEBUG: User Role: {user.role}")
    
    submission = Submission.query.get_or_404(submission_id)
    print(f"DEBUG: Submission ID: {submission.id}")
    print(f"DEBUG: Submission Student ID: {submission.student_id}")
    print(f"DEBUG: Access Check: {submission.student_id == current_user_id}")
    
    submission = Submission.query.get_or_404(submission_id)
    
    # Check if user has access to this submission
    if user.role == 'student':
        if submission.student_id != current_user_id:
            return jsonify({"error": "You don't have access to this submission"}), 403
    else:  # Teacher
        assignment = TaskAssignment.query.get(submission.assignment_id)
        task = assignment.task
        if task.creator_id != current_user_id:
            return jsonify({"error": "You don't have access to this submission"}), 403
    
    assignment = TaskAssignment.query.get(submission.assignment_id)
    task = assignment.task

    submission_dict = submission.to_dict()
    submission_dict['task'] = task.to_dict()

    return jsonify(submission_dict), 200

@submissions_bp.route('/teacher', methods=['GET'])
@jwt_required()
def get_teacher_submissions():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only teachers can access this endpoint
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can access this endpoint"}), 403
    
    # Get all submissions for tasks created by this teacher
    submissions = []
    
    # Get all tasks created by the teacher
    tasks = user.tasks_created.all()
    
    for task in tasks:
        # Get all assignments for this task
        assignments = task.assignments.all()
        
        for assignment in assignments:
            # Get submission for this assignment
            submission = assignment.submission
            if submission:
                # Add student information
                student = User.query.get(assignment.student_id)
                submission_dict = submission.to_dict()
                submission_dict['student'] = student.to_dict()
                submission_dict['task'] = task.to_dict()
                submissions.append(submission_dict)
    
    return jsonify({
        "submissions": submissions
    }), 200

@submissions_bp.route('/<int:submission_id>/review', methods=['POST'])
@jwt_required()
def review_submission(submission_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only teachers can review submissions
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can review submissions"}), 403
    
    submission = Submission.query.get_or_404(submission_id)
    
    # Check if the teacher has access to this submission
    assignment = TaskAssignment.query.get(submission.assignment_id)
    task = assignment.task
    if task.creator_id != current_user_id:
        return jsonify({"error": "You don't have access to this submission"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('feedback'):
        return jsonify({"error": "Feedback is required"}), 400
    
    # Update submission
    submission.teacher_feedback = data.get('feedback')
    submission.status = 'reviewed'
    submission.reviewed_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        "message": "Submission reviewed successfully",
        "submission": submission.to_dict()
    }), 200

@submissions_bp.route('/student', methods=['GET'])
@jwt_required()
def get_student_submissions():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only students can access this endpoint
    if user.role != 'student':
        return jsonify({"error": "Only students can access this endpoint"}), 403
    
    # Get all submissions for this student
    submissions = Submission.query.filter_by(student_id=current_user_id).all()
    
    result = []
    for submission in submissions:
        assignment = TaskAssignment.query.get(submission.assignment_id)
        task = assignment.task
        
        submission_dict = submission.to_dict()
        submission_dict['task'] = task.to_dict()
        result.append(submission_dict)
    
    return jsonify({
        "submissions": result
    }), 200