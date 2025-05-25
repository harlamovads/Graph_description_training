# routes/tasks.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from backend.models import db
from backend.models.user import User
from backend.models.task import Task, TaskAssignment
from backend.services.task_service import upload_file_to_s3, get_tasks_for_user

tasks_bp = Blueprint('tasks', __name__)

# Helper function to check allowed file extensions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    tasks = get_tasks_for_user(user)
    
    return jsonify({
        "tasks": [task.to_dict() for task in tasks]
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_user_id = int(get_jwt_identity())
    task = Task.query.get_or_404(task_id)
    
    # Check if user has access to this task
    user = User.query.get(current_user_id)
    if user.role == 'teacher':
        if task.creator_id != current_user_id:
            return jsonify({"error": "You don't have access to this task"}), 403
    else:  # Student
        assignments = TaskAssignment.query.filter_by(
            student_id=current_user_id, task_id=task_id).all()
        if not assignments:
            return jsonify({"error": "You don't have access to this task"}), 403
    
    return jsonify(task.to_dict()), 200

@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Extract task data
    title = request.form.get('title')
    description = request.form.get('description')
    is_from_database = request.form.get('is_from_database', 'false').lower() == 'true'
    
    # Validate required fields
    if not title or not description:
        return jsonify({"error": "Title and description are required"}), 400
    
    # Handle image upload (now required)
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])
                
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            file.save(file_path)
            image_url = f"/uploads/{unique_filename}"
    
    # If no image provided, return error
    if not image_url:
        return jsonify({"error": "Image is required"}), 400
    
    # Create new task
    new_task = Task(
        title=title,
        description=description,
        image_url=image_url,
        is_from_database=is_from_database,
        creator_id=current_user_id
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({
        "message": "Task created successfully",
        "task": new_task.to_dict()
    }), 201

@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_task(task_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only teachers can assign tasks
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can assign tasks"}), 403
    
    # Validate task exists and belongs to the teacher
    task = Task.query.get_or_404(task_id)
    if task.creator_id != current_user_id:
        return jsonify({"error": "You can only assign your own tasks"}), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('student_ids'):
        return jsonify({"error": "Student IDs are required"}), 400
    
    student_ids = data.get('student_ids')
    due_date = data.get('due_date')
    
    # Convert due_date string to datetime if provided
    due_date_obj = None
    if due_date:
        try:
            due_date_obj = datetime.fromisoformat(due_date)
        except ValueError:
            return jsonify({"error": "Invalid date format for due_date"}), 400
    
    # Create assignments for each student
    assignments = []
    for student_id in student_ids:
        # Check if student exists
        student = User.query.get(student_id)
        if not student or student.role != 'student':
            continue
        
        # Check if assignment already exists
        existing = TaskAssignment.query.filter_by(
            task_id=task_id, student_id=student_id).first()
        if existing:
            continue
        
        # Create new assignment
        assignment = TaskAssignment(
            task_id=task_id,
            student_id=student_id,
            due_date=due_date_obj
        )
        
        db.session.add(assignment)
        assignments.append(assignment)
    
    db.session.commit()
    
    return jsonify({
        "message": f"Task assigned to {len(assignments)} students successfully"
    }), 201

@tasks_bp.route('/database', methods=['GET'])
@jwt_required()
def get_database_tasks():
    # Get tasks from database (predefined tasks)
    database_tasks = Task.query.filter_by(is_from_database=True).all()
    
    return jsonify({
        "tasks": [task.to_dict() for task in database_tasks]
    }), 200