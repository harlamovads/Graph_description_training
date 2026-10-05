import React, { useEffect, useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Card,
  CardContent,
  CardActions,
  Chip
} from '@mui/material';
import AssignmentIcon from '@mui/icons-material/Assignment';
import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import AddIcon from '@mui/icons-material/Add';

import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import taskService from '../../services/taskService';
import submissionService from '../../services/submissionService';
import practiceService from '../../services/practiceService';
import { formatDueDate, isOverdue } from '../../utils/helpers';
import TaskImage from '../../components/common/TaskImage';

const StudentDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [pendingTasks, setPendingTasks] = useState([]);
  const [assignedPractice, setAssignedPractice] = useState([]);
  const [startingPractice, setStartingPractice] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch tasks
        const tasksResponse = await taskService.getTasks();
        setTasks(tasksResponse.tasks || []);

        // Fetch submissions
        const submissionsResponse = await submissionService.getStudentSubmissions();
        setSubmissions(submissionsResponse.submissions || []);

        // Fetch teacher-assigned practice sentences not yet started
        const assignmentsResponse = await practiceService.getAssignments();
        setAssignedPractice(assignmentsResponse.assignments || []);

        // Calculate pending tasks (assigned but not submitted)
        const submittedTaskIds = (submissionsResponse.submissions || []).map(
          submission => submission.task.id
        );

        setPendingTasks(
          (tasksResponse.tasks || []).filter(
            task => !submittedTaskIds.includes(task.id)
          )
        );

        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const navigate = useNavigate();

  const handleStartPractice = async (assignment) => {
    try {
      setStartingPractice(assignment.id);
      const session = await practiceService.start(assignment.submission_id, assignment.sentence_index);
      navigate(`/practice/${session.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start practice session');
      setStartingPractice(null);
    }
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Student Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Pending Tasks */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <AssignmentIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Pending Tasks
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {pendingTasks.length > 0 ? (
              <List>
                {pendingTasks.map((task) => (
                  <ListItem
                    key={task.id}
                    divider
                    secondaryAction={
                      <Button
                        variant="contained"
                        size="small"
                        component={RouterLink}
                        to={`/submissions/${task.id}/create`}
                        color="primary"
                      >
                        Complete
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={task.title}
                      secondary={
                        <>
                          <Typography component="span" variant="body2" color="text.primary">
                            {task.description.substring(0, 100)}
                            {task.description.length > 100 ? '...' : ''}
                          </Typography>
                          {formatDueDate(task.due_date) && (
                            <Typography
                              component="span"
                              variant="body2"
                              sx={{ display: 'block', mt: 0.5 }}
                              color={isOverdue(task.due_date) ? 'error.main' : 'text.secondary'}
                            >
                              Due {formatDueDate(task.due_date)}
                              {isOverdue(task.due_date) ? ' - overdue' : ''}
                            </Typography>
                          )}
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body1" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                No pending tasks. Great job!
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Assigned Practice - sentences a teacher flagged for practice, shown alongside
            assigned tasks; starting one enters the same session a self-started one would. */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="h6" gutterBottom>
                <FitnessCenterIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Practice
              </Typography>
              {/* Practice doesn't have to wait for a teacher to assign something - a student
                  can bring a sentence of their own. */}
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => navigate('/practice/new')}
              >
                My own sentence
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {assignedPractice.length > 0 ? (
              <List>
                {assignedPractice.map((assignment) => (
                  <ListItem
                    key={assignment.id}
                    divider
                    secondaryAction={
                      <Button
                        variant="contained"
                        size="small"
                        color="secondary"
                        disabled={startingPractice === assignment.id}
                        onClick={() => handleStartPractice(assignment)}
                      >
                        Start Practice
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={assignment.task_title}
                      secondary={assignment.sentence_original}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body1" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                No practice assigned right now - you can still practise a sentence of your own.
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Progress Summary */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Your Progress
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Tasks Completed
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="h4" color="primary" sx={{ mr: 2 }}>
                  {submissions.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  out of {submissions.length + pendingTasks.length} assigned
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        
        {/* Recent Submissions */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <AssignmentTurnedInIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Recent Submissions
              </Typography>
              <Chip 
                label={`${submissions.length} Total`} 
                color="primary" 
                variant="outlined" 
              />
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {submissions.slice(0, 3).map((submission) => (
                <Grid item xs={12} md={4} key={submission.id}>
                  <Card>
                    {submission.task.image_url && (
                      <TaskImage src={submission.task.image_url} alt={submission.task.title} maxHeight={140} />
                    )}
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {submission.task.title}
                      </Typography>
                      <Box sx={{ mb: 1 }}>
                        <Chip 
                          size="small"
                          label={submission.status === 'reviewed' ? 'Reviewed' : 'Submitted'} 
                          color={submission.status === 'reviewed' ? 'success' : 'info'}
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Submitted on: {new Date(submission.submitted_at).toLocaleDateString()}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button
                        size="small"
                        component={RouterLink}
                        to={`/submissions/${submission.id}`}
                      >
                        View Details
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
              {submissions.length === 0 && (
                <Grid item xs={12}>
                  <Typography variant="body1" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No submissions yet. Complete your first task!
                  </Typography>
                </Grid>
              )}
            </Grid>
            {submissions.length > 3 && (
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Button variant="text" component={RouterLink} to="/tasks">
                  View All Submissions
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StudentDashboard;