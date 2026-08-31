# backend/routes/activity.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import db
from backend.models.user import User
from backend.models.activity_session import record_heartbeat

activity_bp = Blueprint('activity', __name__)

VALID_ACTIVITY_TYPES = {'task', 'exercise'}


@activity_bp.route('/heartbeat', methods=['POST'])
@jwt_required()
def heartbeat():
    """Record active time on a task submission or practice session in progress.

    The frontend calls this every ~20s while the page is visible (see
    frontend/src/utils/useActivityHeartbeat.js). It's idempotent/self-starting: the first
    call for a given (student, activity_type, target_id) opens the session, later calls
    extend it. The session is closed and its total is stamped onto the resulting
    Submission/PracticeSession when the student actually submits/completes
    (see routes/submissions.py::create_submission, backend/services/practice_service.py).
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    if user.role != 'student':
        return jsonify({"error": "Only students have tracked activity"}), 403

    data = request.get_json() or {}
    activity_type = data.get('activity_type')
    target_id = data.get('target_id')

    if activity_type not in VALID_ACTIVITY_TYPES or not target_id:
        return jsonify({"error": "activity_type ('task'|'exercise') and target_id are required"}), 400

    session = record_heartbeat(current_user_id, activity_type, int(target_id))
    db.session.commit()

    return jsonify({"active_seconds": session.active_seconds}), 200
