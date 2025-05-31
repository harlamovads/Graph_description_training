// frontend/src/pages/Exercises/ExerciseResults.js
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
  Chip,
  Alert,
  LinearProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import StorageIcon from '@mui/icons-material/Storage';
import PersonIcon from '@mui/icons-material/Person';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';

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
    return <LoadingSpinner message="Loading results..." variant="analysis" />;
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
  
  // For students, get their latest attempt
  const studentAttempt = !isTeacher ? displayAttempts[0] : null;
  
  // Calculate statistics
  const databaseSentences = exercise.sentences?.filter(s => s.source === 'database').length || 0;
  const originalSentences = exercise.sentences?.filter(s => s.source === 'original').length || 0;
  const averageScore = displayAttempts.length > 0 
    ? displayAttempts.reduce((sum, att) => sum + att.score, 0) / displayAttempts.length 
    : 0;
  
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
        <Typography variant="h4">Enhanced Exercise Results</Typography>
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
            
            {/* Exercise composition info */}
            <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {originalSentences > 0 && (
                <Chip 
                  icon={<PersonIcon />}
                  label={`${originalSentences} from submission`}
                  color="secondary"
                  variant="outlined"
                  size="small"
                />
              )}
              {databaseSentences > 0 && (
                <Chip 
                  icon={<StorageIcon />}
                  label={`${databaseSentences} from database`}
                  color="primary"
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
            
            {isTeacher ? (
              <Box sx={{ mt: 2 }}>
                <Typography variant="h6" gutterBottom>
                  <TrendingUpIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Student Performance Summary
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f0f8ff' }}>
                      <Typography variant="h4" color="primary">
                        {displayAttempts.length}
                      </Typography>
                      <Typography variant="body2">Total Attempts</Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, textAlign: 'center', backgroundColor: '#f0fff4' }}>
                      <Typography variant="h4" color="success.main">
                        {averageScore.toFixed(1)}%
                      </Typography>
                      <Typography variant="body2">Average Score</Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            ) : studentAttempt && (
              <Box sx={{ mt: 2 }}>
                <Alert 
                  severity={studentAttempt.score >= 70 ? 'success' : studentAttempt.score >= 50 ? 'warning' : 'error'}
                  sx={{ mb: 2 }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="body1">
                      <strong>Your Score: {studentAttempt.score.toFixed(0)}%</strong>
                    </Typography>
                    <Box sx={{ width: '100px' }}>
                      <LinearProgress 
                        variant="determinate" 
                        value={studentAttempt.score} 
                        color={studentAttempt.score >= 70 ? 'success' : studentAttempt.score >= 50 ? 'warning' : 'error'}
                      />
                    </Box>
                  </Box>
                </Alert>
                
                {studentAttempt.score >= 90 && (
                  <Alert severity="success">🏆 Excellent work! You've mastered these grammar concepts.</Alert>
                )}
                {studentAttempt.score >= 70 && studentAttempt.score < 90 && (
                  <Alert severity="info">👍 Good job! Review the feedback below to improve further.</Alert>
                )}
                {studentAttempt.score < 70 && (
                  <Alert severity="warning">📚 Keep practicing! Focus on the error patterns highlighted below.</Alert>
                )}
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
            All Student Attempts
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
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                <Typography variant="subtitle2">
                                  Original Sentence:
                                </Typography>
                                
                                {/* Show sentence source */}
                                {sentence.source === 'database' && (
                                  <Chip 
                                    size="small" 
                                    icon={<StorageIcon />}
                                    label="Database" 
                                    color="primary" 
                                    variant="outlined"
                                    sx={{ ml: 1, height: 20 }}
                                  />
                                )}
                                
                                {sentence.source === 'original' && (
                                  <Chip 
                                    size="small" 
                                    icon={<PersonIcon />}
                                    label="Original" 
                                    color="secondary" 
                                    variant="outlined"
                                    sx={{ ml: 1, height: 20 }}
                                  />
                                )}
                              </Box>
                              
                              <Typography variant="body2">
                                {sentence.content}
                              </Typography>
                              
                              {/* Show error types */}
                              {sentence.error_types && sentence.error_types.length > 0 && (
                                <Box sx={{ mt: 1 }}>
                                  <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                                    Target error types:
                                  </Typography>
                                  {sentence.error_types.map((errorType, etIdx) => (
                                    <Chip 
                                      key={etIdx}
                                      label={errorType} 
                                      size="small" 
                                      variant="outlined"
                                      sx={{ mr: 0.5, mb: 0.5, fontSize: '0.6rem', height: '18px' }}
                                    />
                                  ))}
                                </Box>
                              )}
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
            Your Detailed Results
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
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="subtitle2">
                            Sentence {idx + 1}:
                          </Typography>
                          
                          {/* Show sentence source */}
                          {sentence.source === 'database' && (
                            <Chip 
                              size="small" 
                              icon={<StorageIcon />}
                              label="From Database" 
                              color="primary" 
                              variant="outlined"
                              sx={{ ml: 1, height: 20 }}
                            />
                          )}
                          
                          {sentence.source === 'original' && (
                            <Chip 
                              size="small" 
                              icon={<PersonIcon />}
                              label="Your Submission" 
                              color="secondary" 
                              variant="outlined"
                              sx={{ ml: 1, height: 20 }}
                            />
                          )}
                        </Box>
                        
                        <Typography variant="body2">
                          {sentence.content}
                        </Typography>
                        
                        {/* Show error types */}
                        {sentence.error_types && sentence.error_types.length > 0 && (
                          <Box sx={{ mt: 1 }}>
                            <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                              Focus areas:
                            </Typography>
                            {sentence.error_types.map((errorType, etIdx) => (
                              <Chip 
                                key={etIdx}
                                label={errorType} 
                                size="small" 
                                variant="outlined"
                                sx={{ mr: 0.5, mb: 0.5, fontSize: '0.6rem', height: '18px' }}
                              />
                            ))}
                          </Box>
                        )}
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
                              Areas for improvement:
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