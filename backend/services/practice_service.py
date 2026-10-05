# backend/services/practice_service.py
"""State machine behind a practice session (backend/models/practice_session.py) - a guided
rewrite-then-generate loop the student works through for one errored sentence at a time.

Two round types share one submit-until-clean shape:
  - 'rewrite_original': rewrite the flagged sentence, applying every suggested correction, until
    it matches the already-known target (the submission's own NN/teacher correction).
  - 'practice_item': write a brand-new sentence featuring one specific corrected span (or, for a
    removed span, matching the KWIC context around where it used to be), until that new sentence
    is itself error-free. Any errors it turns up get queued (FIFO) for further rounds.
"""
from datetime import datetime
from backend.models import db
from backend.models.submission import Submission
from backend.models.practice_session import PracticeSession
from backend.models.practice_assignment import PracticeAssignment
from backend.models.error_log import log_edits
from backend.models.activity_session import close_open_session
from backend.services import errant_service, deepseek_service
from backend.services.neural_network_service import analyze_and_diff
from backend.services.load_manager import manager as load_manager, AtCapacity


# Caps for a student-typed practice sentence. Generous enough for any real sentence, small
# enough that the field can't be used to store an essay.
MAX_MANUAL_SENTENCE_CHARS = 500
MAX_MANUAL_MARKS = 20


