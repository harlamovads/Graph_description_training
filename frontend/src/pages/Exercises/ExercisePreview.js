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
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import EditIcon from '@mui/icons-material/Edit';
import PublishIcon from '@mui/icons-material/Publish';
import PreviewIcon from '@mui/icons-material/Preview';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';

import { setAlert } from '../../redux/actions/uiActions';
import exerciseService from '../../services/exerciseService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ExercisePreview = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState(null);
  const [exercise, setExercise] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedTitle, setEditedTitle] = useState('');
  const [editedInstructions, setEditedInstructions] = useState('');
  const [editedSentences, setEditedSentences] = useState([]);
  const [publishDialog, setPublishDialog] = useState(false);
  
  useEffect(() => {
    const fetchExercise = async () => {
      try {
        setLoading(true);
        
        const response = await exerciseService.getExercise(id);
        setExercise(response);
        setEditedTitle(response.title);
        setEditedInstructions(response.instructions);
        setEditedSentences([...response.sentences]);
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load exercise details');
        setLoading(false);
      }
    };
    
    fetchExercise();
  }, [id]);
  
  const handleEdit = () => {
    setEditMode(true);
  };
  
  const handleSaveEdit = async () => {
    try {
      setLoading(true);
      
      await exerciseService.updateExercise(id, {
        title: editedTitle,
        instructions: editedInstructions,
        sentences: editedSentences
      });
      
      // Refresh exercise data
      const response = await exerciseService.getExercise(id);
      setExercise(response);
      setEditMode(false);
      
      dispatch(setAlert('Exercise updated successfully', 'success'));
      setLoading(false);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to update exercise',
        'error'
      ));
      setLoading(false);
    }
  };
  
  const handleCancelEdit = () => {
    setEditedTitle(exercise.title);
    setEditedInstructions(exercise.instructions);
    setEditedSentences([...exercise.sentences]);
    setEditMode(false);
  };
  
  const handlePublish = async () => {
    try {
      setPublishing(true);
      
      await exerciseService.publishExercise(id);
      
      dispatch(setAlert('Exercise published successfully! It is now available to the student.', 'success'));
      navigate('/exercises');
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to publish exercise',
        'error'
      ));
      setPublishing(false);
    }
  };
  
  const handleRemoveSentence = (index) => {
    const newSentences = [...editedSentences];
    newSentences.splice(index, 1);
    setEditedSentences(newSentences);
  };
  
  const handleSentenceChange = (index, newContent) => {
    const newSentences = [...editedSentences];
    newSentences[index] = { ...newSentences[index], content: newContent };
    setEditedSentences(newSentences);
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading exercise preview..." />;
  }
  
  if (publishing) {
    return <LoadingSpinner message="Publishing exercise..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!exercise) {
    return <ErrorBox error="Exercise not found" />;
  }
  
  // Only allow teachers to preview their own exercises
  if (user?.role !== 'teacher' || exercise.creator_id !== user.id) {
    return <ErrorBox error="You don't have permission to preview this exercise" />;
  }
  
  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/exercises')}
            sx={{ mr: 2 }}
          >
            Back to Exercises
          </Button>
          <Typography variant="h4">Exercise Preview</Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          {exercise.status === 'draft' && (
            <>
              {!editMode ? (
                <Button
                  variant="outlined"
                  startIcon={<EditIcon />}
                  onClick={handleEdit}
                >
                  Edit Exercise
                </Button>
              ) : (
                <>
                  <Button
                    variant="outlined"
                    onClick={handleCancelEdit}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveEdit}
                  >
                    Save Changes
                  </Button>
                </>
              )}
              <Button
                variant="contained"
                color="primary"
                startIcon={<PublishIcon />}
                onClick={() => setPublishDialog(true)}
                disabled={editMode}
              >
                Publish Exercise
              </Button>
            </>
          )}
          {exercise.status === 'published' && (
            <Button
              variant="outlined"
              startIcon={<PreviewIcon />}
              component={RouterLink}
              to={`/exercises/${id}/results`}
            >
              View Results
            </Button>
          )}
        </Box>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {editMode ? (
            <TextField
              fullWidth
              variant="outlined"
              value={editedTitle}
              onChange={(e) => setEditedTitle(e.target.value)}
              sx={{ mr: 2 }}
            />
          ) : (
            <Typography variant="h5" sx={{ mr: 2 }}>
              {exercise.title}
            </Typography>
          )}
          <Typography 
            variant="body2" 
            sx={{ 
              px: 2, 
              py: 0.5, 
              borderRadius: 1, 
              bgcolor: exercise.status === 'published' ? 'success.main' : 'warning.main',
              color: 'white'
            }}
          >
            {exercise.status === 'published' ? 'Published' : 'Draft'}
          </Typography>
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="h6" gutterBottom>
              Instructions
            </Typography>
            {editMode ? (
              <TextField
                fullWidth
                multiline
                rows={3}
                variant="outlined"
                value={editedInstructions}
                onChange={(e) => setEditedInstructions(e.target.value)}
                sx={{ mb: 2 }}
              />
            ) : (
              <Typography variant="body1" paragraph>
                {exercise.instructions}
              </Typography>
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
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Exercise Sentences ({editMode ? editedSentences.length : exercise.sentences.length})
        </Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {editMode 
            ? "Edit the sentences below or remove ones you don't want to include:"
            : "Students will be asked to correct the following sentences:"
          }
        </Typography>
        <Divider sx={{ mb: 2 }} />
        
        <List>
          {(editMode ? editedSentences : exercise.sentences).map((sentence, index) => (
            <ListItem key={index} divider>
              <ListItemText
                primary={
                  editMode ? (
                    <TextField
                      fullWidth
                      multiline
                      variant="outlined"
                      value={sentence.content}
                      onChange={(e) => handleSentenceChange(index, e.target.value)}
                    />
                  ) : (
                    <Typography variant="body1">
                      <strong>Sentence {index + 1}:</strong> {sentence.content}
                    </Typography>
                  )
                }
              />
              {editMode && (
                <ListItemSecondaryAction>
                  <IconButton 
                    edge="end" 
                    onClick={() => handleRemoveSentence(index)}
                    disabled={editedSentences.length <= 1}
                  >
                    <DeleteIcon />
                  </IconButton>
                </ListItemSecondaryAction>
              )}
            </ListItem>
          ))}
        </List>
        
        {exercise.sentences.length === 0 && (
          <Typography variant="body1" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
            No sentences in this exercise
          </Typography>
        )}
      </Paper>
      
      {/* Publish Confirmation Dialog */}
      <Dialog open={publishDialog} onClose={() => setPublishDialog(false)}>
        <DialogTitle>Publish Exercise?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to publish this exercise? Once published, it will be available 
            to the student and you won't be able to edit it anymore.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPublishDialog(false)}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={() => {
              setPublishDialog(false);
              handlePublish();
            }}
          >
            Publish Exercise
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ExercisePreview;