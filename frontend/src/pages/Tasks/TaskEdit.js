import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Grid,
  FormControlLabel,
  Switch,
  Divider,
  Card,
  Alert
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SaveIcon from '@mui/icons-material/Save';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import { setAlert } from '../../redux/actions/uiActions';
import taskService from '../../services/taskService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import TaskImage from '../../components/common/TaskImage';

const TaskEdit = () => {
  const { id } = useParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user } = useSelector((state) => state.auth);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [task, setTask] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    is_from_database: false,
    image: null
  });
  const [previewUrl, setPreviewUrl] = useState(null);

  const { title, description, is_from_database } = formData;

  // A shared "task database" task can be opened by any teacher, but only its creator changes it
  // in place. For everyone else, saving creates their own copy - say so before they start typing
  // rather than surprising them afterwards.
  const isCreator = task && user && task.creator_id === user.id;

  useEffect(() => {
    const load = async () => {
      try {
        const data = await taskService.getTask(id);
        setTask(data);
        setFormData({
          title: data.title || '',
          description: data.description || '',
          // Don't carry the shared flag into someone else's copy by default.
          is_from_database: data.creator_id === user?.id ? !!data.is_from_database : false,
          image: null
        });
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load the task');
        setLoading(false);
      }
    };
    load();
  }, [id, user?.id]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFormData({ ...formData, image: file });
      const reader = new FileReader();
      reader.onloadend = () => setPreviewUrl(reader.result);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim() || !description.trim()) {
      dispatch(setAlert('Please fill in all required fields', 'error'));
      return;
    }

    try {
      setSaving(true);
      const result = await taskService.updateTask(id, formData);
      dispatch(setAlert(
        result.forked
          ? 'Saved as your own copy of this task - the original is unchanged'
          : 'Task updated successfully',
        result.forked ? 'info' : 'success'
      ));
      // On a fork the new task has a different id, so go to the copy, not the original.
      navigate(`/tasks/${result.task.id}`);
    } catch (err) {
      dispatch(setAlert(err.response?.data?.error || 'Failed to save the task', 'error'));
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading task..." />;
  }

  if (error) {
    return <ErrorBox error={error} />;
  }

  if (saving) {
    return <LoadingSpinner message="Saving task..." />;
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center' }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(`/tasks/${id}`)}
          sx={{ mr: 2 }}
        >
          Back to Task
        </Button>
        <Typography variant="h4">{isCreator ? 'Edit Task' : 'Edit a Copy'}</Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        {!isCreator && (
          <Alert severity="info" sx={{ mb: 3 }}>
            This task belongs to another teacher and is shared through the task database. Saving
            will create your own copy with your changes; the original stays as it is, so other
            teachers using it are unaffected.
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Task Title"
                name="title"
                value={title}
                onChange={handleChange}
                required
                margin="normal"
              />

              <TextField
                fullWidth
                label="Task Description"
                name="description"
                value={description}
                onChange={handleChange}
                required
                multiline
                rows={6}
                margin="normal"
                helperText="Provide detailed instructions for the task"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={is_from_database}
                    onChange={handleChange}
                    name="is_from_database"
                    color="primary"
                  />
                }
                label="Add to task database (can be reused by other teachers)"
                sx={{ mt: 2 }}
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom>
                Task Image
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Leave this alone to keep the current image, or upload a new one to replace it.
              </Typography>

              <Box sx={{ mt: 2, mb: 3 }}>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<CloudUploadIcon />}
                  fullWidth
                >
                  Replace Image
                  <input type="file" hidden accept="image/*" onChange={handleImageChange} />
                </Button>
              </Box>

              {(previewUrl || task?.image_url) && (
                <Card sx={{ mt: 2 }}>
                  <TaskImage
                    src={previewUrl || task.image_url}
                    alt={previewUrl ? 'New image preview' : task.title}
                    maxHeight={260}
                  />
                </Card>
              )}
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={() => navigate(`/tasks/${id}`)} sx={{ mr: 2 }}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" startIcon={<SaveIcon />}>
              {isCreator ? 'Save Changes' : 'Save as My Copy'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default TaskEdit;
