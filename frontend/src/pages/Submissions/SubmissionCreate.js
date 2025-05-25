import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Card,
  CardMedia,
  Divider
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';

import { setAlert } from '../../redux/actions/uiActions';
import taskService from '../../services/taskService';
import submissionService from '../../services/submissionService';
import RichTextEditor from '../../components/common/RichTextEditor';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const SubmissionCreate = () => {
  const { id } = useParams(); // Task ID
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [task, setTask] = useState(null);
  const [content, setContent] = useState('');
  
  useEffect(() => {
    const fetchTask = async () => {
      try {
        setLoading(true);
        
        // Get task details
        const response = await taskService.getTask(id);
        setTask(response);
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load task details');
        setLoading(false);
      }
    };
    
    fetchTask();
  }, [id]);
  
  const handleContentChange = (value) => {
    setContent(value);
  };
  
  const handleSubmit = async () => {
    if (!content.trim()) {
      dispatch(setAlert('Please write your response before submitting', 'error'));
      return;
    }
    
    try {
      setSubmitting(true);
      
      const response = await submissionService.createSubmission({
        task_id: id,
        content
      });
      
      dispatch(setAlert('Submission created successfully', 'success'));
      navigate(`/submissions/${response.submission?.id || response.id}`);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to create submission',
        'error'
      ));
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading task..." />;
  }
  
  if (submitting) {
    return <LoadingSpinner message="Submitting your response..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  if (!task) {
    return <ErrorBox error="Task not found" />;
  }
  
return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/tasks')}
          sx={{ mr: 2 }}
        >
          Back to Tasks
        </Button>
        <Typography variant="h4">Complete Task</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>{task.title}</Typography>
        <Divider sx={{ mb: 2 }} />
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mb: 3 }}>
              {task.description}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={4}>
            {task.image_url && (
              <Card sx={{ mb: 2 }}>
                <CardMedia
                  component="img"
                  image={task.image_url}
                  alt={task.title}
                  sx={{ height: 200 }}
                />
              </Card>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>Your Response</Typography>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Write your response below. Your work will be analyzed for grammatical errors after submission.
        </Typography>
        
        <Box sx={{ mt: 2 }}>
          <RichTextEditor
            initialValue=""
            onChange={handleContentChange}
          />
        </Box>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/tasks')}
            sx={{ mr: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={handleSubmit}
          >
            Submit Response
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SubmissionCreate;