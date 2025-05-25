import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardMedia,
  Divider,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import EditNoteIcon from '@mui/icons-material/EditNote';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

import { setAlert } from '../../redux/actions/uiActions';
import submissionService from '../../services/submissionService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const SubmissionDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submission, setSubmission] = useState(null);
  
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
  
  if (loading) {
    return <LoadingSpinner message="Loading submission..." />;
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
                <CardMedia
                  component="img"
                  image={submission.task.image_url}
                  alt={submission.task.title}
                  sx={{ height: 200 }}
                />
              </Card>
            )}
            
            <Box sx={{ mt: 3 }}>
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
                submission.status === 'reviewed' && (
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<FitnessCenterIcon />}
                    component={RouterLink}
                    to={`/exercises/create/${submission.id}`}
                    fullWidth
                  >
                    Create Exercise
                  </Button>
                )
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Student's Response</Typography>
        <Box 
          sx={{ mt: 2, p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}
          dangerouslySetInnerHTML={{ __html: submission.content }}
        />
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
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography>View Detailed Analysis</Typography>
                </AccordionSummary>
                <AccordionDetails>
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
                </AccordionDetails>
              </Accordion>
            )}
          </>
        ) : (
          <Typography variant="body2" color="text.secondary">
            No analysis available for this submission.
          </Typography>
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