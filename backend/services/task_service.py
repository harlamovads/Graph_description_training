# services/task_service.py
import boto3
from flask import current_app
from backend.models.task import Task, TaskAssignment

def upload_file_to_s3(file, filename):
    """
    Upload a file to an S3 bucket
    
    :param file: File to upload
    :param filename: S3 object name
    :return: S3 URL if successful, else None
    """
    # Get S3 configuration
    aws_access_key = current_app.config.get('AWS_ACCESS_KEY')
    aws_secret_key = current_app.config.get('AWS_SECRET_KEY')
    bucket_name = current_app.config.get('AWS_BUCKET_NAME')
    
    if not aws_access_key or not aws_secret_key or not bucket_name:
        return None
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        s3_client.upload_fileobj(
            file,
            bucket_name,
            filename,
            ExtraArgs={'ACL': 'public-read'}
        )
        
        # Construct URL
        url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
        return url
    
    except Exception as e:
        print(f"Error uploading file to S3: {str(e)}")
        return None

def get_tasks_for_user(user):
    """
    Get tasks relevant to a user based on their role
    
    :param user: User object
    :return: List of Task objects
    """
    if user.role == 'teacher':
        # Teachers see tasks they created
        return user.tasks_created.all()
    else:  # Student
        # Students see tasks assigned to them
        assignments = TaskAssignment.query.filter_by(student_id=user.id).all()
        task_ids = [assignment.task_id for assignment in assignments]
        return Task.query.filter(Task.id.in_(task_ids)).all()