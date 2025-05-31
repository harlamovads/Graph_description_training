// frontend/src/pages/Exercises/ExerciseAttempt.js
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
  Chip,
  Alert,
  Tooltip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckIcon from '@mui/icons-material/Check';
import InfoIcon from '@mui/icons-material/Info';
import StorageIcon from '@mui/icons-material/Storage';
import PersonIcon from '@mui/icons-material/Person';

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
        
        // Initialize responses object
        const initialResponses = {};
        if (response.sentences) {
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
    return <LoadingSpinner message="Loading exercise..." variant="exercise" />;
  }
  
  if (submitting) {
    return <LoadingSpinner message="Analyzing your responses with enhanced neural network..." variant="analysis" />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!exercise) {
    return <ErrorBox error="Exercise not found" />;
  }
  
  // Count sentences by source
  const databaseSentences = exercise.sentences?.filter(s => s.source === 'database').length || 0;
  const originalSentences = exercise.sentences?.filter(s => s.source === 'original').length || 0;
  
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
        <Typography variant="h4">Enhanced Exercise Practice</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {exercise.title}
        </Typography>
        
        {/* Exercise statistics */}
        {(databaseSentences > 0 || originalSentences > 0) && (
          <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {originalSentences > 0 && (
              <Chip 
                icon={<PersonIcon />}
                label={`${originalSentences} from your submission`}
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
        )}
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              Instructions
            </Typography>
            <Typography variant="body1" paragraph>
              {exercise.instructions}
            </Typography>
            
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="body2">
                <strong>Enhanced Exercise:</strong> This exercise includes sentences with similar error patterns 
                to help you practice specific grammar concepts. Pay attention to the error types highlighted for each sentence.
              </Typography>
            </Alert>
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
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Sentences to Correct ({exercise.sentences?.length || 0})
          </Typography>
          <Tooltip title="Some sentences are from your original submission, others are from our curated database with similar error patterns">
            <InfoIcon sx={{ ml: 1, color: 'text.secondary', cursor: 'help' }} />
          </Tooltip>
        </Box>
        <Divider sx={{ mb: 3 }} />
        
        {exercise.sentences && exercise.sentences.map((sentence, index) => (
          <Box key={sentence.id} sx={{ mb: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1, flexWrap: 'wrap', gap: 1 }}>
              <Typography variant="subtitle1" gutterBottom>
                Sentence {index + 1}:
              </Typography>
              
              {/* Show sentence source */}
              {sentence.source === 'database' && (
                <Chip 
                  size="small" 
                  icon={<StorageIcon />}
                  label="From Database" 
                  color="primary" 
                  variant="outlined"
                />
              )}
              
              {sentence.source === 'original' && (
                <Chip 
                  size="small" 
                  icon={<PersonIcon />}
                  label="Your Submission" 
                  color="secondary" 
                  variant="outlined"
                />
              )}
            </Box>
            
            <Paper 
             variant="outlined" 
             sx={{ p: 2, backgroundColor: '#f8f9fa', mb: 2 }}
           >
             <Typography variant="body1">
               {sentence.content}
             </Typography>
             
             {/* Show error types if available */}
             {sentence.error_types && sentence.error_types.length > 0 && (
               <Box sx={{ mt: 1 }}>
                 <Typography variant="caption" color="text.secondary" sx={{ mr: 1 }}>
                   Focus areas:
                 </Typography>
                 {sentence.error_types.map((errorType, idx) => (
                   <Chip 
                     key={idx}
                     label={errorType} 
                     size="small" 
                     variant="outlined"
                     sx={{ mr: 0.5, mb: 0.5, fontSize: '0.7rem', height: '20px' }}
                   />
                 ))}
               </Box>
             )}
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
             helperText={`Sentence ${index + 1} of ${exercise.sentences.length}`}
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
           disabled={Object.values(responses).some(r => !r.trim())}
         >
           Submit Answers
         </Button>
       </Box>
     </Paper>
   </Box>
 );
};

export default ExerciseAttempt;