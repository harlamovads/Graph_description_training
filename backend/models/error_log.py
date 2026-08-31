# backend/models/error_log.py
from datetime import datetime
from . import db


class ErrorLog(db.Model):
    """One row per ERRANT-typed edit found between a student's text and its correction.

    Populated from task submissions (source_type='submission') and practice sessions
    (source_type='practice_session'). This is the source of truth for "how many errors,
    of what ERRANT type, did a student make" — both for the per-submission view and the
    teacher stats dashboard. The two source types are kept separate everywhere they're
    aggregated (see backend/services/stats_service.py), rather than merged into one total.
    """
    __tablename__ = 'error_logs'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_type = db.Column(db.String(20), nullable=False)  # 'submission' | 'practice_session'
    source_id = db.Column(db.Integer, nullable=False)  # submissions.id or practice_sessions.id
    sentence_index = db.Column(db.Integer)
    errant_type = db.Column(db.String(40), nullable=False)
    original_text = db.Column(db.Text)
    corrected_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'sentence_index': self.sentence_index,
            'errant_type': self.errant_type,
            'original_text': self.original_text,
            'corrected_text': self.corrected_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def log_edits(student_id, source_type, source_id, edits_by_sentence):
    """Persist ERRANT edits as ErrorLog rows.

    :param edits_by_sentence: list of (sentence_index, edits) tuples, where each edit is a
        dict with 'errant_type', 'original_text'/'original', 'corrected_text'/'corrected'.
    """
    rows = []
    for sentence_index, edits in edits_by_sentence:
        for edit in edits:
            rows.append(ErrorLog(
                student_id=student_id,
                source_type=source_type,
                source_id=source_id,
                sentence_index=sentence_index,
                errant_type=edit.get('errant_type', 'OTHER'),
                original_text=edit.get('original_text', edit.get('original', '')),
                corrected_text=edit.get('corrected_text', edit.get('corrected', ''))
            ))
    if rows:
        db.session.add_all(rows)
    return rows


def clear_logs_for_source(source_type, source_id):
    """Delete previously logged edits for a source, e.g. before re-logging after a teacher edit."""
    ErrorLog.query.filter_by(source_type=source_type, source_id=source_id).delete()
