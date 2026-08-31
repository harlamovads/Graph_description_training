# backend/routes/practice.py
from functools import wraps
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db
from backend.models.user import User
from backend.models.submission import Submission
from backend.models.task import TaskAssignment
from backend.models.practice_session import PracticeSession
from backend.models.practice_assignment import PracticeAssignment
from backend.services import practice_service, stats_service

practice_bp = Blueprint('practice', __name__)


def _handle_practice_error(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except practice_service.PracticeError as e:
            return jsonify({"error": e.message}), e.status_code
    return wrapped


@practice_bp.route('/start', methods=['POST'])
@jwt_required()
@_handle_practice_error
def start():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    if user.role != 'student':
        return jsonify({"error": "Only students can start a practice session"}), 403

    data = request.get_json() or {}
    submission_id = data.get('submission_id')
    sentence_index = data.get('sentence_index')
    if submission_id is None or sentence_index is None:
        return jsonify({"error": "submission_id and sentence_index are required"}), 400

    session = practice_service.start_session(current_user_id, submission_id, sentence_index)
    return jsonify(practice_service.session_state(session)), 201


@practice_bp.route('/<int:session_id>', methods=['GET'])
@jwt_required()
@_handle_practice_error
def get_session(session_id):
    current_user_id = int(get_jwt_identity())
    session = practice_service.get_owned_session(current_user_id, session_id)
    return jsonify(practice_service.session_state(session)), 200


@practice_bp.route('/<int:session_id>/submit', methods=['POST'])
@jwt_required()
@_handle_practice_error
def submit(session_id):
    current_user_id = int(get_jwt_identity())
    session = practice_service.get_owned_session(current_user_id, session_id)

    data = request.get_json() or {}
    result = practice_service.submit_round(session, data.get('text'))

    return jsonify({
        'resolved': result['resolved'],
        'edits': result['edits'],
        'target': result['target'],
        'session': practice_service.session_state(result['session'])
    }), 200


@practice_bp.route('/<int:session_id>/stop', methods=['POST'])
@jwt_required()
@_handle_practice_error
def stop(session_id):
    current_user_id = int(get_jwt_identity())
    session = practice_service.get_owned_session(current_user_id, session_id)
    session = practice_service.stop_session(session)
    return jsonify(practice_service.session_state(session)), 200


@practice_bp.route('/assign', methods=['POST'])
@jwt_required()
@_handle_practice_error
def assign():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can assign practice sentences"}), 403

    data = request.get_json() or {}
    submission_id = data.get('submission_id')
    sentence_index = data.get('sentence_index')
    if submission_id is None or sentence_index is None:
        return jsonify({"error": "submission_id and sentence_index are required"}), 400

    submission = Submission.query.get_or_404(submission_id)
    assignment = TaskAssignment.query.get(submission.assignment_id)
    if not assignment or not assignment.task or assignment.task.creator_id != current_user_id:
        return jsonify({"error": "You don't have access to this submission"}), 403

    analysis = submission.get_analysis_result() or {}
    sentence = next((s for s in analysis.get('sentences', []) if s['id'] == sentence_index), None)
    if not sentence or not sentence.get('errant_edits'):
        return jsonify({"error": "This sentence has no errors to practice"}), 400

    existing = PracticeAssignment.query.filter_by(
        submission_id=submission_id,
        sentence_index=sentence_index,
        practice_session_id=None
    ).first()
    if existing:
        return jsonify({"message": "Already assigned", "assignment": existing.to_dict()}), 200

    new_assignment = PracticeAssignment(
        teacher_id=current_user_id,
        student_id=submission.student_id,
        submission_id=submission_id,
        sentence_index=sentence_index
    )
    db.session.add(new_assignment)
    db.session.commit()

    return jsonify({"message": "Sentence assigned for practice", "assignment": new_assignment.to_dict()}), 201


@practice_bp.route('/assignments', methods=['GET'])
@jwt_required()
def assignments():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    if user.role != 'student':
        return jsonify({"error": "Only students can access this endpoint"}), 403

    rows = PracticeAssignment.query.filter_by(
        student_id=current_user_id, practice_session_id=None
    ).order_by(PracticeAssignment.assigned_at.desc()).all()

    return jsonify({"assignments": [a.to_dict() for a in rows]}), 200


@practice_bp.route('/teacher', methods=['GET'])
@jwt_required()
def teacher_sessions():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can access this endpoint"}), 403

    student_ids = {s.id for s in stats_service._get_teacher_students(current_user_id)}
    if not student_ids:
        return jsonify({"sessions": []}), 200

    rows = PracticeSession.query.filter(
        PracticeSession.student_id.in_(student_ids)
    ).order_by(PracticeSession.started_at.desc()).all()

    result = []
    for session in rows:
        d = session.to_dict()
        d['student'] = session.student.to_dict()
        submission = session.submission
        assignment = TaskAssignment.query.get(submission.assignment_id) if submission else None
        d['task_title'] = assignment.task.title if assignment and assignment.task else None
        result.append(d)

    return jsonify({"sessions": result}), 200


@practice_bp.route('/<int:session_id>/review', methods=['GET'])
@jwt_required()
def review(session_id):
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can access this endpoint"}), 403

    session = PracticeSession.query.get_or_404(session_id)
    student_ids = {s.id for s in stats_service._get_teacher_students(current_user_id)}
    if session.student_id not in student_ids:
        return jsonify({"error": "This student is not one of yours"}), 403

    d = session.to_review_dict()
    d['student'] = session.student.to_dict()
    submission = session.submission
    assignment = TaskAssignment.query.get(submission.assignment_id) if submission else None
    d['task_title'] = assignment.task.title if assignment and assignment.task else None

    return jsonify(d), 200
