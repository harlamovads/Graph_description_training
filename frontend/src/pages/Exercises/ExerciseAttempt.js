import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  TextField,
  Grid,
  Card,
  CardMedia,
  Divider,
  CircularProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckIcon from '@mui/icons-material/Check';

import { setAlert } from '../../redux/actions/uiActions';
import exerciseService from '../../services/exerciseService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ExerciseAttempt = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [exercise, setExercise] = useState(null);
  const [responses, setResponses] = useState({});
  
  useEffect(() => {
    const fetchExercise = async () => {
      try {
        setLoading(true);
        
        const response = await exerciseService.getExercise(id);
        setExercise(response);
        console.log('Exercise data received:', response);
        console.log('Exercise sentences:', response.sentences);
        
        // Initialize responses object
        const initialResponses = {};
        if (response.sentences) {  // Remove .exercise
        response.sentences.forEach(sentence => {
        initialResponses[sentence.id] = '';
        });
        }
        setResponses(initialResponses);
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load exercise details');
        setLoading(false);
      }
    };
    
    fetchExercise();
  }, [id]);
  
  const handleResponseChange = (sentenceId, value) => {
    setResponses({
      ...responses,
      [sentenceId]: value
    });
  };
  
  const handleSubmit = async () => {
    // Check if all sentences have responses
    const emptyResponses = Object.values(responses).filter(r => !r.trim()).length;
    if (emptyResponses > 0) {
      dispatch(setAlert(`Please complete all ${emptyResponses} remaining sentences`, 'error'));
      return;
    }
    
    try {
      setSubmitting(true);
      
      const result = await exerciseService.submitAttempt(id, responses);
      
      dispatch(setAlert('Exercise completed successfully', 'success'));
      navigate(`/exercises/${id}/results`);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to submit exercise',
        'error'
      ));
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading exercise..." />;
  }
  
  if (submitting) {
    return <LoadingSpinner message="Analyzing your responses..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!exercise) {
    return <ErrorBox error="Exercise not found" />;
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
        <Typography variant="h4">Exercise</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {exercise.title}
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              Instructions
            </Typography>
            <Typography variant="body1" paragraph>
              {exercise.instructions}
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Correct the grammatical errors in each sentence. There may be multiple errors per sentence.
            </Typography>
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
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Sentences to Correct
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        {exercise.sentences && exercise.sentences.map((sentence, index) => (
          <Box key={sentence.id} sx={{ mb: 4 }}>
            <Typography variant="subtitle1" gutterBottom>
              Original Sentence {index + 1}:
            </Typography>
            <Paper 
              variant="outlined" 
              sx={{ p: 2, backgroundColor: '#f8f9fa', mb: 2 }}
            >
              <Typography variant="body1">
                {sentence.content}
              </Typography>
            </Paper>
            
            <Typography variant="subtitle1" gutterBottom>
              Your Correction:
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={2}
              variant="outlined"
              placeholder="Enter your corrected version..."
              value={responses[sentence.id] || ''}
              onChange={(e) => handleResponseChange(sentence.id, e.target.value)}
            />
          </Box>
        ))}
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/exercises')}
            sx={{ mr: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<CheckIcon />}
            onClick={handleSubmit}
          >
            Submit Answers
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ExerciseAttempt;