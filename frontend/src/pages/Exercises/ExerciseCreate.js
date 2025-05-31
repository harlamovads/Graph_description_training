// frontend/src/pages/Exercises/ExerciseCreate.js
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
  Chip,
  Alert,
  CircularProgress,
  LinearProgress
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import StorageIcon from '@mui/icons-material/Storage';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';

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
  
  // Database status state
  const [databaseStatus, setDatabaseStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch submission
        const submissionResponse = await submissionService.getSubmission(submissionId);
        setSubmission(submissionResponse);
        
        // Fetch database status
        try {
          const statusResponse = await exerciseService.getSentenceDatabaseStatus();
          setDatabaseStatus(statusResponse);
        } catch (err) {
          console.log('Could not fetch database status:', err);
          setDatabaseStatus({ status: 'unavailable' });
        }
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load submission details');
        setLoading(false);
      } finally {
        setLoadingStatus(false);
      }
    };
    
    fetchData();
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
      
      dispatch(setAlert(
        `Enhanced exercise generated successfully! ${response.sentences_from_database || 0} sentences from database included.`, 
        'success'
      ));
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
    return <LoadingSpinner message="Loading submission..." variant="database" />;
  }
  
  if (creating) {
    return <LoadingSpinner message="Generating enhanced exercise from database..." variant="exercise" />;
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
        <Typography variant="h4">Create Enhanced Exercise</Typography>
      </Box>
      
      {/* Database Status Card */}
      {!loadingStatus && (
        <Paper sx={{ p: 3, mb: 3, backgroundColor: '#f8f9fa', border: '1px solid #e0e0e0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <StorageIcon sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="h6">
              📚 Sentence Database Status
            </Typography>
          </Box>
          
          {databaseStatus?.status === 'loaded' ? (
  <Box>
    <Alert severity="success" sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <CheckCircleIcon sx={{ mr: 1 }} />
        <Typography variant="body2">
          Database loaded with <strong>{databaseStatus.total_sentences?.toLocaleString()}</strong> sentences
        </Typography>
      </Box>
    </Alert>
    
    {databaseStatus.error_types && databaseStatus.error_types.length > 0 && (
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" gutterBottom>
          <strong>Available GED error types:</strong>
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
          {/* Show the actual GED tags with descriptions */}
          {databaseStatus.error_types.slice(0, 12).map((errorType) => {
            const descriptions = {
              'ORTH': 'Orthography',
              'FORM': 'Word Form', 
              'MORPH': 'Morphology',
              'DET': 'Determiners',
              'POS': 'Part of Speech',
              'VERB': 'Verb Errors',
              'NUM': 'Number',
              'WORD': 'Word Choice',
              'PUNCT': 'Punctuation',
              'RED': 'Redundancy',
              'MULTIWORD': 'Multi-word',
              'SPELL': 'Spelling'
            };
            
            return (
              <Chip 
                key={errorType}
                label={`${errorType} - ${descriptions[errorType] || errorType}`} 
                size="small" 
                variant="outlined"
                color="primary"
                title={descriptions[errorType] || errorType}
              />
            );
          })}
          {databaseStatus.error_types.length > 12 && (
            <Chip 
              label={`+${databaseStatus.error_types.length - 12} more`} 
              size="small" 
              variant="outlined"
            />
          )}
        </Box>
      </Box>
    )}
    
    <Typography variant="body2" color="text.secondary">
      💡 Your exercise will include similar sentences from this database using advanced GED tag matching for enhanced practice
    </Typography>
  </Box>
) : (
            <Alert severity="info">
              <Typography variant="body2">
                Database status unavailable. Exercise generation will proceed with available methods.
              </Typography>
            </Alert>
          )}
        </Paper>
      )}
      
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
              Select a Sentence for Enhanced Exercise
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Choose a sentence with errors from your submission. Our system will find similar sentences 
              from the database with matching error patterns to create a comprehensive exercise.
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
                variant="contained"
                color="primary"
                startIcon={<RefreshIcon />}
                onClick={generateExercise}
                disabled={sentences.length === 0 && !selectedSentence.trim()}
              >
                Generate Enhanced Exercise
              </Button>
            </Box>
            
            {/* Show creation progress */}
            {creating && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Creating exercise with database sentences...
                </Typography>
                <LinearProgress />
              </Box>
            )}
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                Selected Sentences
              </Typography>
              
              {sentences.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No sentences added yet. Add sentences above to create a multi-sentence exercise.
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
              <Card sx={{ mb: 2 }}>
                <CardMedia
                  component="img"
                  image={submission.task.image_url}
                  alt={submission.task.title}
                  sx={{ height: 200 }}
                />
              </Card>
            )}
            
            <Alert severity="info">
              <Typography variant="body2">
                <strong>Enhanced Exercise Features:</strong>
              </Typography>
              <Box component="ul" sx={{ mt: 1, pl: 2, mb: 0 }}>
                <li>Similar sentences from curated database</li>
                <li>Matching error pattern detection</li>
                <li>Comprehensive grammar practice</li>
                <li>Detailed feedback and scoring</li>
              </Box>
            </Alert>
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
          Generate Enhanced Exercise
        </Button>
      </Box>
    </Box>
  );
};

export default ExerciseCreate;