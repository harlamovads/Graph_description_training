import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import practiceService from '../../services/practiceService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import GrammarDiffView from '../../components/common/GrammarDiffView';

const formatSeconds = (seconds) => {
  if (seconds === null || seconds === undefined) return 'N/A';
  const minutes = Math.round(seconds / 60);
  if (minutes < 1) return '<1 min';
  return `${minutes} min`;
};

const statusColor = (status) => {
  if (status === 'completed') return 'success';
  if (status === 'stopped') return 'default';
  return 'info';
};

const PracticeSessionList = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    const fetch = async () => {
      try {
        const response = await practiceService.getTeacherSessions();
        setSessions(response.sessions || []);
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load practice sessions');
        setLoading(false);
      }
    };
    fetch();
  }, []);

  if (loading) return <LoadingSpinner message="Loading practice sessions..." />;
  if (error) return <ErrorBox error={error} />;

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button startIcon={<ArrowBackIcon />} component={RouterLink} to="/dashboard" sx={{ mr: 2 }}>
          Back to Dashboard
        </Button>
        <Typography variant="h5">Practice Sessions</Typography>
      </Box>

      <Paper>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>From</TableCell>
                <TableCell>Sentence practised</TableCell>
                <TableCell align="right">Sentences</TableCell>
                <TableCell align="right">Time</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Started</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sessions.map((s) => (
                <TableRow
                  key={s.id}
                  hover
                  sx={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/practice-review/${s.id}`)}
                >
                  <TableCell>{s.student?.username}</TableCell>
                  <TableCell>
                    {/* A session started from a sentence the student wrote themselves has no
                        task behind it, so this column used to be blank for them. */}
                    {s.source === 'manual' ? (
                      <Chip size="small" variant="outlined" color="secondary" label="Own sentence" />
                    ) : (
                      s.task_title || <em>Task removed</em>
                    )}
                  </TableCell>
                  <TableCell sx={{ maxWidth: 320 }}>
                    <Typography variant="body2" noWrap title={s.original_sentence}>
                      {s.original_sentence}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">{s.sentences_completed}</TableCell>
                  <TableCell align="right">{formatSeconds(s.time_spent_seconds)}</TableCell>
                  <TableCell><Chip size="small" label={s.status} color={statusColor(s.status)} /></TableCell>
                  <TableCell align="right">{s.started_at ? new Date(s.started_at).toLocaleDateString() : ''}</TableCell>
                </TableRow>
              ))}
              {sessions.length === 0 && (
                <TableRow><TableCell colSpan={7}>No practice sessions yet.</TableCell></TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

const PracticeSessionDetail = () => {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [session, setSession] = useState(null);

  const fetchDetail = useCallback(async () => {
    try {
      const response = await practiceService.getSessionReview(sessionId);
      setSession(response);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load practice session');
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  if (loading) return <LoadingSpinner message="Loading practice session..." />;
  if (error) return <ErrorBox error={error} />;
  if (!session) return <ErrorBox error="Practice session not found" />;

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/practice-review')} sx={{ mr: 2 }}>
          Back to Sessions
        </Button>
        <Typography variant="h5">Practice Session — {session.student?.username}</Typography>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        {session.source === 'manual' ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Chip size="small" variant="outlined" color="secondary" label="Own sentence" />
            <Typography variant="body2" color="text.secondary">
              The student wrote this sentence themselves and marked the errors in it, so the
              corrections below are their own rather than the neural network's.
            </Typography>
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary">
            Task: {session.task_title || <em>removed</em>}
          </Typography>
        )}
        <Box sx={{ my: 1.5, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">Sentence practised</Typography>
          <Typography variant="body1">{session.original_sentence}</Typography>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            Target
          </Typography>
          <Typography variant="body1">{session.target_corrected}</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Status: <Chip size="small" label={session.status} color={statusColor(session.status)} />
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Sentences completed: {session.sentences_completed} · Time: {formatSeconds(session.time_spent_seconds)}
        </Typography>
      </Paper>

      {(session.history || []).map((round, i) => (
        <Paper key={i} sx={{ p: 3, mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Round {i + 1} — {round.step_type === 'rewrite_original' ? 'Rewrite original sentence' : 'Create a sentence'}
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>{round.prompt}</Typography>
          <Divider sx={{ mb: 2 }} />
          <GrammarDiffView
            original={round.submitted_text}
            corrected={round.target}
            edits={round.edits || []}
            gentleHighlight
          />
          <Chip
            size="small"
            sx={{ mt: 1 }}
            label={round.resolved ? 'Resolved' : 'Retry'}
            color={round.resolved ? 'success' : 'warning'}
          />
        </Paper>
      ))}
      {(session.history || []).length === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography color="text.secondary">No rounds recorded yet.</Typography>
        </Paper>
      )}
    </Box>
  );
};

export { PracticeSessionList, PracticeSessionDetail };
