# routes/auth.py
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from backend.models.task import Task, TaskAssignment
from backend.models import db
from backend.models.user import User, Invitation
import uuid
from backend.services.auth_service import validate_registration

auth_bp = Blueprint('auth', __name__)

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
    
    # Process invitation code for students
    invitation_code = data.get('invitation_code')
    teacher_id = None
    
    if data['role'] == 'student' and invitation_code:
        invitation = Invitation.query.filter_by(code=invitation_code, is_used=False).first()
        if invitation:
            teacher_id = invitation.teacher_id
            invitation.is_used = True
        else:
            return jsonify({"error": "Invalid invitation code"}), 400
    
    # Create new user
    new_user = User(
        username=data['username'],
        email=data['email'],
        role=data['role']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
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
    
    # Debug info
    print(f"Login attempt for: {data.get('email')}")
    
    # Validate required fields
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    
    # Debug info
    if not user:
        print(f"User not found: {data.get('email')}")
    else:
        print(f"User found: {user.username}, checking password")
    
    # Check if user exists and password is correct
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Create access and refresh tokens - convert ID to string
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    print(f"Login successful for: {user.email}, Role: {user.role}")
    print(f"Generated access token: {access_token[:20]}...")
    
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
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        "access_token": access_token
    }), 200

@auth_bp.route('/user', methods=['GET'])
@jwt_required()
def get_user():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    return jsonify(user.to_dict()), 200

@auth_bp.route('/generate-invitation', methods=['POST'])
@jwt_required()
def generate_invitation():
    current_user_id = get_jwt_identity()
    user = User.query.get_or_404(int(current_user_id))
    
    # Only teachers can generate invitations
    if user.role != 'teacher':
        return jsonify({"error": "Only teachers can generate invitation codes"}), 403
    
    # Generate a unique invitation code
    code = str(uuid.uuid4())[:8].upper()
    
    # Create a new invitation
    invitation = Invitation(
        code=code,
        teacher_id=user.id
    )
    
    db.session.add(invitation)
    db.session.commit()
    
    return jsonify({
        "message": "Invitation code generated successfully",
        "code": code
    }), 201

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
    invited_students = db.session.query(User).join(Invitation).filter(
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