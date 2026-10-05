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
  Divider,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import SaveIcon from '@mui/icons-material/Save';

import { setAlert } from '../../redux/actions/uiActions';
import taskService from '../../services/taskService';
import submissionService from '../../services/submissionService';
import RichTextEditor from '../../components/common/RichTextEditor';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import useActivityHeartbeat from '../../utils/useActivityHeartbeat';
import { formatDueDate, isOverdue } from '../../utils/helpers';
import TaskImage from '../../components/common/TaskImage';

const SubmissionCreate = () => {
  const { id } = useParams(); // Task ID
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  // Set when the server refuses the submission because it is at capacity (HTTP 503). Shown as a
  // persistent banner rather than the usual 5-second toast: the student needs long enough to read
  // that their text is still here and that retrying shortly is all that is needed.
  const [serverBusy, setServerBusy] = useState(null);
  const [error, setError] = useState(null);
  const [task, setTask] = useState(null);
  const [content, setContent] = useState('');

  // Tracks active time spent on this task while the page is open, so the teacher's stats
  // dashboard can show it (see backend/routes/activity.py).
  useActivityHeartbeat('task', id, !loading && !!task);

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
      setServerBusy(null);
      
      const response = await submissionService.createSubmission({
        task_id: id,
        content
      });
      
      dispatch(setAlert('Submission created successfully', 'success'));
      navigate(`/submissions/${response.submission?.id || response.id}`);
    } catch (err) {
      if (err.response?.status === 503) {
        const retryAfter = Number(err.response.headers?.['retry-after']);
        setServerBusy({
          message: err.response.data?.error
            || 'The server is busy right now. Please try again in a few minutes.',
          retryAfter: Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter : null
        });
      } else {
        dispatch(setAlert(
          err.response?.data?.error || 'Failed to create submission',
          'error'
        ));
      }
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading task..." />;
  }
  
  if (submitting) {
    return (
      <LoadingSpinner
        message="Submitting your response..."
        variant="analysis"
        note="Your writing is being checked for grammar errors. This can take a few minutes if
              several students submit at the same time - please wait and do not close or reload
              this page, or your submission may be lost."
      />
    );
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
        {formatDueDate(task.due_date) && (
          <Typography
            variant="body2"
            sx={{ mb: 1, fontWeight: 500 }}
            color={isOverdue(task.due_date) ? 'error.main' : 'text.secondary'}
          >
            Due {formatDueDate(task.due_date)}
            {isOverdue(task.due_date) ? ' - overdue' : ''}
          </Typography>
        )}
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
                <TaskImage src={task.image_url} alt={task.title} maxHeight={260} />
              </Card>
            )}
          </Grid>
        </Grid>
      </Paper>
      
      <Paper sx={{ p: 3 }}>
        {serverBusy && (
          <Alert severity="warning" sx={{ mb: 2 }} onClose={() => setServerBusy(null)}>
            {serverBusy.message}
            {serverBusy.retryAfter
              ? ` Estimated wait: about ${Math.max(1, Math.round(serverBusy.retryAfter / 60))} minute(s).`
              : ''}
            {' '}Your text is still here - press Submit Response again when you are ready.
          </Alert>
        )}
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