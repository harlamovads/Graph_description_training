# backend/services/stats_service.py
"""Aggregation queries backing the teacher stats dashboard: per-student time spent, task
scores, practice-session activity, and error-type distribution (task errors and practice-session
errors kept separate, per the source_type split in ErrorLog)."""
from collections import defaultdict
from backend.models import db
from backend.models.user import User, Invitation
from backend.models.task import Task, TaskAssignment
from backend.models.submission import Submission
from backend.models.practice_session import PracticeSession
from backend.models.error_log import ErrorLog


def _get_teacher_students(teacher_id):
    """Students belonging to a teacher: invited via one of their codes, or assigned one of
    their tasks. Mirrors routes/auth.py::get_students so "the teacher's students" means the
    same thing everywhere in the app."""
    invited = db.session.query(User).join(
        Invitation, Invitation.student_id == User.id
    ).filter(
        Invitation.teacher_id == teacher_id,
        Invitation.is_used == True,
        User.role == 'student'
    ).all()
    assigned = db.session.query(User).join(TaskAssignment).join(Task).filter(
        Task.creator_id == teacher_id,
        User.role == 'student'
    ).all()
    by_id = {s.id: s for s in invited + assigned}
    return list(by_id.values())


def student_summary(student):
    submissions = Submission.query.filter_by(student_id=student.id).all()
    sessions = PracticeSession.query.filter_by(student_id=student.id).all()
    assigned_count = TaskAssignment.query.filter_by(student_id=student.id).count()

    scored = [s.score for s in submissions if s.score is not None]
    avg_score = (sum(scored) / len(scored)) if scored else None
    total_time = sum((s.time_spent_seconds or 0) for s in submissions) + \
        sum((s.time_spent_seconds or 0) for s in sessions)
    total_errors = ErrorLog.query.filter_by(student_id=student.id, source_type='submission').count()

    return {
        'student': student.to_dict(),
        'tasks_completed': len(submissions),
        'tasks_assigned': assigned_count,
        'average_score': avg_score,
        'practice_sessions_completed': len([s for s in sessions if s.status == 'completed']),
        'practice_sessions_total': len(sessions),
        'total_time_spent_seconds': total_time,
        'total_errors': total_errors
    }


def teacher_students_summary(teacher_id):
    return [student_summary(s) for s in _get_teacher_students(teacher_id)]


def student_detail(teacher_id, student_id):
    """Detailed stats for one of the teacher's students, or None if that student isn't theirs."""
    student = next((s for s in _get_teacher_students(teacher_id) if s.id == student_id), None)
    if not student:
        return None

    submissions = Submission.query.filter_by(student_id=student_id).all()
    sessions = PracticeSession.query.filter_by(student_id=student_id).all()
    submission_error_rows = ErrorLog.query.filter_by(
        student_id=student_id, source_type='submission'
    ).all()
    practice_error_rows = ErrorLog.query.filter_by(
        student_id=student_id, source_type='practice_session'
    ).all()

    # Task errors indexed by submission id, for the monthly breakdown below.
    errors_by_submission = defaultdict(list)
    for row in submission_error_rows:
        errors_by_submission[row.source_id].append(row)

    time_per_task = []
    monthly = defaultdict(lambda: {
        'submissions_count': 0, 'total_time_spent_seconds': 0.0,
        'scores': [], 'total_errors': 0, 'error_distribution': defaultdict(int)
    })
    for s in submissions:
        assignment = TaskAssignment.query.get(s.assignment_id)
        task = assignment.task if assignment else None
        time_per_task.append({
            'task_id': task.id if task else None,
            'task_title': task.title if task else 'Unknown task',
            'submission_id': s.id,
            'attempt_number': s.attempt_number,
            'is_resubmission': s.attempt_number > 1,
            'score': s.score,
            'time_spent_seconds': s.time_spent_seconds,
            'submitted_at': s.submitted_at.isoformat() if s.submitted_at else None
        })

        month = s.submitted_at.strftime('%Y-%m') if s.submitted_at else 'unknown'
        bucket = monthly[month]
        bucket['submissions_count'] += 1
        bucket['total_time_spent_seconds'] += (s.time_spent_seconds or 0)
        if s.score is not None:
            bucket['scores'].append(s.score)
        for row in errors_by_submission.get(s.id, []):
            bucket['total_errors'] += 1
            bucket['error_distribution'][row.errant_type] += 1

    monthly_task_stats = []
    for month in sorted(monthly.keys()):
        b = monthly[month]
        monthly_task_stats.append({
            'month': month,
            'submissions_count': b['submissions_count'],
            'total_time_spent_seconds': b['total_time_spent_seconds'],
            'average_score': (sum(b['scores']) / len(b['scores'])) if b['scores'] else None,
            'total_errors': b['total_errors'],
            'error_distribution': dict(b['error_distribution'])
        })

    practice_sessions_list = []
    for session in sessions:
        # A session the student started from their own sentence has no submission behind it.
        # It used to be reported as "Unknown task", which read like a data error rather than
        # what it is - so say where it came from instead.
        submission = (Submission.query.get(session.submission_id)
                      if session.submission_id is not None else None)
        assignment = TaskAssignment.query.get(submission.assignment_id) if submission else None
        task = assignment.task if assignment else None
        is_manual = session.submission_id is None
        practice_sessions_list.append({
            'id': session.id,
            'source': 'manual' if is_manual else 'submission',
            'original_sentence': session.original_sentence,
            'task_title': None if is_manual else (task.title if task else 'Unknown task'),
            'sentence_index': session.sentence_index,
            'status': session.status,
            'sentences_completed': session.sentences_completed,
            'time_spent_seconds': session.time_spent_seconds,
            'started_at': session.started_at.isoformat() if session.started_at else None,
            'ended_at': session.ended_at.isoformat() if session.ended_at else None
        })

    practice_error_by_type = {}
    practice_monthly = defaultdict(lambda: defaultdict(int))
    for row in practice_error_rows:
        practice_error_by_type[row.errant_type] = practice_error_by_type.get(row.errant_type, 0) + 1
        month = row.created_at.strftime('%Y-%m') if row.created_at else 'unknown'
        practice_monthly[month][row.errant_type] += 1
    practice_monthly_error_distribution = {
        month: dict(counts) for month, counts in sorted(practice_monthly.items())
    }

    task_error_by_type = {}
    for row in submission_error_rows:
        task_error_by_type[row.errant_type] = task_error_by_type.get(row.errant_type, 0) + 1

    return {
        'student': student.to_dict(),
        'time_per_task': time_per_task,
        'monthly_task_stats': monthly_task_stats,
        'error_distribution': task_error_by_type,
        'total_errors': len(submission_error_rows),
        'practice_sessions': {
            'total_completed': len([s for s in sessions if s.status == 'completed']),
            'total_stopped': len([s for s in sessions if s.status == 'stopped']),
            'total_sentences_completed': sum(s.sentences_completed for s in sessions),
            # Split out because the two are different kinds of practice: one drills errors found
            # in the student's own submitted work, the other a sentence they brought themselves.
            'total_from_own_sentences': len([s for s in sessions if s.submission_id is None]),
            'total_from_submissions': len([s for s in sessions if s.submission_id is not None]),
            'total_time_spent_seconds': sum((s.time_spent_seconds or 0) for s in sessions),
            'sessions': practice_sessions_list,
            'error_distribution': practice_error_by_type,
            'monthly_error_distribution': practice_monthly_error_distribution
        }
    }
