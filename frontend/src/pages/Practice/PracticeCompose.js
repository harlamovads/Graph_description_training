import React, { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Divider,
  Popover,
  Chip,
  IconButton,
  Alert,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

import practiceService from '../../services/practiceService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const MAX_CHARS = 500;

/**
 * Practice a sentence of your own: type it, mark what is wrong with it and say what each part
 * should be, then drill it through the normal practice rounds.
 *
 * The student's own corrections define the target - the neural network is not asked. This mode
 * is for practising a correction they already know about, so overruling it with the model would
 * defeat the point.
 */
const PracticeCompose = () => {
  const navigate = useNavigate();
  const textRef = useRef(null);

  const [sentence, setSentence] = useState('');
  const [locked, setLocked] = useState(false);   // sentence fixed, now marking it up
  const [marks, setMarks] = useState([]);
  const [draft, setDraft] = useState(null);
  const [anchor, setAnchor] = useState(null);
  const [notice, setNotice] = useState(null);
  const [error, setError] = useState(null);
  const [starting, setStarting] = useState(false);

  const sorted = [...marks].sort((a, b) => a.start - b.start);

  // The marked-up sentence as it will read once the corrections are applied - the same string
  // the backend rebuilds, shown here so the student can see what they are committing to.
  const preview = (() => {
    let out = sentence;
    [...sorted].reverse().forEach((m) => {
      out = out.slice(0, m.start) + m.correction + out.slice(m.end);
    });
    return out.split(/\s+/).filter(Boolean).join(' ');
  })();

  const segments = (() => {
    const out = [];
    let cursor = 0;
    sorted.forEach((mark) => {
      if (mark.start > cursor) out.push({ type: 'plain', text: sentence.slice(cursor, mark.start) });
      out.push({ type: 'marked', text: sentence.slice(mark.start, mark.end), mark });
      cursor = mark.end;
    });
    if (cursor < sentence.length) out.push({ type: 'plain', text: sentence.slice(cursor) });
    return out;
  })();

  const handleMouseUp = (event) => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return;
    const range = selection.getRangeAt(0);
    const container = textRef.current;
    if (!container || !container.contains(range.commonAncestorContainer)) return;

    // Character offsets into `sentence`: the container renders it verbatim under pre-wrap, so a
    // Range's string length is an offset into the sentence itself.
    const before = range.cloneRange();
    before.selectNodeContents(container);
    before.setEnd(range.startContainer, range.startOffset);
    const start = before.toString().length;
    const end = start + range.toString().length;
    if (end <= start) return;

    if (sorted.some((m) => start < m.end && end > m.start)) {
      setNotice('That overlaps a mark you already made - remove it first.');
      selection.removeAllRanges();
      return;
    }

    setNotice(null);
    setAnchor({ top: event.clientY, left: event.clientX });
    setDraft({ start, end, text: sentence.slice(start, end), correction: '' });
  };

  const closeDraft = () => {
    setDraft(null);
    setAnchor(null);
    window.getSelection()?.removeAllRanges();
  };

  const addMark = () => {
    if (!draft) return;
    setMarks([...marks, {
      id: `m${Date.now()}`,
      start: draft.start,
      end: draft.end,
      text: draft.text,
      correction: draft.correction.trim()
    }]);
    closeDraft();
  };

  const startPractice = async () => {
    setError(null);
    setStarting(true);
    try {
      const session = await practiceService.startManual(
        sentence,
        marks.map((m) => ({ start: m.start, end: m.end, correction: m.correction }))
      );
      navigate(`/practice/${session.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Could not start the practice session');
      setStarting(false);
    }
  };

  if (starting) return <LoadingSpinner message="Setting up your practice session..." />;

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/student-dashboard')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">Practise your own sentence</Typography>
      </Box>

      <Stepper activeStep={locked ? 1 : 0} sx={{ mb: 3 }}>
        <Step><StepLabel>Write the sentence</StepLabel></Step>
        <Step><StepLabel>Mark what is wrong with it</StepLabel></Step>
      </Stepper>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Your sentence</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Write a sentence you want to work on - one you got wrong, or one you are unsure about.
        </Typography>

        {!locked ? (
          <>
            <TextField
              fullWidth
              multiline
              minRows={2}
              autoFocus
              placeholder="Type your sentence here..."
              value={sentence}
              onChange={(e) => setSentence(e.target.value.slice(0, MAX_CHARS))}
              helperText={`${sentence.length}/${MAX_CHARS}`}
              sx={{ mt: 1 }}
            />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                disabled={!sentence.trim()}
                onClick={() => setLocked(true)}
              >
                Next: mark the errors
              </Button>
            </Box>
          </>
        ) : (
          <>
            <Paper variant="outlined" sx={{ p: 2, mt: 1, backgroundColor: '#fff' }}>
              <Typography
                ref={textRef}
                onMouseUp={handleMouseUp}
                variant="body1"
                component="div"
                sx={{ whiteSpace: 'pre-wrap', lineHeight: 2.2, cursor: 'text' }}
              >
                {segments.map((seg, i) => (
                  seg.type === 'plain'
                    ? <React.Fragment key={i}>{seg.text}</React.Fragment>
                    : (
                      <Box
                        key={i}
                        component="span"
                        sx={{
                          backgroundColor: '#e3f2fd',
                          borderBottom: '2px solid #64b5f6',
                          borderRadius: '2px',
                          padding: '0 2px'
                        }}
                      >
                        {seg.text}
                      </Box>
                    )
                ))}
              </Typography>
            </Paper>

            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {notice || 'Select the part that is wrong, then say what it should be. '
                + 'Leave the correction empty if the words should simply be removed.'}
            </Typography>

            <Box sx={{ mt: 2 }}>
              <Button size="small" onClick={() => { setLocked(false); setMarks([]); }}>
                Edit the sentence (this clears your marks)
              </Button>
            </Box>
          </>
        )}
      </Paper>

      {locked && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Corrections ({marks.length})</Typography>
          <Divider sx={{ mb: 2 }} />

          {sorted.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Nothing marked yet - select part of the sentence above to add your first correction.
            </Typography>
          ) : (
            <>
              {sorted.map((mark) => (
                <Box key={mark.id} sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.75 }}>
                  <Chip size="small" variant="outlined" label={mark.correction ? 'Replace' : 'Remove'} />
                  <Typography variant="body2" sx={{ textDecoration: 'line-through', color: 'text.secondary' }}>
                    {mark.text}
                  </Typography>
                  {mark.correction && (
                    <>
                      <Typography variant="body2" color="text.secondary">→</Typography>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>{mark.correction}</Typography>
                    </>
                  )}
                  <Box sx={{ flexGrow: 1 }} />
                  <IconButton size="small" onClick={() => setMarks(marks.filter((m) => m.id !== mark.id))}>
                    <DeleteOutlineIcon fontSize="small" />
                  </IconButton>
                </Box>
              ))}

              <Box sx={{ mt: 2, p: 2, backgroundColor: '#f0fff4', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  The sentence you will be practising towards
                </Typography>
                <Typography variant="body1">{preview}</Typography>
              </Box>
            </>
          )}

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              startIcon={<FitnessCenterIcon />}
              disabled={marks.length === 0 || preview === sentence}
              onClick={startPractice}
            >
              Start practice
            </Button>
          </Box>
          {marks.length > 0 && preview === sentence && (
            <Typography variant="caption" color="error" sx={{ display: 'block', mt: 1, textAlign: 'right' }}>
              Your corrections don't change anything yet.
            </Typography>
          )}
        </Paper>
      )}

      <Popover
        open={Boolean(anchor && draft)}
        onClose={closeDraft}
        anchorReference="anchorPosition"
        anchorPosition={anchor || { top: 0, left: 0 }}
        transformOrigin={{ vertical: 'top', horizontal: 'left' }}
      >
        <Box sx={{ p: 2, width: 320 }}>
          <Typography variant="body2" sx={{ fontStyle: 'italic', mb: 1 }}>
            “{draft?.text}”
          </Typography>
          <TextField
            fullWidth
            autoFocus
            size="small"
            label="What should it say?"
            placeholder="Leave empty to remove these words"
            value={draft?.correction ?? ''}
            onChange={(e) => setDraft({ ...draft, correction: e.target.value })}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addMark(); } }}
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 1.5 }}>
            <Button size="small" onClick={closeDraft}>Cancel</Button>
            <Button size="small" variant="contained" onClick={addMark}>Add</Button>
          </Box>
        </Box>
      </Popover>
    </Box>
  );
};

export default PracticeCompose;