class PracticeError(Exception):
    """Raised for user-facing 4xx conditions (routes/practice.py turns these into responses)."""
    def __init__(self, message, status_code=400, retry_after=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        # Set for 503s so the route can send a Retry-After and the client can back off.
        self.retry_after = retry_after


def _get_sentence(submission, sentence_index):
    analysis = submission.get_analysis_result() or {}
    sentence = next(
        (s for s in analysis.get('sentences', []) if s['id'] == sentence_index),
        None
    )
    if not sentence:
        raise PracticeError("Sentence not found in this submission's analysis", 404)
    return sentence


def _queue_item_from_edit(edit, corrected_text):
    item = {
        'errant_type': edit.get('errant_type', 'OTHER'),
        'category': edit.get('category', 'OTHER'),
        'original_text': edit.get('original_text', ''),
        'corrected_text': edit.get('corrected_text', ''),
        'kwic_before': None,
        'kwic_after': None
    }
    is_deletion = item['category'] == 'U' or not item['corrected_text']
    if is_deletion:
        char_pos = edit.get('corrected_start_char', 0)
        kwic = errant_service.kwic_context(corrected_text, char_pos, num_words=2)
        item['kwic_before'] = kwic['before']
        item['kwic_after'] = kwic['after']
    return item


def _prompt_for_item(item):
    if item['corrected_text']:
        return f'Now create a similar sentence with "{item["corrected_text"]}" in it.'
    before = item.get('kwic_before') or ''
    after = item.get('kwic_after') or ''
    context = f'"...{before} … {after}..."' if (before or after) else 'a similar sentence'
    original = item.get('original_text') or ''
    return (
        f'Now create a sentence with a similar structure to {context} '
        f'- without adding back "{original}".'
    )


def _advance_from_queue(session):
    """Pop the next queue item into current_item, or mark the session completed if empty."""
    queue = session.get_queue()
    if queue:
        item = queue.pop(0)
        # Example sentences to show alongside the prompt. Both round types get them, but they
        # have to be asked for differently: an item with a target span needs examples USING that
        # span, while a deletion item needs examples that keep the structure around the gap and
        # leave the removed words out. Deletion rounds used to get [] here, which is why they
        # showed no examples at all. Degrades to [] with no key configured / on any failure.
        if item.get('corrected_text'):
            item['examples'] = deepseek_service.generate_similar_sentences(
                session.target_corrected, item['corrected_text'])
        else:
            item['examples'] = deepseek_service.generate_structure_examples(
                session.target_corrected,
                item.get('kwic_before') or '',
                item.get('kwic_after') or '',
                item.get('original_text') or ''
            )
        session.set_current_item(item)
        session.set_queue(queue)
        session.current_step = 'practice_item'
    else:
        session.set_current_item(None)
        session.current_step = 'done'
        session.status = 'completed'
        session.ended_at = datetime.utcnow()
        session.time_spent_seconds = close_open_session(session.student_id, 'exercise', session.id)


def start_session(student_id, submission_id, sentence_index):
    submission = Submission.query.get(submission_id)
    if not submission or submission.student_id != student_id:
        raise PracticeError("You don't have access to this submission", 403)

    sentence = _get_sentence(submission, sentence_index)
    edits = sentence.get('errant_edits') or []
    if not edits:
        raise PracticeError("This sentence has no errors to practice", 400)

    existing = PracticeSession.query.filter_by(
        student_id=student_id,
        submission_id=submission_id,
        sentence_index=sentence_index,
        status='in_progress'
    ).order_by(PracticeSession.id.desc()).first()
    if existing:
        _link_assignment(existing)
        db.session.commit()
        return existing

    target_corrected = sentence.get('teacher_corrected') or sentence['corrected']

    session = PracticeSession(
        student_id=student_id,
        submission_id=submission_id,
        sentence_index=sentence_index,
        original_sentence=sentence['original'],
        target_corrected=target_corrected,
        status='in_progress',
        current_step='rewrite_original',
        sentences_completed=0
    )
    session.set_queue([_queue_item_from_edit(e, target_corrected) for e in edits])
    session.set_current_item(None)
    session.set_history([])

    db.session.add(session)
    db.session.flush()  # assign session.id before logging/linking

    log_edits(student_id, 'practice_session', session.id, [(0, edits)])
    _link_assignment(session)

    db.session.commit()
    return session


def start_manual_session(student_id, sentence, marks):
    """Start a practice session from a sentence the student typed and marked up themselves.

    The student supplies both the error spans and what each should say, so THEY define the
    target - the neural network is not consulted. That is deliberate: this mode exists for
    practising a correction the student already knows about (one a teacher gave them on paper,
    say), and second-guessing it with the model would defeat the point.

    The target sentence is rebuilt by applying their corrections, and then diffed with ERRANT
    exactly as a submission's sentence is. Everything downstream - the rewrite round, the queue
    of "create a sentence with X in it" rounds, KWIC context for deletions, the error-type
    logging behind the statistics - therefore works identically and needs no special case.
    """
    sentence = (sentence or '').strip()
    if not sentence:
        raise PracticeError("Please write a sentence first", 400)
    if len(sentence) > MAX_MANUAL_SENTENCE_CHARS:
        raise PracticeError(
            f"That sentence is too long (limit {MAX_MANUAL_SENTENCE_CHARS} characters)", 400)

    if not marks:
        raise PracticeError("Mark at least one error in the sentence", 400)
    if len(marks) > MAX_MANUAL_MARKS:
        raise PracticeError(f"That is more than {MAX_MANUAL_MARKS} marks", 400)

    cleaned = []
    for mark in marks:
        if not isinstance(mark, dict):
            raise PracticeError("Each mark must be an object", 400)
        try:
            start = int(mark.get('start'))
            end = int(mark.get('end'))
        except (TypeError, ValueError):
            raise PracticeError("Each mark needs a numeric start and end", 400)
        if start < 0 or end <= start or end > len(sentence):
            raise PracticeError("A marked span falls outside the sentence", 400)
        # An empty correction is meaningful: it means "these words should be removed", which
        # becomes a deletion round with KWIC context, the same as an NN-found deletion.
        correction = (mark.get('correction') or '').strip()
        cleaned.append({'start': start, 'end': end, 'correction': correction})

    cleaned.sort(key=lambda m: m['start'])
    for previous, nxt in zip(cleaned, cleaned[1:]):
        if nxt['start'] < previous['end']:
            raise PracticeError("Marked spans cannot overlap", 400)

    # Apply corrections from the end backwards, so each replacement leaves the offsets of the
    # ones still to come untouched.
    target = sentence
    for mark in reversed(cleaned):
        target = target[:mark['start']] + mark['correction'] + target[mark['end']:]
    target = ' '.join(target.split())

    if target == sentence:
        raise PracticeError(
            "Your corrections don't change the sentence - there would be nothing to practise",
            400)

    edits = errant_service.compute_edits(sentence, target)
    if not edits:
        # ERRANT found no alignable change even though the strings differ (punctuation-only
        # edits can do this). Fall back to the student's own marks so the session still starts
        # rather than telling them their correction doesn't count.
        edits = [{
            'errant_type': 'OTHER',
            'category': 'U' if not m['correction'] else 'R',
            'original_text': sentence[m['start']:m['end']],
            'corrected_text': m['correction'],
            'start_char': m['start'],
            'end_char': m['end'],
            'corrected_start_char': m['start'],
            'corrected_end_char': m['start'] + len(m['correction'])
        } for m in cleaned]

    session = PracticeSession(
        student_id=student_id,
        submission_id=None,
        sentence_index=None,
        original_sentence=sentence,
        target_corrected=target,
        status='in_progress',
        current_step='rewrite_original',
        sentences_completed=0
    )
    session.set_queue([_queue_item_from_edit(e, target) for e in edits])
    session.set_current_item(None)
    session.set_history([])

    db.session.add(session)
    db.session.flush()

    log_edits(student_id, 'practice_session', session.id, [(0, edits)])
    # No _link_assignment: a teacher assigns practice on a submission's sentence, and this
    # sentence is the student's own.

    db.session.commit()
    return session


def _link_assignment(session):
    """If this (submission, sentence) had an open teacher assignment, mark it entered."""
    assignment = PracticeAssignment.query.filter_by(
        student_id=session.student_id,
        submission_id=session.submission_id,
        sentence_index=session.sentence_index,
        practice_session_id=None
    ).first()
    if assignment:
        assignment.practice_session_id = session.id


def get_owned_session(student_id, session_id):
    session = PracticeSession.query.get(session_id)
    if not session or session.student_id != student_id:
        raise PracticeError("You don't have access to this practice session", 403)
    return session


def submit_round(session, text):
    if session.status != 'in_progress':
        raise PracticeError("This practice session has already ended", 400)

    text = (text or '').strip()
    if not text:
        raise PracticeError("Please enter some text", 400)

    round_index = len(session.get_history())

    if session.current_step == 'rewrite_original':
        target = session.target_corrected
        edits = errant_service.compute_edits(text, target)
        resolved = not edits
        session.append_history({
            'round_index': round_index, 'step_type': 'rewrite_original',
            'prompt': 'Rewrite the sentence, applying the suggested corrections.',
            'submitted_text': text, 'target': target, 'edits': edits, 'resolved': resolved
        })
        if resolved:
            session.sentences_completed += 1
            _advance_from_queue(session)
        db.session.commit()
        return {'resolved': resolved, 'edits': edits, 'target': target, 'session': session,
                'step_type': 'rewrite_original'}

    if session.current_step == 'practice_item':
        item = session.get_current_item()
        if not item:
            raise PracticeError("No active practice item", 400)

        if not session.round_target:
            # First submission of this round: analyze the student's freshly-written sentence
            # through the same analyze-then-diff path a submission's own sentences use, and fix
            # this round's target from it. Any errors found here are new - queue them (FIFO,
            # to the back) and log them now, once, regardless of how many retries follow.
            # One sentence, but the same expensive model as a submission, so it queues through
            # the same admission control (backend/services/load_manager.py). Taking the slot
            # around this call only - not the whole round - keeps retries of an already-analysed
            # round (which are pure string diffs) instant even while the server is busy.
            try:
                with load_manager.slot('practice'):
                    result = analyze_and_diff(text)
            except AtCapacity as busy:
                raise PracticeError(busy.message, 503, retry_after=busy.retry_after)
            target = result['corrected']
            edits = result['errant_edits']
            session.round_target = target
            if edits:
                queue = session.get_queue()
                queue.extend(_queue_item_from_edit(e, target) for e in edits)
                session.set_queue(queue)
                log_edits(session.student_id, 'practice_session', session.id, [(round_index, edits)])
        else:
            target = session.round_target
            edits = errant_service.compute_edits(text, target)

        resolved = not edits
        session.append_history({
            'round_index': round_index, 'step_type': 'practice_item',
            'prompt': _prompt_for_item(item),
            'submitted_text': text, 'target': target, 'edits': edits, 'resolved': resolved
        })
        if resolved:
            session.round_target = None
            session.sentences_completed += 1
            _advance_from_queue(session)
        db.session.commit()
        # The step type is reported from the round that was just submitted, NOT from
        # session.current_step - a resolved round has already advanced the session by this point.
        return {'resolved': resolved, 'edits': edits, 'target': target, 'session': session,
                'step_type': 'practice_item'}

    raise PracticeError("This practice session has already ended", 400)


def stop_session(session):
    if session.status == 'in_progress':
        session.status = 'stopped'
        session.ended_at = datetime.utcnow()
        session.time_spent_seconds = close_open_session(session.student_id, 'exercise', session.id)
        db.session.commit()
    return session


def current_prompt(session):
    """The prompt text for whatever step the session is currently on, or None if done."""
    if session.current_step == 'rewrite_original':
        return 'Rewrite the sentence, applying the suggested corrections shown above.'
    if session.current_step == 'practice_item':
        item = session.get_current_item()
        return _prompt_for_item(item) if item else None
    return None


def session_state(session):
    """The full state payload the frontend renders from - session.to_dict() plus the current
    prompt and, for the rewrite_original round, the highlighted-span edits (recomputed as a
    plain diff, no NN call - the same computation start_session used to seed the queue)."""
    state = session.to_dict()
    state['prompt'] = current_prompt(session)
    if session.current_step == 'rewrite_original':
        state['initial_edits'] = errant_service.compute_edits(
            session.original_sentence, session.target_corrected
        )
    return state
