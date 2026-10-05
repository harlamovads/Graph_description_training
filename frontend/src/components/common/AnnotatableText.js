import React, { useCallback, useMemo, useRef, useState } from 'react';
import {
  Box,
  Paper,
  Popover,
  TextField,
  Button,
  Typography,
  ToggleButton,
  ToggleButtonGroup,
  Chip,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import EditNoteIcon from '@mui/icons-material/EditNote';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';

// A correction proposes different wording; a comment says something about the text. They are
// coloured differently so a teacher can see at a glance which is which - and so can the student.
const STYLES = {
  correction: { bg: '#fff8e1', border: '#ffb300', chip: 'warning', label: 'Correction' },
  comment: { bg: '#e8eaf6', border: '#5c6bc0', chip: 'primary', label: 'Comment' }
};

/**
 * The student's text, annotatable by selecting words in it.
 *
 * Annotations are { id, type: 'correction'|'comment', start, end, quoted_text, content } where
 * start/end are character offsets into `text` (which callers derive with htmlToPlainText, so
 * both the teacher's and the student's view address the same characters).
 *
 * Props:
 *  - text: the plain text to display
 *  - annotations: the current list
 *  - editable: whether selecting text creates annotations (teachers only)
 *  - onChange(nextAnnotations): called whenever the list changes; the caller persists it
 */
const AnnotatableText = ({ text, annotations = [], editable = false, onChange }) => {
  const containerRef = useRef(null);
  const [draft, setDraft] = useState(null);      // a new annotation being written
  const [anchor, setAnchor] = useState(null);    // popover anchor position
  const [openId, setOpenId] = useState(null);    // an existing annotation being viewed
  const [noticed, setNoticed] = useState(null);  // a short message, e.g. overlapping selection

  const sorted = useMemo(
    () => [...annotations].sort((a, b) => a.start - b.start),
    [annotations]
  );

  // Split the text into plain runs and annotated runs. Overlaps are prevented when creating,
  // so a simple left-to-right walk is enough.
  const segments = useMemo(() => {
    const out = [];
    let cursor = 0;
    sorted.forEach((ann) => {
      const start = Math.max(cursor, Math.min(ann.start, text.length));
      const end = Math.max(start, Math.min(ann.end, text.length));
      if (start > cursor) out.push({ type: 'plain', text: text.slice(cursor, start) });
      if (end > start) out.push({ type: 'annotated', text: text.slice(start, end), ann });
      cursor = Math.max(cursor, end);
    });
    if (cursor < text.length) out.push({ type: 'plain', text: text.slice(cursor) });
    return out;
  }, [sorted, text]);

  const overlaps = useCallback(
    (start, end) => sorted.some((a) => start < a.end && end > a.start),
    [sorted]
  );

  // Character offsets of the current selection within the container. This works because the
  // container renders `text` verbatim under white-space: pre-wrap - every character in the DOM
  // is a character of `text`, so a Range's string length is an offset into it.
  const selectionOffsets = () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return null;
    const range = selection.getRangeAt(0);
    const container = containerRef.current;
    if (!container || !container.contains(range.commonAncestorContainer)) return null;

    const before = range.cloneRange();
    before.selectNodeContents(container);
    before.setEnd(range.startContainer, range.startOffset);
    const start = before.toString().length;
    const end = start + range.toString().length;
    return end > start ? { start, end } : null;
  };

  const handleMouseUp = (event) => {
    if (!editable) return;
    const offsets = selectionOffsets();
    if (!offsets) return;
    if (overlaps(offsets.start, offsets.end)) {
      setNoticed('That selection overlaps an existing note - remove it first.');
      window.getSelection()?.removeAllRanges();
      return;
    }
    setNoticed(null);
    setOpenId(null);
    setAnchor({ top: event.clientY, left: event.clientX });
    setDraft({
      id: `a${Date.now()}`,
      type: 'correction',
      start: offsets.start,
      end: offsets.end,
      quoted_text: text.slice(offsets.start, offsets.end),
      content: ''
    });
  };

  const closePopovers = () => {
    setDraft(null);
    setAnchor(null);
    setOpenId(null);
    window.getSelection()?.removeAllRanges();
  };

  const saveDraft = () => {
    if (!draft || !draft.content.trim()) return;
    onChange([...annotations, { ...draft, content: draft.content.trim() }]);
    closePopovers();
  };

  const removeAnnotation = (id) => {
    onChange(annotations.filter((a) => a.id !== id));
    closePopovers();
  };

  const openAnnotation = (event, ann) => {
    setDraft(null);
    setAnchor({ top: event.clientY, left: event.clientX });
    setOpenId(ann.id);
  };

  const openAnn = sorted.find((a) => a.id === openId) || null;

  return (
    <Box>
      <Paper
        variant="outlined"
        sx={{ p: 2, backgroundColor: '#fff', cursor: editable ? 'text' : 'default' }}
      >
        <Typography
          ref={containerRef}
          onMouseUp={handleMouseUp}
          variant="body1"
          component="div"
          sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.9 }}
        >
          {segments.map((seg, i) => {
            if (seg.type === 'plain') return <React.Fragment key={i}>{seg.text}</React.Fragment>;
            const style = STYLES[seg.ann.type] || STYLES.comment;
            return (
              <Tooltip
                key={i}
                arrow
                title={`${style.label}: ${seg.ann.content}`}
              >
                <Box
                  component="span"
                  onClick={(e) => openAnnotation(e, seg.ann)}
                  sx={{
                    backgroundColor: style.bg,
                    borderBottom: `2px solid ${style.border}`,
                    borderRadius: '2px',
                    padding: '0 2px',
                    cursor: 'pointer'
                  }}
                >
                  {seg.text}
                </Box>
              </Tooltip>
            );
          })}
        </Typography>
      </Paper>

      {editable && (
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
          {noticed || 'Select any part of the text to add a correction or a comment. '
            + 'Click an existing note to read or remove it.'}
        </Typography>
      )}

      {sorted.length > 0 && (
        <Paper variant="outlined" sx={{ mt: 2, p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Notes on this text ({sorted.length})
          </Typography>
          <Divider sx={{ mb: 1 }} />
          {sorted.map((ann) => {
            const style = STYLES[ann.type] || STYLES.comment;
            return (
              <Box
                key={ann.id}
                sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, py: 0.75 }}
              >
                <Chip
                  size="small"
                  color={style.chip}
                  variant="outlined"
                  icon={ann.type === 'correction' ? <EditNoteIcon /> : <ChatBubbleOutlineIcon />}
                  label={style.label}
                />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" sx={{ fontStyle: 'italic', color: 'text.secondary' }}>
                    “{ann.quoted_text}”
                  </Typography>
                  <Typography variant="body2">{ann.content}</Typography>
                </Box>
                {editable && (
                  <IconButton size="small" onClick={() => removeAnnotation(ann.id)}>
                    <DeleteOutlineIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
            );
          })}
        </Paper>
      )}

      <Popover
        open={Boolean(anchor && (draft || openAnn))}
        onClose={closePopovers}
        anchorReference="anchorPosition"
        anchorPosition={anchor || { top: 0, left: 0 }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
      >
        <Box sx={{ p: 2, width: 340 }}>
          {draft && (
            <>
              <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                “{draft.quoted_text}”
              </Typography>
              <ToggleButtonGroup
                size="small"
                exclusive
                value={draft.type}
                onChange={(e, value) => value && setDraft({ ...draft, type: value })}
                sx={{ mb: 1.5 }}
              >
                <ToggleButton value="correction">Correction</ToggleButton>
                <ToggleButton value="comment">Comment</ToggleButton>
              </ToggleButtonGroup>
              <TextField
                fullWidth
                multiline
                minRows={2}
                autoFocus
                size="small"
                placeholder={draft.type === 'correction'
                  ? 'How should this be written instead?'
                  : 'Your comment for the student'}
                value={draft.content}
                onChange={(e) => setDraft({ ...draft, content: e.target.value })}
              />
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 1.5 }}>
                <Button size="small" onClick={closePopovers}>Cancel</Button>
                <Button
                  size="small"
                  variant="contained"
                  disabled={!draft.content.trim()}
                  onClick={saveDraft}
                >
                  Add
                </Button>
              </Box>
            </>
          )}

          {!draft && openAnn && (
            <>
              <Chip
                size="small"
                color={(STYLES[openAnn.type] || STYLES.comment).chip}
                variant="outlined"
                label={(STYLES[openAnn.type] || STYLES.comment).label}
                sx={{ mb: 1 }}
              />
              <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
                “{openAnn.quoted_text}”
              </Typography>
              <Typography variant="body2">{openAnn.content}</Typography>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 1.5 }}>
                <Button size="small" onClick={closePopovers}>Close</Button>
                {editable && (
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteOutlineIcon />}
                    onClick={() => removeAnnotation(openAnn.id)}
                  >
                    Remove
                  </Button>
                )}
              </Box>
            </>
          )}
        </Box>
      </Popover>
    </Box>
  );
};

export default AnnotatableText;
