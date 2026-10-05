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
import { formatDueDate, isOverdue } from '../../utils/helpers';
import TaskImage from '../../components/common/TaskImage';

// Sentinel value for the "All students" row in the assign dropdown - never sent to the API.
const ALL_STUDENTS = '__all_students__';

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
  
  const allStudentIds = availableStudents.map((s) => s.id);
  const allSelected = availableStudents.length > 0 && selectedStudents.length === availableStudents.length;

  const handleStudentChange = (event) => {
    const {
      target: { value },
    } = event;

    const next = typeof value === 'string' ? value.split(',') : value;

    // The "All students" row is a toggle, not a value of its own: picking it selects everyone
    // (or clears the selection if everyone is already picked) rather than landing in the list.
    if (next.includes(ALL_STUDENTS)) {
      setSelectedStudents(allSelected ? [] : allStudentIds);
      return;
    }

    setSelectedStudents(next);
  };
  
  const handleAssignTask = async () => {
    if (selectedStudents.length === 0) {
      dispatch(setAlert('Please select at least one student', 'error'));
      return;
    }
    
    try {
      setAssignLoading(true);
      
      const response = await taskService.assignTask(
        task.id,
        selectedStudents,
        dueDate?.toISOString()
      );

      // The API reports how many assignments it actually created - students who already had
      // this task are skipped, which matters when assigning to everyone at once.
      dispatch(setAlert(response?.message || 'Task assigned successfully', 'success'));
      setSelectedStudents([]);
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

            {formatDueDate(task.due_date) && (
              <Typography
                variant="body2"
                sx={{ mb: 2, fontWeight: 500 }}
                color={isOverdue(task.due_date) ? 'error.main' : 'text.secondary'}
              >
                Due {formatDueDate(task.due_date)}
                {isOverdue(task.due_date) ? ' - overdue' : ''}
              </Typography>
            )}

            <Typography variant="body1" sx={{ whiteSpace: 'pre-line', mb: 2 }}>
              {task.description}
            </Typography>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Card>
              {task.image_url && (
                <TaskImage src={task.image_url} alt={task.title} maxHeight={260} />
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
                    component={RouterLink}
                    to={`/tasks/${task.id}/edit`}
                    fullWidth
                  >
                    {task.creator_id === user?.id ? 'Edit Task' : 'Edit a Copy'}
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
                  if (selected.length === 0) return '';
                  if (selected.length === availableStudents.length) {
                    return `All students (${selected.length})`;
                  }
                  const selectedNames = selected.map(
                    id => availableStudents.find(s => s.id === id)?.username || ''
                  );
                  return selectedNames.join(', ');
                }}
                MenuProps={MenuProps}
              >
                {availableStudents.length > 0 && (
                  <MenuItem value={ALL_STUDENTS}>
                    <Checkbox
                      checked={allSelected}
                      indeterminate={selectedStudents.length > 0 && !allSelected}
                    />
                    <ListItemText
                      primary="All students"
                      secondary={`${availableStudents.length} total`}
                    />
                  </MenuItem>
                )}
                {availableStudents.map((student) => (
                  <MenuItem key={student.id} value={student.id}>
                    <Checkbox checked={selectedStudents.indexOf(student.id) > -1} />
                    <ListItemText primary={student.username} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {availableStudents.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                No students yet - generate an invitation code from your dashboard and share it
                with them first.
              </Typography>
            )}
            
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
            disabled={assignLoading || selectedStudents.length === 0}
          >
            {assignLoading
              ? 'Assigning...'
              : allSelected
                ? `Assign to all (${selectedStudents.length})`
                : 'Assign Task'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskDetails;