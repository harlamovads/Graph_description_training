import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  TextField,
  Divider,
  Card,
  CardMedia
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SendIcon from '@mui/icons-material/Send';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

import { setAlert } from '../../redux/actions/uiActions';
import submissionService from '../../services/submissionService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const SubmissionReview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [feedback, setFeedback] = useState('');
  
  useEffect(() => {
  const fetchSubmission = async () => {
    try {
      setLoading(true);
      console.log('Fetching submission with ID:', id);
      
      const response = await submissionService.getSubmission(id);
      console.log('Submission response received:', response);
      
      setSubmission(response);
      console.log('Submission set in state:', response);
      
      setLoading(false);
    } catch (err) {
      console.log('Error fetching submission:', err);
      console.log('Error response:', err.response);
      setError(err.response?.data?.error || 'Failed to load submission details');
      setLoading(false);
    }
  };
  
  fetchSubmission();
}, [id]);
  
  const handleFeedbackChange = (e) => {
    setFeedback(e.target.value);
  };
  
  const handleSubmit = async () => {
    if (!feedback.trim()) {
      dispatch(setAlert('Please provide feedback before submitting', 'error'));
      return;
    }
    
    try {
      setSubmitting(true);
      
      await submissionService.reviewSubmission(id, feedback);
      
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
    return <LoadingSpinner message="Submitting feedback..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!submission) {
    return <ErrorBox error="Submission not found" />;
  }
  
  // Prevent reviewing already reviewed submissions
  if (submission.status === 'reviewed') {
    return (
      <ErrorBox error="This submission has already been reviewed" />
    );
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
        <Typography variant="h4">Review Submission</Typography>
      </Box>
      
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
            <Box 
              sx={{ mt: 1, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}
              dangerouslySetInnerHTML={{ __html: submission.content }}
            />
          </Grid>
          
          <Grid item xs={12} md={4}>
            {submission.task.image_url && (
              <Card>
                <CardMedia
                  component="img"
                  image={submission.task.image_url}
                  alt={submission.task.title}
                  sx={{ height: 200 }}
                />
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
              The neural network detected {submission.analysis_result.total_errors || 0} potential errors in the text.
            </Typography>
            
            {submission.analysis_result?.html_output ? (
              <Box 
                sx={{ mt: 2 }}
                dangerouslySetInnerHTML={{ __html: submission.analysis_result.html_output }}
              />
            ) : (
              <>
                {submission.analysis_result.sentences?.map((sentence, index) => (
                  <Box key={index} sx={{ mb: 2, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
                    <Typography variant="body1" paragraph>
                      {sentence.content}
                    </Typography>
                    
                    {sentence.errors.length > 0 ? (
                      <>
                        <Typography variant="subtitle2" gutterBottom>
                          Errors Found:
                        </Typography>
                        <Box component="ul" sx={{ mt: 1, pl: 2 }}>
                          {sentence.errors.map((error, errorIndex) => (
                            <Box component="li" key={errorIndex}>
                              <Typography variant="body2">
                                <strong>{error.type}</strong>: {error.original}
                                {error.suggestion && ` → ${error.suggestion}`}
                              </Typography>
                            </Box>
                          ))}
                        </Box>
                      </>
                    ) : (
                      <Typography variant="body2" color="success.main">
                        No errors detected
                      </Typography>
                    )}
                  </Box>
                ))}
              </>
            )}
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No analysis available for this submission.
          </Typography>
        )}
      </Paper>
      
      <Paper sx={{ p: 3 }}>
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
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
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
            sx={{ mr: 2 }}
          >
            Submit Feedback
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<FitnessCenterIcon />}
            component={RouterLink}
            to={`/exercises/create/${submission.id}`}
          >
            Create Exercise
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SubmissionReview;