import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  TextField,
  Divider,
  Card,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SendIcon from '@mui/icons-material/Send';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

import { setAlert } from '../../redux/actions/uiActions';
import submissionService from '../../services/submissionService';
import practiceService from '../../services/practiceService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import GrammarDiffView from '../../components/common/GrammarDiffView';
import TaskImage from '../../components/common/TaskImage';
import AnnotatableText from '../../components/common/AnnotatableText';
import { htmlToPlainText } from '../../utils/helpers';

// Score must be a number 0-10, int or float (e.g. 9.5) - not a dropdown, just validated
// free-form input. Empty is allowed (score is optional).
const isValidScore = (value) => {
  if (value === '' || value === null || value === undefined) return true;
  const num = Number(value);
  return !Number.isNaN(num) && num >= 0 && num <= 10;
};

const SubmissionReview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [score, setScore] = useState('');
  // Per-sentence corrections a teacher edits, keyed by sentence id. Prefilled with the NN's
  // correction so the teacher only has to touch the ones they want to change.
  const [corrections, setCorrections] = useState({});
  const [assignedSentences, setAssignedSentences] = useState({});
  const [assigning, setAssigning] = useState(null);
  const [annotations, setAnnotations] = useState([]);
  const [annotationError, setAnnotationError] = useState(null);
  // An already-reviewed submission opens read-only rather than being refused outright: a teacher
  // needs to be able to look back at work they have already marked (reachable from a student's
  // statistics page). Annotating stays available - it is a reading aid, not part of the verdict.
  const alreadyReviewed = submission?.status === 'reviewed';

  useEffect(() => {
    const fetchSubmission = async () => {
      try {
        setLoading(true);
        const response = await submissionService.getSubmission(id);
        setSubmission(response);

        const initialCorrections = {};
        (response.analysis_result?.sentences || []).forEach((sentence) => {
          initialCorrections[sentence.id] = sentence.teacher_corrected || sentence.corrected || sentence.original;
        });
        setCorrections(initialCorrections);
        setAnnotations(response.teacher_annotations || []);

        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load submission details');
        setLoading(false);
      }
    };

    fetchSubmission();
  }, [id]);

  // Persist on every change: the teacher never presses "save annotations", the notes are simply
  // there. On failure the local state is rolled back, so what is on screen is what is stored.
  const handleAnnotationsChange = async (next) => {
    const previous = annotations;
    setAnnotations(next);
    setAnnotationError(null);
    try {
      await submissionService.saveAnnotations(id, next);
    } catch (err) {
      setAnnotations(previous);
      setAnnotationError(err.response?.data?.error || 'Could not save that note - please retry.');
    }
  };

  const handleFeedbackChange = (e) => {
    setFeedback(e.target.value);
  };

  const handleCorrectionChange = (sentenceId, value) => {
    setCorrections({ ...corrections, [sentenceId]: value });
  };

  const handleAssignPractice = async (sentenceId) => {
    try {
      setAssigning(sentenceId);
      await practiceService.assign(submission.id, sentenceId);
      setAssignedSentences({ ...assignedSentences, [sentenceId]: true });
    } catch (err) {
      dispatch(setAlert(err.response?.data?.error || 'Failed to assign practice', 'error'));
    } finally {
      setAssigning(null);
    }
  };

  const handleSubmit = async () => {
    if (!feedback.trim()) {
      dispatch(setAlert('Please provide feedback before submitting', 'error'));
      return;
    }

    if (!isValidScore(score)) {
      dispatch(setAlert('Score must be a number between 0 and 10', 'error'));
      return;
    }

    // Only send corrections that actually differ from the NN's original suggestion.
    const changedCorrections = {};
    (submission.analysis_result?.sentences || []).forEach((sentence) => {
      const edited = corrections[sentence.id];
      if (edited && edited !== (sentence.teacher_corrected || sentence.corrected)) {
        changedCorrections[sentence.id] = edited;
      }
    });

    try {
      setSubmitting(true);

      await submissionService.reviewSubmission(
        id, feedback, changedCorrections, score !== '' ? Number(score) : undefined
      );

      dispatch(setAlert('Feedback submitted successfully', 'success'));
      navigate(`/submissions/${id}`);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to submit feedback',
        'error'
      ));
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading submission..." />;
  }
  
  if (submitting) {
    return (
      <LoadingSpinner
        message="Submitting feedback..."
        note="Please wait and do not close this page while your feedback is saved."
      />
    );
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
          onClick={() => navigate(`/submissions/${id}`)}
          sx={{ mr: 2 }}
        >
          Back to Submission
        </Button>
        <Typography variant="h4">
          {alreadyReviewed ? 'Reviewed Submission' : 'Review Submission'}
        </Typography>
      </Box>

      {alreadyReviewed && (
        <Alert severity="info" sx={{ mb: 3 }}>
          You reviewed this submission on{' '}
          {submission.reviewed_at ? new Date(submission.reviewed_at).toLocaleString() : 'an earlier date'}.
          It is shown here for reference; your feedback is below and cannot be resubmitted, but you
          can still add notes to the student's text.
        </Alert>
      )}
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">{submission.task.title}</Typography>
          <Typography variant="body2" color="text.secondary">
            Submitted by: {submission.student?.username || 'Student'}
          </Typography>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Submitted on: {new Date(submission.submitted_at).toLocaleString()}
            </Typography>
            
            <Typography variant="h6" sx={{ mt: 2 }} gutterBottom>
              Student's Response
            </Typography>
            {annotationError && (
              <Alert severity="error" sx={{ mb: 1 }} onClose={() => setAnnotationError(null)}>
                {annotationError}
              </Alert>
            )}
            <AnnotatableText
              text={htmlToPlainText(submission.content)}
              annotations={annotations}
              editable
              onChange={handleAnnotationsChange}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            {submission.task.image_url && (
              <Card>
                <TaskImage src={submission.task.image_url} alt={submission.task.title} maxHeight={260} />
              </Card>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Grammar Analysis</Typography>

        {submission.analysis_result ? (
          <>
            <Typography variant="body2" color="text.secondary" paragraph>
              The neural network detected {submission.analysis_result.total_errors || 0} potential error(s).
              The highlight below is the diff against the neural network's correction; if you
              edit the correction and save, the highlight and the logged errors are
              recomputed against your version instead.
            </Typography>

            {submission.analysis_result.sentences?.map((sentence) => (
              <Box key={sentence.id} sx={{ mb: 3, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">Sentence {sentence.id + 1}</Typography>
                <GrammarDiffView
                  original={sentence.original}
                  corrected={sentence.teacher_corrected || sentence.corrected}
                  edits={sentence.errant_edits || []}
                  showCorrected={false}
                />
                <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                  {alreadyReviewed ? 'Correction:' : 'Correction (edit if the NN got it wrong):'}
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  variant="outlined"
                  size="small"
                  disabled={alreadyReviewed}
                  value={corrections[sentence.id] ?? ''}
                  onChange={(e) => handleCorrectionChange(sentence.id, e.target.value)}
                />
                {sentence.errant_edits?.length > 0 && (
                  <Button
                    size="small"
                    variant="outlined"
                    color="secondary"
                    startIcon={<FitnessCenterIcon />}
                    sx={{ mt: 1 }}
                    disabled={!!assignedSentences[sentence.id] || assigning === sentence.id}
                    onClick={() => handleAssignPractice(sentence.id)}
                  >
                    {assignedSentences[sentence.id] ? 'Assigned' : 'Assign for Practice'}
                  </Button>
                )}
              </Box>
            ))}
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No analysis available for this submission.
          </Typography>
        )}
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        {alreadyReviewed ? (
          <>
            <Typography variant="h6" gutterBottom>Your Feedback</Typography>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mt: 1 }}>
              {submission.teacher_feedback || 'No written feedback was given.'}
            </Typography>
            <Typography variant="subtitle2" sx={{ mt: 3 }}>
              Score: {submission.score !== null && submission.score !== undefined
                ? submission.score
                : 'not scored'}
            </Typography>
          </>
        ) : (
        <>
        <Typography variant="h6" gutterBottom>Provide Feedback</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Add your feedback for the student's submission
        </Typography>
        
        <TextField
          fullWidth
          multiline
          rows={6}
          variant="outlined"
          placeholder="Enter your feedback here..."
          value={feedback}
          onChange={handleFeedbackChange}
          sx={{ mt: 2 }}
        />

        <Typography variant="subtitle2" sx={{ mt: 3 }} gutterBottom>Score (optional, 0-10)</Typography>
        <TextField
          variant="outlined"
          size="small"
          placeholder="e.g. 9.5"
          value={score}
          onChange={(e) => setScore(e.target.value)}
          error={!isValidScore(score)}
          helperText={!isValidScore(score) ? 'Enter a number between 0 and 10' : ' '}
          sx={{ width: 160 }}
        />

        <Box sx={{ mt: 1, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            onClick={() => navigate(`/submissions/${id}`)}
            sx={{ mr: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SendIcon />}
            onClick={handleSubmit}
          >
            Submit Feedback
          </Button>
        </Box>
        </>
        )}
      </Paper>
    </Box>
  );
};

export default SubmissionReview;