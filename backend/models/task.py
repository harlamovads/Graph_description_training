# models/task.py
from datetime import datetime
from . import db

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255), nullable=False)  # Changed to be required
    is_from_database = db.Column(db.Boolean, default=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assignments = db.relationship('TaskAssignment', backref='task', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'image_url': self.image_url,
            'is_from_database': self.is_from_database,
            'creator_id': self.creator_id,
            'created_at': self.created_at.isoformat()
        }


class TaskAssignment(db.Model):
    __tablename__ = 'task_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.DateTime)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    submission = db.relationship('Submission', backref='assignment', uselist=False)