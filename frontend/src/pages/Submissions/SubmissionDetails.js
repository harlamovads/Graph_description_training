// frontend/src/pages/Submissions/SubmissionDetails.js
import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  Divider,
  Chip,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditNoteIcon from '@mui/icons-material/EditNote';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import RefreshIcon from '@mui/icons-material/Refresh';
import BrainIcon from '@mui/icons-material/Psychology';

import { useDispatch } from 'react-redux';
import { setAlert } from '../../redux/actions/uiActions';
import submissionService from '../../services/submissionService';
import practiceService from '../../services/practiceService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { htmlToPlainText } from '../../utils/helpers';
import AnnotatableText from '../../components/common/AnnotatableText';
import ErrorBox from '../../components/common/ErrorBox';
import GrammarDiffView from '../../components/common/GrammarDiffView';
import TaskImage from '../../components/common/TaskImage';

const SubmissionDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [startingPractice, setStartingPractice] = useState(null);

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        setLoading(true);

        const response = await submissionService.getSubmission(id);
        setSubmission(response);

        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load submission details');
        setLoading(false);
      }
    };

    fetchSubmission();
  }, [id]);

  const handlePractice = async (sentenceId) => {
    try {
      setStartingPractice(sentenceId);
      const session = await practiceService.start(submission.id, sentenceId);
      navigate(`/practice/${session.id}`);
    } catch (err) {
      dispatch(setAlert(err.response?.data?.error || 'Failed to start practice session', 'error'));
      setStartingPractice(null);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading submission..." variant="analysis" />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!submission) {
    return <ErrorBox error="Submission not found" />;
  }
  
  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/tasks')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">Submission Details</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">{submission.task.title}</Typography>
          <Chip
            label={submission.status === 'reviewed' ? 'Reviewed' : 'Submitted'}
            color={submission.status === 'reviewed' ? 'success' : 'info'}
          />
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="body2" color="text.secondary">
              Submitted on: {new Date(submission.submitted_at).toLocaleString()}
            </Typography>
            {submission.reviewed_at && (
              <Typography variant="body2" color="text.secondary">
                Reviewed on: {new Date(submission.reviewed_at).toLocaleString()}
              </Typography>
            )}
            
            <Divider sx={{ my: 2 }} />
            
            <Typography variant="h6" gutterBottom>Original Task</Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              {submission.task.description}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={4}>
            {submission.task.image_url && (
              <Card>
                <TaskImage src={submission.task.image_url} alt={submission.task.title} maxHeight={260} />
              </Card>
            )}
            
            <Box sx={{ mt: 3, display: 'flex', flexDirection: 'column', gap: 1 }}>
              {isTeacher ? (
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<EditNoteIcon />}
                  component={RouterLink}
                  to={`/submissions/${submission.id}/review`}
                  fullWidth
                  disabled={submission.status === 'reviewed'}
                >
                  {submission.status === 'reviewed' ? 'Already Reviewed' : 'Review Submission'}
                </Button>
              ) : (
                submission.status === 'reviewed' && submission.is_latest_attempt && (
                  <Button
                    variant="outlined"
                    color="primary"
                    startIcon={<RefreshIcon />}
                    component={RouterLink}
                    to={`/submissions/${submission.task.id}/create`}
                    fullWidth
                  >
                    Resubmit
                  </Button>
                )
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Student's Response</Typography>
        {/* Rendered through AnnotatableText (read-only here) rather than as raw HTML, so the
            teacher's inline corrections and comments appear on the same characters they were
            written against - the offsets are into htmlToPlainText's output. With no annotations
            it is simply the text. */}
        <Box sx={{ mt: 2 }}>
          <AnnotatableText
            text={htmlToPlainText(submission.content)}
            annotations={submission.teacher_annotations || []}
          />
        </Box>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <BrainIcon sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">Enhanced Grammar Analysis</Typography>
        </Box>
        
        {submission.analysis_result ? (
          <>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>{submission.analysis_result.total_errors || 0}</strong> error{submission.analysis_result.total_errors === 1 ? '' : 's'} detected,
                highlighted below against what the neural network (or your teacher) corrected.
                {submission.analysis_result.total_errors === 0 && " Great job on your grammar!"}
              </Typography>
            </Alert>

            {submission.analysis_result.sentences?.map((sentence) => (
              <Box key={sentence.id} sx={{ mb: 2 }}>
                <GrammarDiffView
                  original={sentence.original}
                  corrected={sentence.teacher_corrected || sentence.corrected}
                  edits={sentence.errant_edits || []}
                  suggestionsAboveSpan
                />
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  {sentence.teacher_corrected && (
                    <Chip size="small" label="Corrected by teacher" color="secondary" />
                  )}
                  {!isTeacher && sentence.errant_edits?.length > 0 && (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<FitnessCenterIcon />}
                      disabled={startingPractice === sentence.id}
                      onClick={() => handlePractice(sentence.id)}
                    >
                      Practice this sentence
                    </Button>
                  )}
                </Box>
              </Box>
            ))}
          </>
        ) : (
          <Alert severity="warning">
            <Typography variant="body2">
              No analysis available for this submission. The grammar analysis may still be processing.
            </Typography>
          </Alert>
        )}
      </Paper>
      
      {submission.teacher_feedback && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Teacher's Feedback</Typography>
          <Box 
            sx={{ mt: 2, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}
          >
            <Typography variant="body1">{submission.teacher_feedback}</Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default SubmissionDetails;