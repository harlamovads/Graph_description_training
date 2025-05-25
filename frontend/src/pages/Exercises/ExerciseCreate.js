import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Divider,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Card,
  CardMedia,
  Chip
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';

import { setAlert } from '../../redux/actions/uiActions';
import submissionService from '../../services/submissionService';
import exerciseService from '../../services/exerciseService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ExerciseCreate = () => {
  const { submissionId } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [submission, setSubmission] = useState(null);
  const [selectedSentence, setSelectedSentence] = useState('');
  const [sentences, setSentences] = useState([]);
  
  useEffect(() => {
  const fetchSubmission = async () => {
    try {
      setLoading(true);
      console.log('Fetching submission with ID:', submissionId);
      
      const response = await submissionService.getSubmission(submissionId);
      console.log('Submission response received:', response);
      console.log('Response type:', typeof response);
      console.log('Response keys:', Object.keys(response));
      
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
}, [submissionId]);
  
  const generateExercise = async () => {
    if (!selectedSentence.trim()) {
      dispatch(setAlert('Please select a sentence first', 'error'));
      return;
    }
    
    try {
      setCreating(true);
      
      const response = await exerciseService.generateExercise(
        submissionId,
        selectedSentence,
        submission.task.image_url
      );
      
      dispatch(setAlert('Exercise generated successfully', 'success'));
      navigate(`/exercises/${response.exercise.id}/preview`);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to generate exercise',
        'error'
      ));
      setCreating(false);
    }
  };
  
  const addSentence = () => {
    if (!selectedSentence.trim()) {
      dispatch(setAlert('Please enter a sentence', 'error'));
      return;
    }
    
    if (sentences.includes(selectedSentence)) {
      dispatch(setAlert('This sentence is already in the list', 'error'));
      return;
    }
    
    setSentences([...sentences, selectedSentence]);
    setSelectedSentence('');
  };
  
  const removeSentence = (index) => {
    const newSentences = [...sentences];
    newSentences.splice(index, 1);
    setSentences(newSentences);
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading submission..." />;
  }
  
  if (creating) {
    return <LoadingSpinner message="Generating exercise..." />;
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
          onClick={() => navigate(`/submissions/${submissionId}`)}
          sx={{ mr: 2 }}
        >
          Back to Submission
        </Button>
        <Typography variant="h4">Create Exercise</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {submission.task.title}
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Based on submission from:
          </Typography>
          <Chip 
            label={submission.submitted_at ? new Date(submission.submitted_at).toLocaleDateString() : 'Unknown date'}
            size="small"
            variant="outlined"
          />
        </Box>
        
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          <Box sx={{ flex: 2 }}>
            <Typography variant="h6" gutterBottom>
              Select a Sentence
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose a sentence with errors from your submission to create an exercise.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              placeholder="Enter or paste a sentence with grammatical errors..."
              value={selectedSentence}
              onChange={(e) => setSelectedSentence(e.target.value)}
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={addSentence}
              >
                Add Sentence
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={generateExercise}
                disabled={sentences.length === 0 && !selectedSentence.trim()}
              >
                Generate Exercise
              </Button>
            </Box>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Selected Sentences
              </Typography>
              
              {sentences.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No sentences added yet. Add sentences above.
                </Typography>
              ) : (
                <List>
                  {sentences.map((sentence, index) => (
                    <ListItem key={index} divider>
                      <ListItemText
                        primary={sentence}
                        primaryTypographyProps={{
                          variant: 'body2',
                          style: { 
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }
                        }}
                      />
                      <ListItemSecondaryAction>
                        <IconButton edge="end" onClick={() => removeSentence(index)}>
                          <DeleteIcon />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          </Box>
          
          <Box sx={{ flex: 1 }}>
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
            
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              This image will be included with the exercise to provide context for the sentences.
            </Typography>
          </Box>
        </Box>
      </Paper>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          onClick={() => navigate(`/submissions/${submissionId}`)}
          sx={{ mr: 2 }}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          color="primary"
          startIcon={<SaveIcon />}
          onClick={generateExercise}
          disabled={sentences.length === 0 && !selectedSentence.trim()}
        >
          Generate Exercise
        </Button>
      </Box>
    </Box>
  );
};

export default ExerciseCreate;