# routes/tasks.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import shutil
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


def _save_uploaded_image(file_storage):
    """Save an uploaded image and return the URL to serve it from, or None if unusable."""
    if not file_storage or not file_storage.filename or not allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    file_storage.save(os.path.join(upload_folder, unique_filename))
    return f"/uploads/{unique_filename}"


def _duplicate_image(image_url):
    """Copy the file behind an existing task's image so a forked task owns its own.

    Sharing the URL would work today, but it quietly couples two tasks that are meant to be
    independent: whatever happens to the original's file later would change the copy too.
    If the source file is missing we fall back to reusing the URL rather than failing the edit.
    """
    if not image_url or not image_url.startswith('/uploads/'):
        return image_url
    upload_folder = current_app.config['UPLOAD_FOLDER']
    source = os.path.join(upload_folder, os.path.basename(image_url))
    if not os.path.exists(source):
        current_app.logger.warning("Task image %s is missing; the copy will reuse it", image_url)
        return image_url
    new_name = f"{uuid.uuid4()}_{os.path.basename(image_url).split('_', 1)[-1]}"
    shutil.copyfile(source, os.path.join(upload_folder, new_name))
    return f"/uploads/{new_name}"

@tasks_bp.route('/', methods=['GET'])
@jwt_required()
def get_tasks():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    tasks = get_tasks_for_user(user)
    task_dicts = [task.to_dict() for task in tasks]

    # due_date lives on the student's own TaskAssignment, not on the shared Task, so it never
    # made it into the payload - merge it in here (one query, keyed by task) so students
    # actually see the deadline their teacher set. Teachers set it per student, so their view
    # of a task has no single due date to report.
    if user.role == 'student':
        due_by_task = {
            a.task_id: a.due_date
            for a in TaskAssignment.query.filter_by(student_id=current_user_id).all()
        }
        for task_dict in task_dicts:
            due = due_by_task.get(task_dict['id'])
            task_dict['due_date'] = due.isoformat() if due else None

    return jsonify({
        "tasks": task_dicts
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_user_id = int(get_jwt_identity())
    task = Task.query.get_or_404(task_id)
    
    # Check if user has access to this task
    user = User.query.get(current_user_id)
    task_dict = task.to_dict()
    if user.role == 'teacher':
        # Own task, or one published to the shared task database by another teacher.
        if task.creator_id != current_user_id and not task.is_from_database:
            return jsonify({"error": "You don't have access to this task"}), 403
    else:  # Student
        assignments = TaskAssignment.query.filter_by(
            student_id=current_user_id, task_id=task_id).all()
        if not assignments:
            return jsonify({"error": "You don't have access to this task"}), 403
        # Same as in get_tasks(): surface this student's own due date.
        due = assignments[0].due_date
        task_dict['due_date'] = due.isoformat() if due else None

    return jsonify(task_dict), 200

@tasks_bp.route('/', methods=['POST'])
@jwt_required()
def create_task():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    # Teachers only. This check was missing, so a student could POST a task - and with the
    # shared task database that meant injecting content into every teacher's task list.
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can create tasks"}), 403

    # Extract task data
    title = request.form.get('title')
    description = request.form.get('description')
    is_from_database = request.form.get('is_from_database', 'false').lower() == 'true'
    
    # Validate required fields
    if not title or not description:
        return jsonify({"error": "Title and description are required"}), 400
    
    # Handle image upload (now required)
    image_url = _save_uploaded_image(request.files.get('image'))
    
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

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Edit a task - or, for a shared task you don't own, fork it and edit the fork.

    A task in the shared database is visible to every teacher, so letting any of them edit it in
    place would silently change a task other teachers are already using (and whose students have
    already submitted against it). Instead:

      * the creator edits their own task in place;
      * another teacher gets their own private copy with the edits applied, leaving the original
        untouched - the response says so via "forked", so the UI can explain what happened;
      * a task that is neither yours nor shared is not yours to touch.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can edit tasks"}), 403

    task = Task.query.get_or_404(task_id)

    is_creator = task.creator_id == current_user_id
    if not is_creator and not task.is_from_database:
        return jsonify({"error": "You don't have access to this task"}), 403

    # Only the fields actually sent are changed, so a form that omits one leaves it alone.
    title = request.form.get('title', task.title)
    description = request.form.get('description', task.description)
    if not title.strip() or not description.strip():
        return jsonify({"error": "Title and description are required"}), 400

    if 'is_from_database' in request.form:
        is_from_database = request.form.get('is_from_database', 'false').lower() == 'true'
    else:
        # A fork defaults to private: copying someone's shared task to tweak it for your own
        # class shouldn't publish a near-duplicate back into everyone's task database.
        is_from_database = task.is_from_database if is_creator else False

    new_image_url = _save_uploaded_image(request.files.get('image'))
    if 'image' in request.files and request.files['image'].filename and not new_image_url:
        return jsonify({"error": "Unsupported image type - use PNG, JPG, JPEG or GIF"}), 400

    if is_creator:
        task.title = title
        task.description = description
        task.is_from_database = is_from_database
        if new_image_url:
            task.image_url = new_image_url
        db.session.commit()
        return jsonify({
            "message": "Task updated successfully",
            "task": task.to_dict(),
            "forked": False
        }), 200

    copy = Task(
        title=title,
        description=description,
        image_url=new_image_url or _duplicate_image(task.image_url),
        is_from_database=is_from_database,
        creator_id=current_user_id
    )
    db.session.add(copy)
    db.session.commit()
    return jsonify({
        "message": "This task belongs to another teacher, so your changes were saved to your own "
                   "copy of it. The original is unchanged.",
        "task": copy.to_dict(),
        "forked": True,
        "original_task_id": task.id
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
    # A shared-database task is assignable by any teacher; anything else stays owner-only.
    if task.creator_id != current_user_id and not task.is_from_database:
        return jsonify({"error": "You can only assign your own tasks or shared ones"}), 403
    
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