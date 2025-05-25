# services/auth_service.py
import re

def validate_registration(data):
    # Check required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if field not in data:
            return f"{field} is required"
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, data['email']):
        return "Invalid email format"
    
    # Validate username (3-20 alphanumeric chars and underscore)
    username_pattern = r'^[a-zA-Z0-9_]{3,20}$'
    if not re.match(username_pattern, data['username']):
        return "Username must be 3-20 characters long and contain only letters, numbers, and underscores"
    
    # Validate password strength (at least 8 chars)
    if len(data['password']) < 8:
        return "Password must be at least 8 characters long"
    
    # Validate role
    valid_roles = ['teacher', 'student']
    if data['role'] not in valid_roles:
        return "Role must be either 'teacher' or 'student'"
    
    # If all validations pass
    return True