# backend/routes/stats.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models.user import User
from backend.services import stats_service

stats_bp = Blueprint('stats', __name__)


def _require_teacher(current_user_id):
    user = User.query.get_or_404(current_user_id)
    if user.role != 'teacher':
        return None, (jsonify({"error": "Only teachers can access this endpoint"}), 403)
    return user, None


@stats_bp.route('/students', methods=['GET'])
@jwt_required()
def students_summary():
    """Summary stats for every student belonging to the current teacher."""
    current_user_id = int(get_jwt_identity())
    user, error = _require_teacher(current_user_id)
    if error:
        return error

    return jsonify({
        "students": stats_service.teacher_students_summary(current_user_id)
    }), 200


@stats_bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def student_detail(student_id):
    """Detailed stats for one of the current teacher's students: time spent per task,
    month-bucketed task stats, practice-session activity, and error-type distribution."""
    current_user_id = int(get_jwt_identity())
    user, error = _require_teacher(current_user_id)
    if error:
        return error

    detail = stats_service.student_detail(current_user_id, student_id)
    if detail is None:
        return jsonify({"error": "This student is not one of yours"}), 403

    return jsonify(detail), 200
