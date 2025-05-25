from datetime import datetime
import json
from . import db

class Submission(db.Model):
    __tablename__ = 'submissions'
   
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('task_assignments.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    analysis_result = db.Column(db.Text)  # JSON string with error detection results
    teacher_feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, etc.
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    analysis_html = db.Column(db.Text)  # Added this field
   
    def get_analysis_result(self):
        if self.analysis_result:
            return json.loads(self.analysis_result)
        return None
   
    def set_analysis_result(self, result):
        self.analysis_result = json.dumps(result)
   
    def to_dict(self):
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'exercise_id': self.exercise_id,
            'content': self.content,
            'analysis_result': self.get_analysis_result(),
            'teacher_feedback': self.teacher_feedback,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }