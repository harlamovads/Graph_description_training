# routes/submissions.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import logging
from backend.models import db
from backend.models.user import User
from backend.models.task import TaskAssignment
from backend.models.submission import Submission
from backend.models.error_log import log_edits, clear_logs_for_source
from backend.models.activity_session import close_open_session
from backend.services.neural_network_service import analyze_submission
from backend.services import errant_service
from backend.utils.security import sanitize_input

submissions_bp = Blueprint('submissions', __name__)
logger = logging.getLogger(__name__)

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
    content = sanitize_input(data.get('content'))

    # Check if assignment exists and belongs to the student
    assignment = TaskAssignment.query.filter_by(
        task_id=task_id,
        student_id=current_user_id
    ).first()

    if not assignment:
        return jsonify({"error": "You don't have access to this task"}), 403

    # Resubmission after review goes through this same route (no separate endpoint): a student
    # may only submit once per assignment at a time, but once the teacher has reviewed it, a
    # new attempt is allowed. The new attempt is a new row (not an edit of the original), so the
    # original's time/errors/score are untouched - it can be told apart later via
    # attempt_number/parent_submission_id.
    existing_submission = assignment.submissions.order_by(Submission.attempt_number.desc()).first()
    if existing_submission:
        if existing_submission.status != 'reviewed':
            return jsonify({"error": "Your last submission for this task is still awaiting review"}), 400
        attempt_number = existing_submission.attempt_number + 1
        parent_submission_id = existing_submission.parent_submission_id or existing_submission.id
    else:
        attempt_number = 1
        parent_submission_id = None

    # Finalize time tracking for this task, if a heartbeat session was open
    time_spent_seconds = close_open_session(current_user_id, 'task', task_id)

    # Create new submission
    new_submission = Submission(
        assignment_id=assignment.id,
        student_id=current_user_id,
        content=content,
        status='submitted',
        time_spent_seconds=time_spent_seconds,
        attempt_number=attempt_number,
        parent_submission_id=parent_submission_id
    )

    db.session.add(new_submission)
    db.session.commit()

    # Analyze submission with enhanced neural network
    try:
        analysis_result = analyze_submission(content)

        if analysis_result and 'error' not in analysis_result:
            new_submission.set_analysis_result(analysis_result)
            db.session.commit()

            # Log every ERRANT edit found so it feeds the per-student error stats
            edits_for_log = [
                (s['id'], s.get('errant_edits', []))
                for s in analysis_result.get('sentences', [])
            ]
            log_edits(current_user_id, 'submission', new_submission.id, edits_for_log)
            db.session.commit()
            logger.info("Neural network analysis completed for submission %s", new_submission.id)
        else:
            logger.warning("Neural network analysis failed for submission %s: %s",
                            new_submission.id, analysis_result.get('error') if analysis_result else 'no result')

    except Exception as e:
        logger.exception("Error during neural network analysis for submission %s", new_submission.id)
        # Continue without analysis rather than failing the submission

    return jsonify({
        "message": "Submission created successfully",
        "submission": new_submission.to_dict()
    }), 201

@submissions_bp.route('/<int:submission_id>', methods=['GET'])
@jwt_required()
def get_submission(submission_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

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
    latest = assignment.latest_submission()
    submission_dict['is_latest_attempt'] = bool(latest and latest.id == submission.id)

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
            # Get every attempt for this assignment (a resubmission is its own row, its own
            # reviewable entry) - not just the latest one.
            for submission in assignment.submissions.all():
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

    # Optional numeric task score (0-10, int or float e.g. 9.5) - not required, a teacher can
    # still review with just text feedback.
    if 'score' in data and data.get('score') is not None:
        try:
            score = float(data.get('score'))
        except (TypeError, ValueError):
            return jsonify({"error": "Score must be a number between 0 and 10"}), 400
        if score < 0 or score > 10:
            return jsonify({"error": "Score must be between 0 and 10"}), 400
        submission.score = score

    # Update submission
    submission.teacher_feedback = sanitize_input(data.get('feedback'))
    submission.status = 'reviewed'
    submission.reviewed_at = datetime.utcnow()

    # Optional per-sentence corrections: a teacher can override the NN's suggested
    # correction for a sentence. When present, recompute that sentence's ERRANT edits
    # against the teacher's version and re-log errors for this submission from the result,
    # so the highlight and the error stats reflect the teacher's final call.
    corrections = data.get('corrections')
    if corrections:
        analysis_result = submission.get_analysis_result() or {'sentences': []}
        sentences = analysis_result.get('sentences', [])

        for sentence in sentences:
            key = str(sentence['id'])
            if key not in corrections:
                continue
            teacher_corrected = sanitize_input(corrections[key])
            sentence['teacher_corrected'] = teacher_corrected
            sentence['errant_edits'] = errant_service.compute_edits(
                sentence['original'], teacher_corrected
            )

        analysis_result['sentences'] = sentences
        analysis_result['total_errors'] = sum(len(s.get('errant_edits', [])) for s in sentences)
        submission.set_analysis_result(analysis_result)

        clear_logs_for_source('submission', submission.id)
        edits_for_log = [(s['id'], s.get('errant_edits', [])) for s in sentences]
        log_edits(current_user_id, 'submission', submission.id, edits_for_log)

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