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
  CardMedia,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';

import exerciseService from '../../services/exerciseService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ExerciseResults = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exercise, setExercise] = useState(null);
  const [attempts, setAttempts] = useState([]);
  
  useEffect(() => {
    const fetchExerciseData = async () => {
      try {
        setLoading(true);
        
        // Get exercise details
        const exerciseResponse = await exerciseService.getExercise(id);
        setExercise(exerciseResponse);
        
        // Get attempt details
        const attemptsResponse = await exerciseService.getExerciseAttempts(id);
        setAttempts(attemptsResponse.attempts || []);
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load exercise results');
        setLoading(false);
      }
    };
    
    fetchExerciseData();
  }, [id]);
  
  if (loading) {
    return <LoadingSpinner message="Loading results..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!exercise) {
    return <ErrorBox error="Exercise not found" />;
  }
  
  // For students, show only their own attempt
  const displayAttempts = isTeacher 
    ? attempts 
    : attempts.filter(attempt => attempt.student_id === user.id);
  
  // No attempts to display
  if (displayAttempts.length === 0) {
    return (
      <Box>
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/exercises')}
            sx={{ mr: 2 }}
          >
            Back to Exercises
          </Button>
          <Typography variant="h4">Exercise Results</Typography>
        </Box>
        
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No attempts found
          </Typography>
          {!isTeacher && (
            <Button
              variant="contained"
              color="primary"
              component={RouterLink}
              to={`/exercises/${id}/attempt`}
              startIcon={<FitnessCenterIcon />}
              sx={{ mt: 2 }}
            >
              Attempt Exercise
            </Button>
          )}
        </Paper>
      </Box>
    );
  }
  
  // For students, get their latest attempt
  const studentAttempt = !isTeacher ? displayAttempts[0] : null;
  
  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/exercises')}
          sx={{ mr: 2 }}
        >
          Back to Exercises
        </Button>
        <Typography variant="h4">Exercise Results</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {exercise.title}
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="body1" paragraph>
              {exercise.instructions}
            </Typography>
            
            {isTeacher ? (
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  Student Attempts: {displayAttempts.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Average Score: {
                    displayAttempts.length > 0 
                      ? (
                          displayAttempts.reduce((sum, att) => sum + att.score, 0) / 
                          displayAttempts.length
                        ).toFixed(1) 
                      : 'N/A'
                  }%
                </Typography>
              </Box>
            ) : studentAttempt && (
              <Box sx={{ mt: 2, display: 'flex', alignItems: 'center' }}>
                <Typography variant="h6" sx={{ mr: 2 }}>
                  Your Score:
                </Typography>
                <Chip
                  label={`${studentAttempt.score.toFixed(0)}%`}
                  color={studentAttempt.score >= 70 ? 'success' : 'warning'}
                  variant="outlined"
                  size="medium"
                />
              </Box>
            )}
          </Grid>
          
          <Grid item xs={12} md={4}>
            {exercise.image_url && (
              <Card>
                <CardMedia
                  component="img"
                  image={exercise.image_url}
                  alt={exercise.title}
                  sx={{ height: 200 }}
                />
              </Card>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      {isTeacher ? (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            All Attempts
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          {displayAttempts.map((attempt, index) => (
            <Accordion key={attempt.id} defaultExpanded={index === 0}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography variant="subtitle1">
                      {attempt.student?.username || `Student ${attempt.student_id}`}
                    </Typography>
                    <Chip
                      label={`${attempt.score.toFixed(0)}%`}
                      color={attempt.score >= 70 ? 'success' : 'warning'}
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(attempt.completed_at).toLocaleString()}
                  </Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {exercise.sentences && exercise.sentences.map((sentence, idx) => {
                    const response = attempt.responses ? attempt.responses[sentence.id] : null;
                    const analysis = attempt.analysis_result ? attempt.analysis_result[sentence.id] : null;
                    const hasErrors = analysis && analysis.errors && analysis.errors.length > 0;
                    
                    return (
                      <ListItem key={idx} divider>
                        <ListItemText
                          primary={
                            <Box sx={{ mb: 1 }}>
                              <Typography variant="subtitle2">
                                Original Sentence:
                              </Typography>
                              <Typography variant="body2">
                                {sentence.content}
                              </Typography>
                            </Box>
                          }
                          secondary={
                            <Box sx={{ mt: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Typography variant="subtitle2" sx={{ mr: 1 }}>
                                  Student's Response:
                                </Typography>
                                {hasErrors ? (
                                  <ErrorIcon color="error" fontSize="small" />
                                ) : (
                                  <CheckCircleIcon color="success" fontSize="small" />
                                )}
                              </Box>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  backgroundColor: '#f8f9fa', 
                                  p: 1, 
                                  borderRadius: 1,
                                  mt: 0.5
                                }}
                              >
                                {response || 'No response'}
                              </Typography>
                              
                              {hasErrors && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="subtitle2" color="error">
                                    Errors Found:
                                  </Typography>
                                  <Box component="ul" sx={{ mt: 0.5, pl: 2 }}>
                                    {analysis.errors.map((error, errIdx) => (
                                      <Box component="li" key={errIdx}>
                                        <Typography variant="body2">
                                          <strong>{error.type}</strong>: {error.original}
                                          {error.suggestion && ` → ${error.suggestion}`}
                                        </Typography>
                                      </Box>
                                    ))}
                                  </Box>
                                </Box>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    );
                  })}
                </List>
              </AccordionDetails>
            </Accordion>
          ))}
        </Paper>
      ) : studentAttempt && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Your Results
          </Typography>
          <Divider sx={{ mb: 2 }} />
          
          <List>
            {exercise.sentences && exercise.sentences.map((sentence, idx) => {
              const response = studentAttempt.responses ? studentAttempt.responses[sentence.id] : null;
              const analysis = studentAttempt.analysis_result ? studentAttempt.analysis_result[sentence.id] : null;
              const hasErrors = analysis && analysis.errors && analysis.errors.length > 0;
              
              return (
                <ListItem key={idx} divider>
                  <ListItemText
                    primary={
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="subtitle2">
                          Original Sentence:
                        </Typography>
                        <Typography variant="body2">
                          {sentence.content}
                        </Typography>
                      </Box>
                    }
                    secondary={
                      <Box sx={{ mt: 1 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Typography variant="subtitle2" sx={{ mr: 1 }}>
                            Your Response:
                          </Typography>
                          {hasErrors ? (
                            <ErrorIcon color="error" fontSize="small" />
                          ) : (
                            <CheckCircleIcon color="success" fontSize="small" />
                          )}
                        </Box>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            backgroundColor: '#f8f9fa', 
                            p: 1, 
                            borderRadius: 1,
                            mt: 0.5
                          }}
                        >
                          {response || 'No response'}
                        </Typography>
                        
                        {hasErrors && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="subtitle2" color="error">
                              Errors Found:
                            </Typography>
                            <Box component="ul" sx={{ mt: 0.5, pl: 2 }}>
                              {analysis.errors.map((error, errIdx) => (
                                <Box component="li" key={errIdx}>
                                  <Typography variant="body2">
                                    <strong>{error.type}</strong>: {error.original}
                                    {error.suggestion && ` → ${error.suggestion}`}
                                  </Typography>
                                </Box>
                              ))}
                            </Box>
                          </Box>
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              );
            })}
          </List>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              color="primary"
              component={RouterLink}
              to={`/exercises/${id}/attempt`}
              startIcon={<FitnessCenterIcon />}
            >
              Try Again
            </Button>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default ExerciseResults;