# backend/services/errant_service.py
"""Diff/ERRANT-based error detection.

Replaces highlighting driven by the internal ELECTRA GED tagger's own token predictions
(which can disagree with what the T5 model, or a teacher, actually changed) with edits
computed directly from the diff between a piece of text and its correction, typed using the
ERRANT toolkit (https://github.com/chrisjbryant/errant). This is what both the student/teacher
-facing highlight and the per-student error log (feature: "errors made + ERRANT types") are
built from.
"""
import threading

import errant

_annotator = None
_annotator_lock = threading.Lock()


def get_annotator():
    """Lazily load a single shared ERRANT annotator (spaCy en_core_web_sm under the hood).

    Locked for the same reason as get_model(): without it, simultaneous first requests each
    load their own spaCy pipeline.
    """
    global _annotator
    if _annotator is None:
        with _annotator_lock:
            if _annotator is None:
                _annotator = errant.load('en')
    return _annotator


def compute_edits(original, corrected):
    """Diff `original` against `corrected` and return a list of typed edits.

    Each edit: {
        'errant_type': e.g. 'R:VERB:TENSE', 'M:DET', 'U:PUNCT',
        'category': the coarse ERRANT operation, 'R' | 'M' | 'U',
        'original_text': the original span (empty string for a pure insertion),
        'corrected_text': the replacement span (empty string for a pure deletion),
        'start_char': character offset into `original` where the edit starts,
        'end_char': character offset into `original` where the edit ends
                    (start_char == end_char for a pure insertion)
    }
    Returns [] if the two strings are equivalent (no edits) or either is blank.
    """
    original = (original or '').strip()
    corrected = (corrected or '').strip()
    if not original or not corrected:
        return []

    annotator = get_annotator()
    orig_doc = annotator.parse(original)
    corr_doc = annotator.parse(corrected)
    raw_edits = annotator.annotate(orig_doc, corr_doc)

    edits = []
    for e in raw_edits:
        if e.type == 'UNK' and e.o_str == e.c_str:
            continue

        if e.o_start == e.o_end:
            # Pure insertion: no original span to highlight, anchor at the boundary between
            # the token before and after the insertion point.
            if e.o_start == 0:
                start_char = end_char = 0
            elif e.o_start >= len(orig_doc):
                start_char = end_char = len(original)
            else:
                start_char = end_char = orig_doc[e.o_start - 1].idx + len(orig_doc[e.o_start - 1])
        else:
            span = orig_doc[e.o_start:e.o_end]
            start_char = span.start_char
            end_char = span.end_char

        # Same idea, but anchored into `corrected` instead of `original`. Used by the practice
        # session's KWIC-context prompt for deletion-type edits (nothing removed survives into
        # `original`'s offsets, so a deletion needs its position in `corrected` to find context
        # around it there).
        if e.c_start == e.c_end:
            if e.c_start == 0:
                corrected_start_char = corrected_end_char = 0
            elif e.c_start >= len(corr_doc):
                corrected_start_char = corrected_end_char = len(corrected)
            else:
                corrected_start_char = corrected_end_char = corr_doc[e.c_start - 1].idx + len(corr_doc[e.c_start - 1])
        else:
            corrected_span = corr_doc[e.c_start:e.c_end]
            corrected_start_char = corrected_span.start_char
            corrected_end_char = corrected_span.end_char

        category = e.type.split(':', 1)[0] if e.type else 'OTHER'

        edits.append({
            'errant_type': e.type or 'OTHER',
            'category': category,
            'original_text': e.o_str,
            'corrected_text': e.c_str,
            'start_char': start_char,
            'end_char': end_char,
            'corrected_start_char': corrected_start_char,
            'corrected_end_char': corrected_end_char
        })

    edits.sort(key=lambda e: e['start_char'])
    return edits


def kwic_context(corrected_text, char_pos, num_words=2):
    """A small keyword-in-context window from `corrected_text` around `char_pos` (a
    `corrected_start_char`/`corrected_end_char` from compute_edits) - used to prompt a practice
    session's "create a sentence" round for a deletion-type edit, where there's no replacement
    word to ask the student to feature, only the surrounding structure.

    Returns {'before': <up to num_words words before char_pos>, 'after': <up to num_words words
    after char_pos>}, clipped at sentence edges.
    """
    corrected_text = (corrected_text or '').strip()
    if not corrected_text:
        return {'before': '', 'after': ''}

    doc = get_annotator().parse(corrected_text)
    tokens = list(doc)
    if not tokens:
        return {'before': '', 'after': ''}

    # Index of the first token starting at/after char_pos - the boundary the removed word used
    # to sit at.
    boundary = len(tokens)
    for i, tok in enumerate(tokens):
        if tok.idx >= char_pos:
            boundary = i
            break

    before_tokens = tokens[max(0, boundary - num_words):boundary]
    after_tokens = tokens[boundary:boundary + num_words]

    return {
        'before': ' '.join(t.text for t in before_tokens),
        'after': ' '.join(t.text for t in after_tokens)
    }


def summarize(edits):
    """Aggregate a flat list of edits into counts by ERRANT type / coarse category."""
    by_type = {}
    by_category = {}
    for edit in edits:
        by_type[edit['errant_type']] = by_type.get(edit['errant_type'], 0) + 1
        by_category[edit['category']] = by_category.get(edit['category'], 0) + 1
    return {
        'total_errors': len(edits),
        'by_type': by_type,
        'by_category': by_category
    }
