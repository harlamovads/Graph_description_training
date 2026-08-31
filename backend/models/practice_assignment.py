# backend/models/practice_assignment.py
"""A teacher's flag that a specific sentence (from a submission they reviewed) should be
practiced. Deliberately separate from PracticeSession itself: assigning one doesn't create a
session - the session is only created lazily, the first time the student actually starts it
(see practice_service.start_session, which stamps practice_session_id here once that happens).
Until then this is just a pending marker shown on the student's dashboard, alongside their
assigned tasks.
"""
from datetime import datetime
from . import db


class PracticeAssignment(db.Model):
    __tablename__ = 'practice_assignments'

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    sentence_index = db.Column(db.Integer, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    practice_session_id = db.Column(db.Integer, db.ForeignKey('practice_sessions.id'), nullable=True)

    teacher = db.relationship('User', foreign_keys=[teacher_id])
    student = db.relationship('User', foreign_keys=[student_id])
    submission = db.relationship('Submission')

    def to_dict(self):
        sentence = None
        task_title = None
        analysis = self.submission.get_analysis_result() if self.submission else None
        if analysis:
            sentence = next(
                (s for s in analysis.get('sentences', []) if s['id'] == self.sentence_index),
                None
            )
        if self.submission and self.submission.assignment and self.submission.assignment.task:
            task_title = self.submission.assignment.task.title

        return {
            'id': self.id,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'submission_id': self.submission_id,
            'sentence_index': self.sentence_index,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'practice_session_id': self.practice_session_id,
            'task_title': task_title,
            'sentence_original': sentence['original'] if sentence else None,
            'sentence_corrected': (sentence.get('teacher_corrected') or sentence.get('corrected')) if sentence else None
        }
