import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
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
  CardMedia
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SaveIcon from '@mui/icons-material/Save';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';

import { setAlert } from '../../redux/actions/uiActions';
import taskService from '../../services/taskService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

const TaskCreate = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    is_from_database: false,
    image: null
  });
  
  const [previewUrl, setPreviewUrl] = useState(null);
  
  const { title, description, is_from_database } = formData;
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    
    if (file) {
      setFormData({
        ...formData,
        image: file
      });
      
      // Create preview URL
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewUrl(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!title.trim() || !description.trim()) {
      dispatch(setAlert('Please fill in all required fields', 'error'));
      return;
    }
    
    // Validate image
    if (!formData.image) {
      dispatch(setAlert('Please upload an image for the task', 'error'));
      return;
    }
    
    try {
      setLoading(true);
      
      const result = await taskService.createTask(formData);
      
      dispatch(setAlert('Task created successfully', 'success'));
      navigate(`/tasks/${result.task.id}`);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to create task',
        'error'
      ));
      setLoading(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Creating task..." />;
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
        <Typography variant="h4">Create New Task</Typography>
      </Box>
      
      <Paper sx={{ p: 3 }}>
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
                margin="normal"
                sx={{ mt: 2 }}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle1" gutterBottom>
                Task Image
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Upload an image for this task (chart, graph, or other visual)
              </Typography>
              
              <Box sx={{ mt: 2, mb: 3 }}>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<CloudUploadIcon />}
                  fullWidth
                >
                  Upload Image
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                    onChange={handleImageChange}
                  />
                </Button>
              </Box>
              
              {previewUrl && (
                <Card sx={{ mt: 2 }}>
                  <CardMedia
                    component="img"
                    height="200"
                    image={previewUrl}
                    alt="Image Preview"
                  />
                </Card>
              )}
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 3 }} />
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate('/tasks')}
              sx={{ mr: 2 }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={<SaveIcon />}
            >
              Create Task
            </Button>
          </Box>
        </form>
      </Paper>
    </Box>
  );
};

export default TaskCreate;