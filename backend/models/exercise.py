# models/exercise.py
from datetime import datetime
import json
from . import db

class Exercise(db.Model):
    __tablename__ = 'exercises'
   
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    sentences = db.Column(db.Text, nullable=False)  # JSON string with sentences
    image_url = db.Column(db.String(255))  # Add image URL field for graph/chart
    status = db.Column(db.String(20), default='draft')  # 'draft' or 'published'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # This establishes the one-to-many relationship correctly
    submissions = db.relationship('Submission', backref='exercise', lazy='dynamic')
   
    # Relationships
    creator = db.relationship('User')
    attempts = db.relationship('ExerciseAttempt', backref='exercise', lazy='dynamic')
    
    def get_sentences(self):
        return json.loads(self.sentences)
    
    def set_sentences(self, sentences_list):
        self.sentences = json.dumps(sentences_list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'creator_id': self.creator_id,
            'title': self.title,
            'instructions': self.instructions,
            'sentences': self.get_sentences(),
            'image_url': self.image_url,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'submissions': [submission.to_dict() for submission in self.submissions]
        }


class ExerciseAttempt(db.Model):
    __tablename__ = 'exercise_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    responses = db.Column(db.Text)  # JSON string with student responses
    analysis_result = db.Column(db.Text)  # JSON string with error detection results
    score = db.Column(db.Float)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    student = db.relationship('User')
    
    def get_responses(self):
        if self.responses:
            return json.loads(self.responses)
        return None
    
    def set_responses(self, responses_dict):
        self.responses = json.dumps(responses_dict)
    
    def get_analysis_result(self):
        if self.analysis_result:
            return json.loads(self.analysis_result)
        return None
    
    def set_analysis_result(self, result):
        self.analysis_result = json.dumps(result)