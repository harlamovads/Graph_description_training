import React, { useState, useEffect, useCallback } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Chip,
  Divider,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import StopIcon from '@mui/icons-material/Stop';
import SendIcon from '@mui/icons-material/Send';

import { setAlert } from '../../redux/actions/uiActions';
import practiceService from '../../services/practiceService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import GrammarDiffView from '../../components/common/GrammarDiffView';
import useActivityHeartbeat from '../../utils/useActivityHeartbeat';

const PracticeSession = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [session, setSession] = useState(null);
  const [text, setText] = useState('');
  const [submitting, setSubmitting] = useState(false);
  // Feedback from the most recent submission: null before any attempt, or
  // { resolved, edits, target } after one.
  const [feedback, setFeedback] = useState(null);
  // Snapshot of what was actually submitted for `feedback` above, frozen at submit time - the
  // feedback diff must keep showing what was graded, not live-follow further edits to `text`.
  const [submittedText, setSubmittedText] = useState('');

  useActivityHeartbeat('exercise', sessionId, !loading && !!session && session.status === 'in_progress');

  const fetchSession = useCallback(async () => {
    try {
      setLoading(true);
      const response = await practiceService.getSession(sessionId);
      setSession(response);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load practice session');
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchSession();
  }, [fetchSession]);

  const handleSubmit = async () => {
    if (!text.trim()) {
      dispatch(setAlert('Please write a sentence before submitting', 'error'));
      return;
    }
    try {
      setSubmitting(true);
      setSubmittedText(text);
      const response = await practiceService.submitRound(sessionId, text);
      setSession(response.session);
      setFeedback({ resolved: response.resolved, edits: response.edits, target: response.target });
      if (response.resolved) {
        setText('');
      }
      setSubmitting(false);
    } catch (err) {
      dispatch(setAlert(err.response?.data?.error || 'Failed to submit', 'error'));
      setSubmitting(false);
    }
  };

  const handleStop = async () => {
    try {
      const response = await practiceService.stop(sessionId);
      setSession(response);
    } catch (err) {
      dispatch(setAlert(err.response?.data?.error || 'Failed to stop the session', 'error'));
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading practice session..." />;
  }
  if (error) {
    return <ErrorBox error={error} />;
  }
  if (!session) {
    return <ErrorBox error="Practice session not found" />;
  }

  const isDone = session.status !== 'in_progress';

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/submissions/${session.submission_id}`)}
            sx={{ mr: 2 }}
          >
            Back to Submission
          </Button>
          <Typography variant="h4">Practice</Typography>
        </Box>
        {!isDone && (
          <Button variant="outlined" color="error" startIcon={<StopIcon />} onClick={handleStop}>
            Stop Exercise
          </Button>
        )}
      </Box>

      {isDone ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            {session.status === 'completed' ? 'Session complete! 🎉' : 'Session stopped'}
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 1 }}>
            You practiced {session.sentences_completed} sentence{session.sentences_completed === 1 ? '' : 's'}.
          </Typography>
          {session.time_spent_seconds != null && (
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Time spent: {Math.round(session.time_spent_seconds / 60)} min
            </Typography>
          )}
          <Button variant="contained" component={RouterLink} to={`/submissions/${session.submission_id}`}>
            Back to Submission
          </Button>
        </Paper>
      ) : (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Chip
              size="small"
              label={`Sentences completed: ${session.sentences_completed}`}
              sx={{ mb: 2 }}
            />
            <Divider sx={{ mb: 2 }} />

            {session.current_step === 'rewrite_original' && (
              <>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Rewrite the sentence below, applying the suggested corrections shown above
                  each highlighted word.
                </Typography>
                <GrammarDiffView
                  original={session.original_sentence}
                  edits={session.initial_edits || []}
                  gentleHighlight
                  suggestionsAboveSpan
                  showCorrected={false}
                />
              </>
            )}

            {session.current_step === 'practice_item' && (
              <>
                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                  {session.prompt}
                </Typography>
                {session.current_item?.examples?.length > 0 && (
                  <Box sx={{ mt: 2, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                      Example sentences for inspiration:
                    </Typography>
                    {session.current_item.examples.map((ex, i) => (
                      <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>
                        {ex}
                      </Typography>
                    ))}
                  </Box>
                )}
              </>
            )}
          </Paper>

          {feedback && !feedback.resolved && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Not quite - here's the difference between what you wrote and the target.
              </Alert>
              <GrammarDiffView
                original={submittedText}
                corrected={feedback.target}
                edits={feedback.edits}
                gentleHighlight
              />
            </Paper>
          )}

          {feedback && feedback.resolved && (
            <Alert severity="success" sx={{ mb: 3 }}>Good job!</Alert>
          )}

          <Paper sx={{ p: 3 }}>
            <TextField
              fullWidth
              multiline
              minRows={2}
              placeholder="Write your sentence here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={submitting}
            />
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                startIcon={<SendIcon />}
                onClick={handleSubmit}
                disabled={submitting}
              >
                Submit
              </Button>
            </Box>
          </Paper>
        </>
      )}
    </Box>
  );
};

export default PracticeSession;
