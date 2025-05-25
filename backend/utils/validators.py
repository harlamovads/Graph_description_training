# utils/validators.py
import re
from datetime import datetime

def validate_email(email):
    """
    Validate email format
    
    :param email: Email to validate
    :return: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password):
    """
    Validate password strength
    
    :param password: Password to validate
    :return: (is_valid, message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for at least one uppercase letter, one lowercase letter, and one digit
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is valid"

def validate_date_format(date_str, format='%Y-%m-%d'):
    """
    Validate date format
    
    :param date_str: Date string to validate
    :param format: Expected date format
    :return: True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False

def validate_user_input(data, required_fields=None, max_lengths=None):
    """
    Validate user input data
    
    :param data: Data to validate
    :param required_fields: List of required fields
    :param max_lengths: Dict of field names and max lengths
    :return: (is_valid, errors)
    """
    errors = {}
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data or not data[field]:
                errors[field] = f"{field} is required"
    
    # Check max lengths
    if max_lengths:
        for field, max_length in max_lengths.items():
            if field in data and data[field] and len(str(data[field])) > max_length:
                errors[field] = f"{field} cannot be longer than {max_length} characters"
    
    return len(errors) == 0, errors

def validate_file_type(filename, allowed_extensions):
    """
    Validate file type based on extension
    
    :param filename: Filename to validate
    :param allowed_extensions: List of allowed extensions
    :return: True if valid, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions