import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useParams, useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Paper,
  Grid,
  Divider,
  Card,
  CardMedia,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  OutlinedInput,
  Checkbox,
  ListItemText,
  TextField
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AssignmentIcon from '@mui/icons-material/Assignment';
import EditIcon from '@mui/icons-material/Edit';

import { setAlert } from '../../redux/actions/uiActions';
import taskService from '../../services/taskService';
import authService from '../../services/authService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ITEM_HEIGHT = 48;
const ITEM_PADDING_TOP = 8;
const MenuProps = {
  PaperProps: {
    style: {
      maxHeight: ITEM_HEIGHT * 4.5 + ITEM_PADDING_TOP,
      width: 250,
    },
  },
};

const TaskDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [task, setTask] = useState(null);
  const [assignDialog, setAssignDialog] = useState(false);
  
  // For assignment dialog
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [availableStudents, setAvailableStudents] = useState([]);
  const [dueDate, setDueDate] = useState(null);
  const [assignLoading, setAssignLoading] = useState(false);
  
  useEffect(() => {
    const fetchTask = async () => {
      try {
        setLoading(true);
        
        // Get task details
        const response = await taskService.getTask(id);
        setTask(response);
        
        // If teacher, fetch available students
        if (isTeacher) {
            const studentsResponse = await authService.getStudents();
            setAvailableStudents(studentsResponse.students || []);
                      }
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load task details');
        setLoading(false);
      }
    };
    
    fetchTask();
  }, [id, isTeacher]);
  
  const handleAssignDialogOpen = () => {
    setAssignDialog(true);
  };
  
  const handleAssignDialogClose = () => {
    setAssignDialog(false);
  };
  
  const handleStudentChange = (event) => {
    const {
      target: { value },
    } = event;
    
    setSelectedStudents(
      typeof value === 'string' ? value.split(',') : value,
    );
  };
  
  const handleAssignTask = async () => {
    if (selectedStudents.length === 0) {
      dispatch(setAlert('Please select at least one student', 'error'));
      return;
    }
    
    try {
      setAssignLoading(true);
      
      await taskService.assignTask(
        task.id,
        selectedStudents,
        dueDate?.toISOString()
      );
      
      dispatch(setAlert('Task assigned successfully', 'success'));
      handleAssignDialogClose();
      setAssignLoading(false);
    } catch (err) {
      dispatch(setAlert(
        err.response?.data?.error || 'Failed to assign task',
        'error'
      ));
      setAssignLoading(false);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading task details..." />;
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
        <Typography variant="h4">Task Details</Typography>
      </Box>
      
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h5">{task.title}</Typography>
              {task.is_from_database && (
                <Chip
                  label="Database Task"
                  color="primary"
                  variant="outlined"
                  size="small"
                />
              )}
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mb: 2 }}>
              {task.description}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              {task.image_url && (
                <CardMedia
                  component="img"
                  image={task.image_url}
                  alt={task.title}
                  sx={{ height: 200 }}
                />
              )}
            </Card>
            
            <Box sx={{ mt: 3 }}>
              {isTeacher ? (
                <>
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<AssignmentIcon />}
                    onClick={handleAssignDialogOpen}
                    fullWidth
                    sx={{ mb: 1 }}
                  >
                    Assign to Students
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<EditIcon />}
                    fullWidth
                  >
                    Edit Task
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  color="primary"
                  component={RouterLink}
                  to={`/submissions/${task.id}/create`}
                  fullWidth
                >
                  Complete This Task
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Assign Dialog */}
      <Dialog open={assignDialog} onClose={handleAssignDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Assign Task to Students</DialogTitle>
        <DialogContent>
          <Box sx={{ my: 2 }}>
            <FormControl fullWidth sx={{ mb: 3 }}>
              <InputLabel id="students-label">Select Students</InputLabel>
              <Select
                labelId="students-label"
                id="students"
                multiple
                value={selectedStudents}
                onChange={handleStudentChange}
                input={<OutlinedInput label="Select Students" />}
                renderValue={(selected) => {
                  const selectedNames = selected.map(
                    id => availableStudents.find(s => s.id === id)?.username || ''
                  );
                  return selectedNames.join(', ');
                }}
                MenuProps={MenuProps}
              >
                {availableStudents.map((student) => (
                  <MenuItem key={student.id} value={student.id}>
                    <Checkbox checked={selectedStudents.indexOf(student.id) > -1} />
                    <ListItemText primary={student.username} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <TextField
            label="Due Date (Optional)"
            type="date"
            value={dueDate ? new Date(dueDate).toISOString().split('T')[0] : ''}
            onChange={(e) => setDueDate(new Date(e.target.value))}
            InputLabelProps={{
              shrink: true,
            }}
            fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleAssignDialogClose}>Cancel</Button>
          <Button 
            onClick={handleAssignTask} 
            variant="contained"
            disabled={assignLoading}
          >
            {assignLoading ? 'Assigning...' : 'Assign Task'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskDetails;