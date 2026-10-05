from datetime import datetime
import json
from . import db

class Submission(db.Model):
    __tablename__ = 'submissions'
   
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('task_assignments.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    analysis_result = db.Column(db.Text)  # JSON string with error detection results
    teacher_feedback = db.Column(db.Text)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, etc.
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    analysis_html = db.Column(db.Text)  # Added this field
    time_spent_seconds = db.Column(db.Float)  # active time from ActivitySession, if tracked

    # Resubmission after review: same assignment_id, a new row per attempt rather than an
    # update in place, so the original's time/errors/score stay intact. attempt_number=1 is
    # the original; parent_submission_id always points at that original row (never a chain).
    attempt_number = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    parent_submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=True)

    # Numeric task-evaluation score (0-10, int or float e.g. 9.5) set by the teacher on review.
    # Distinct from practice sessions, which are never scored.
    score = db.Column(db.Float, nullable=True)

    # Free-form teacher annotations on the student's text: a JSON list of
    # {id, type: 'correction'|'comment', start, end, quoted_text, content}. Offsets are
    # character positions into the PLAIN TEXT of `content` (see the frontend's htmlToPlainText -
    # both sides must derive it the same way), not into the HTML, so editing the markup of the
    # renderer can never silently shift where a teacher's note points. quoted_text is stored
    # alongside so a stale annotation can be spotted rather than mis-highlighting other words.
    teacher_annotations = db.Column(db.Text)

    def get_analysis_result(self):
        if self.analysis_result:
            return json.loads(self.analysis_result)
        return None
   
    def set_analysis_result(self, result):
        self.analysis_result = json.dumps(result)
   
    def get_teacher_annotations(self):
        if not self.teacher_annotations:
            return []
        try:
            return json.loads(self.teacher_annotations)
        except ValueError:
            return []

    def set_teacher_annotations(self, annotations):
        self.teacher_annotations = json.dumps(annotations or [])

    def to_dict(self):
        return {
            'id': self.id,
            'assignment_id': self.assignment_id,
            'student_id': self.student_id,
            'content': self.content,
            'analysis_result': self.get_analysis_result(),
            'teacher_feedback': self.teacher_feedback,
            'status': self.status,
            'submitted_at': self.submitted_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'time_spent_seconds': self.time_spent_seconds,
            'attempt_number': self.attempt_number,
            'parent_submission_id': self.parent_submission_id,
            'score': self.score,
            'teacher_annotations': self.get_teacher_annotations()
        }