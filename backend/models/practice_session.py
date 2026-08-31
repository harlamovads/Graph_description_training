# backend/models/practice_session.py
"""A guided, per-sentence practice loop a student can start from any errored sentence in one
of their submissions (see backend/services/practice_service.py for the state machine).

Replaces the old teacher-authored, corpus-backed Exercise/ExerciseAttempt system: instead of a
teacher curating sentences from a corpus, the student drills the exact errors the neural
network (or a teacher's edit) found in their own writing.
"""
from datetime import datetime
import json
from . import db


class PracticeSession(db.Model):
    __tablename__ = 'practice_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    sentence_index = db.Column(db.Integer, nullable=False)  # the sentence's `id` within
                                                              # submission.analysis_result['sentences']

    status = db.Column(db.String(20), nullable=False, default='in_progress')  # in_progress | completed | stopped
    current_step = db.Column(db.String(20), nullable=False, default='rewrite_original')  # rewrite_original | practice_item | done

    original_sentence = db.Column(db.Text, nullable=False)
    target_corrected = db.Column(db.Text, nullable=False)  # fixed target for the rewrite_original round
    round_target = db.Column(db.Text)  # fixed target for the CURRENT practice_item round; null
                                        # until that round's first submission establishes it

    queue = db.Column(db.Text)          # JSON list (FIFO) of items still to practice
    current_item = db.Column(db.Text)   # JSON of the item popped from the front, or null
    history = db.Column(db.Text)        # JSON list of round records, for teacher review

    sentences_completed = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    time_spent_seconds = db.Column(db.Float)

    student = db.relationship('User')
    submission = db.relationship('Submission')

    def get_queue(self):
        return json.loads(self.queue) if self.queue else []

    def set_queue(self, items):
        self.queue = json.dumps(items)

    def get_current_item(self):
        return json.loads(self.current_item) if self.current_item else None

    def set_current_item(self, item):
        self.current_item = json.dumps(item) if item is not None else None

    def get_history(self):
        return json.loads(self.history) if self.history else []

    def set_history(self, entries):
        self.history = json.dumps(entries)

    def append_history(self, entry):
        entries = self.get_history()
        entries.append(entry)
        self.set_history(entries)

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'submission_id': self.submission_id,
            'sentence_index': self.sentence_index,
            'status': self.status,
            'current_step': self.current_step,
            'original_sentence': self.original_sentence,
            'target_corrected': self.target_corrected,
            'current_item': self.get_current_item(),
            'queue_length': len(self.get_queue()),
            'sentences_completed': self.sentences_completed,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'time_spent_seconds': self.time_spent_seconds
        }

    def to_review_dict(self):
        d = self.to_dict()
        d['history'] = self.get_history()
        return d
