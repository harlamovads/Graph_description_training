# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from backend.models.task import Task, TaskAssignment
from backend.models import db
from backend.models.user import User, Invitation
import secrets
import uuid
from datetime import datetime
from backend.services.auth_service import validate_registration
from backend.utils.security import sanitize_input

auth_bp = Blueprint('auth', __name__)


def _temporary_password(length=12):
    """A readable one-time password: no I/l/1/O/0, so a teacher can dictate it out loud."""
    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def _unique_invitation_code():
    """A short code that isn't already taken by another teacher."""
    while True:
        code = str(uuid.uuid4())[:8].upper()
        if not User.query.filter_by(invitation_code=code).first():
            return code


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate input data
    validation_result = validate_registration(data)
    if validation_result is not True:
        return jsonify({"error": validation_result}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already taken"}), 400
    
    # Experiment participation agreement: students must answer one way or the other before
    # they can register. Declining is a valid answer - the account still works, the choice is
    # just recorded so their data can be excluded at analysis time.
    experiment_consent = None
    if data['role'] == 'student':
        experiment_consent = data.get('experiment_consent')
        if experiment_consent not in (True, False):
            return jsonify({
                "error": "Please accept or decline the experiment participation agreement"
            }), 400

    # Redeem an invitation code. A code belongs to a teacher and is reusable by any number of
    # students, so redeeming it records a new row rather than consuming a pre-made one.
    invitation_code = data.get('invitation_code')
    teacher_id = None
    invitation = None

    if data['role'] == 'student' and invitation_code:
        teacher = User.query.filter_by(
            invitation_code=invitation_code, role='teacher'
        ).first()

        if teacher:
            teacher_id = teacher.id
            invitation = Invitation(code=invitation_code, teacher_id=teacher_id, is_used=True)
            db.session.add(invitation)
        else:
            # Fall back to the old single-use rows, so any code handed out before codes became
            # permanent still works for the student holding it.
            invitation = Invitation.query.filter_by(
                code=invitation_code, is_used=False
            ).first()
            if not invitation:
                return jsonify({"error": "Invalid invitation code"}), 400
            teacher_id = invitation.teacher_id
            invitation.is_used = True
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role'],
        experiment_consent=experiment_consent,
        experiment_consent_at=datetime.utcnow() if experiment_consent is not None else None
    )
    new_user.set_password(data['password'])

    db.session.add(new_user)
    db.session.flush()  # assign new_user.id before linking the invitation to it

    if invitation:
        invitation.student_id = new_user.id

    db.session.commit()
    
    # Create access and refresh tokens
    access_token = create_access_token(identity=new_user.id)
    refresh_token = create_refresh_token(identity=new_user.id)
    
    return jsonify({
        "message": "Registration successful",
        "user": new_user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    # Validate required fields (also guards data being None for a missing/non-JSON body -
    # the old code called data.get(...) for a debug print before this check ever ran)
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    # Find user by email
    user = User.query.filter_by(email=data['email']).first()

    # Check if user exists and password is correct
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid email or password"}), 401

    # Create access and refresh tokens - convert ID to string
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=str(current_user_id))

    return jsonify({
        "access_token": access_token
    }), 200

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    return jsonify(user.to_dict()), 200

@auth_bp.route('/generate-invitation', methods=['POST'])
@jwt_required()
def generate_invitation():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only teachers can generate invitations
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can generate invitation codes"}), 403

    # A teacher has exactly one code, reusable by any number of students: hand back the
    # existing one, and only mint it the first time it's asked for.
    if not user.invitation_code:
        user.invitation_code = _unique_invitation_code()
        db.session.commit()

    return jsonify({
        "message": "Invitation code retrieved successfully",
        "code": user.invitation_code
    }), 200

@auth_bp.route('/regenerate-invitation', methods=['POST'])
@jwt_required()
def regenerate_invitation():
    """Replace a teacher's invitation code, so a leaked one stops working."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can regenerate invitation codes"}), 403

    user.invitation_code = _unique_invitation_code()

    # Retire any leftover single-use rows from before codes became permanent. Without this a
    # retired code could still be redeemed through register()'s legacy fallback, which would
    # defeat the point of rotating. student_id stays NULL on these, so they never show up in
    # the teacher's roster (that join is on student_id).
    Invitation.query.filter_by(teacher_id=user.id, is_used=False).update({'is_used': True})

    db.session.commit()

    return jsonify({
        "message": "Invitation code regenerated - the previous code no longer works",
        "code": user.invitation_code
    }), 200

@auth_bp.route('/students/<int:student_id>/reset-password', methods=['POST'])
@jwt_required()
def reset_student_password(student_id):
    """Teacher-initiated password reset - the recovery path for a student who forgot theirs.

    Deliberately NOT a backdoor: there's no master password and no way to read an existing
    one (they're hashed). A teacher can only reset a student in their own class, and the
    temporary password is returned once, in this response, for them to hand over in person.
    It is never logged or emailed.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can reset student passwords"}), 403

    # Same definition of "my students" used everywhere else in the app.
    from backend.services import stats_service
    if student_id not in {s.id for s in stats_service._get_teacher_students(current_user_id)}:
        return jsonify({"error": "This student is not one of yours"}), 403

    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({"error": "That account is not a student"}), 400

    temporary_password = _temporary_password()
    student.set_password(temporary_password)
    db.session.commit()

    return jsonify({
        "message": f"Password reset for {student.username}. Give them this temporary password "
                   f"and ask them to change it after signing in.",
        "username": student.username,
        "temporary_password": temporary_password
    }), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Any signed-in user changing their own password, current password required."""
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    data = request.get_json() or {}
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"error": "Current and new password are required"}), 400

    if not user.check_password(current_password):
        # 400, deliberately not 401: the caller IS authenticated, they just mistyped the old
        # password. A 401 here means "your session expired" to every HTTP client, and ours acted
        # on it by clearing the token and redirecting to /login mid-dialog.
        return jsonify({"error": "Current password is incorrect"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters long"}), 400

    if new_password == current_password:
        return jsonify({"error": "New password must be different from the current one"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Everything the profile page shows that isn't already in the auth state.

    For a teacher: their invitation code and their students (each with the id the statistics
    page needs). For a student: who they are attached to - the teacher whose invitation code
    they signed up with.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    profile = {'user': user.to_dict()}

    if user.role == 'teacher':
        # Same definition of "my students" as everywhere else in the app. Imported here rather
        # than at module scope, matching reset_student_password below.
        from backend.services import stats_service
        students = stats_service._get_teacher_students(current_user_id)
        profile['invitation_code'] = user.invitation_code
        profile['students'] = sorted(
            (s.to_dict() for s in students), key=lambda s: (s.get('username') or '').lower()
        )
    else:
        # The teacher whose code this student redeemed. A student who was only ever assigned a
        # task (no code) has no such link, so this is allowed to be absent.
        invitation = Invitation.query.filter_by(
            student_id=current_user_id, is_used=True
        ).order_by(Invitation.id.desc()).first()
        teacher = User.query.get(invitation.teacher_id) if invitation else None
        profile['teacher'] = {
            'username': teacher.username,
            'email': teacher.email
        } if teacher else None

    return jsonify(profile), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """A student filling in their own background from the profile page.

    Every field is optional and independently updatable: only the keys actually present in the
    request are touched, and an explicit null clears one. Nothing here affects access to the
    app - it exists so the study's results can be interpreted - so the validation is about
    keeping the values groupable, not about forcing anyone to answer.
    """
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)

    if user.role != 'student':
        return jsonify({"error": "Only students have a background profile"}), 403

    data = request.get_json() or {}

    if 'age' in data:
        age = data.get('age')
        if age in (None, ''):
            user.age = None
        else:
            try:
                age = int(age)
            except (TypeError, ValueError):
                return jsonify({"error": "Age must be a whole number"}), 400
            if age < 5 or age > 120:
                return jsonify({"error": "Age must be between 5 and 120"}), 400
            user.age = age

    for field, limit in (('gender', 32), ('native_language', 64), ('english_level', 32)):
        if field in data:
            value = data.get(field)
            if value in (None, ''):
                setattr(user, field, None)
                continue
            value = sanitize_input(str(value)).strip()
            if len(value) > limit:
                return jsonify({"error": f"{field.replace('_', ' ').capitalize()} is too long"}), 400
            setattr(user, field, value)

    db.session.commit()

    return jsonify({
        "message": "Profile updated",
        "user": user.to_dict()
    }), 200


@auth_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    current_user_id = int(get_jwt_identity())
    user = User.query.get_or_404(current_user_id)
    
    # Only teachers can access this
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can access this endpoint"}), 403
    
    # Get students who were invited by this teacher or assigned to this teacher's tasks
    # Method 1: Students who used this teacher's invitation codes
    invited_students = db.session.query(User).join(
        Invitation, Invitation.student_id == User.id
    ).filter(
        Invitation.teacher_id == current_user_id,
        Invitation.is_used == True,
        User.role == 'student'
    ).all()
    
    # Method 2: Students who have assignments from this teacher's tasks
    assigned_students = db.session.query(User).join(TaskAssignment).join(Task).filter(
        Task.creator_id == current_user_id,
        User.role == 'student'
    ).all()
    
    # Combine and remove duplicates
    all_students = list(set(invited_students + assigned_students))
    
    return jsonify({
        "students": [student.to_dict() for student in all_students]
    }), 200