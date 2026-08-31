# backend/models/activity_session.py
from datetime import datetime
from . import db

# How often the frontend is expected to send a heartbeat. Any gap between heartbeats longer
# than this (tab backgrounded, laptop asleep, network hiccup) is capped at this value so it
# doesn't get counted as active time.
HEARTBEAT_INTERVAL_SECONDS = 20
HEARTBEAT_CAP_SECONDS = HEARTBEAT_INTERVAL_SECONDS * 3


class ActivitySession(db.Model):
    """Tracks active time a student spends on a task submission or practice session.

    One open (closed_at IS NULL) session per (student, activity_type, target_id) at a time.
    The frontend pings /api/activity/heartbeat roughly every HEARTBEAT_INTERVAL_SECONDS while
    the page is visible; each heartbeat adds the (capped) elapsed time since the last one.
    """
    __tablename__ = 'activity_sessions'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(20), nullable=False)  # 'task' | 'exercise' (a practice session)
    target_id = db.Column(db.Integer, nullable=False)  # task_id or practice_session id
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_heartbeat_at = db.Column(db.DateTime, default=datetime.utcnow)
    active_seconds = db.Column(db.Float, default=0.0)
    closed_at = db.Column(db.DateTime)

    student = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'activity_type': self.activity_type,
            'target_id': self.target_id,
            'active_seconds': self.active_seconds,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None
        }


def record_heartbeat(student_id, activity_type, target_id):
    """Create-or-continue the open session for this student+activity, return it."""
    now = datetime.utcnow()
    session = ActivitySession.query.filter_by(
        student_id=student_id,
        activity_type=activity_type,
        target_id=target_id,
        closed_at=None
    ).order_by(ActivitySession.id.desc()).first()

    if session is None:
        session = ActivitySession(
            student_id=student_id,
            activity_type=activity_type,
            target_id=target_id,
            started_at=now,
            last_heartbeat_at=now,
            active_seconds=0.0
        )
        db.session.add(session)
    else:
        delta = (now - session.last_heartbeat_at).total_seconds()
        delta = max(0.0, min(delta, HEARTBEAT_CAP_SECONDS))
        session.active_seconds = (session.active_seconds or 0.0) + delta
        session.last_heartbeat_at = now

    return session


def close_open_session(student_id, activity_type, target_id):
    """Close the open session for this student+activity (called on final submit), return the
    active_seconds recorded, or None if no session was ever started (e.g. direct API use)."""
    session = ActivitySession.query.filter_by(
        student_id=student_id,
        activity_type=activity_type,
        target_id=target_id,
        closed_at=None
    ).order_by(ActivitySession.id.desc()).first()

    if session is None:
        return None

    session.closed_at = datetime.utcnow()
    return session.active_seconds
