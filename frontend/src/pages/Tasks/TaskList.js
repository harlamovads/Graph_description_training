import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Chip,
  Tabs,
  Tab,
  Divider
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import taskService from '../../services/taskService';
import submissionService from '../../services/submissionService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const TaskList = () => {
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch tasks
        const tasksResponse = await taskService.getTasks();
        setTasks(tasksResponse.tasks || []);
        
        // If student, fetch submissions to check completion status
        if (!isTeacher) {
          const submissionsResponse = await submissionService.getStudentSubmissions();
          setSubmissions(submissionsResponse.submissions || []);
        }
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load tasks');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [isTeacher]);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // For students: Check if a task has been completed
  const isTaskCompleted = (taskId) => {
    return submissions.some(submission => submission.task.id === taskId);
  };
  
  // For students: Get submission ID for a completed task
  const getSubmissionId = (taskId) => {
    const submission = submissions.find(sub => sub.task.id === taskId);
    return submission ? submission.id : null;
  };
  
  // Filter tasks based on selected tab
  const getFilteredTasks = () => {
    if (isTeacher) {
      // For teachers: All tasks, Database tasks, Custom tasks
      if (tabValue === 0) return tasks;
      if (tabValue === 1) return tasks.filter(task => !task.is_from_database);
      if (tabValue === 2) return tasks.filter(task => task.is_from_database);
    } else {
      // For students: All tasks, Pending tasks, Completed tasks
      if (tabValue === 0) return tasks;
      if (tabValue === 1) return tasks.filter(task => !isTaskCompleted(task.id));
      if (tabValue === 2) return tasks.filter(task => isTaskCompleted(task.id));
    }
    return tasks;
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading tasks..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Tasks
        </Typography>
        {isTeacher && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            component={RouterLink}
            to="/tasks/create"
          >
            Create Task
          </Button>
        )}
      </Box>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="task tabs">
          <Tab label="All Tasks" />
          <Tab label={isTeacher ? "My Custom Tasks" : "Pending Tasks"} />
          <Tab label={isTeacher ? "Database Tasks" : "Completed Tasks"} />
        </Tabs>
      </Box>
      
      {getFilteredTasks().length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 5 }}>
          <Typography variant="h6" color="text.secondary">
            No tasks found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {isTeacher 
              ? "Create your first task by clicking the 'Create Task' button above." 
              : "No tasks have been assigned to you yet."}
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {getFilteredTasks().map((task) => (
            <Grid item xs={12} sm={6} md={4} key={task.id}>
              <Card>
                {task.image_url && (
                  <CardMedia
                    component="img"
                    height="140"
                    image={task.image_url}
                    alt={task.title}
                  />
                )}
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {task.title}
                  </Typography>
                  {!isTeacher && (
                    <Box sx={{ mb: 1 }}>
                      <Chip 
                        size="small"
                        label={isTaskCompleted(task.id) ? 'Completed' : 'Pending'} 
                        color={isTaskCompleted(task.id) ? 'success' : 'warning'}
                      />
                    </Box>
                  )}
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {task.description.substring(0, 120)}
                    {task.description.length > 120 ? '...' : ''}
                  </Typography>
                </CardContent>
                <Divider />
                <CardActions>
                  <Button size="small" component={RouterLink} to={`/tasks/${task.id}`}>
                    View Details
                  </Button>
                  {!isTeacher && !isTaskCompleted(task.id) && (
                    <Button 
                      size="small" 
                      color="primary"
                      component={RouterLink}
                      to={`/submissions/${task.id}/create`}
                    >
                      Complete Task
                    </Button>
                  )}
                  {!isTeacher && isTaskCompleted(task.id) && (
                    <Button 
                      size="small" 
                      color="secondary"
                      component={RouterLink}
                      to={`/submissions/${getSubmissionId(task.id)}`}
                    >
                      View Submission
                    </Button>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default TaskList;