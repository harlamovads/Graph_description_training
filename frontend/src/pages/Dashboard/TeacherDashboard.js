import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import SchoolIcon from '@mui/icons-material/School';
import AssignmentIcon from '@mui/icons-material/Assignment';
import GradingIcon from '@mui/icons-material/Grading';
import InsightsIcon from '@mui/icons-material/Insights';

import { setAlert } from '../../redux/actions/uiActions';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import taskService from '../../services/taskService';
import submissionService from '../../services/submissionService';
import authService from '../../services/authService';
import practiceService from '../../services/practiceService';

const ONE_WEEK_MS = 7 * 24 * 60 * 60 * 1000;

const TeacherDashboard = () => {
  const dispatch = useDispatch();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [pendingSubmissions, setPendingSubmissions] = useState([]);
  const [invitationDialog, setInvitationDialog] = useState(false);
  const [invitationCode, setInvitationCode] = useState('');
  const [practiceSessionsThisWeek, setPracticeSessionsThisWeek] = useState(0);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch tasks
        const tasksResponse = await taskService.getTasks();
        setTasks(tasksResponse.tasks || []);

        // Fetch submissions
        const submissionsResponse = await submissionService.getTeacherSubmissions();
        setSubmissions(submissionsResponse.submissions || []);

        // Filter pending submissions (not reviewed)
        setPendingSubmissions(
          (submissionsResponse.submissions || []).filter(
            submission => submission.status === 'submitted'
          )
        );

        // Practice sessions are surfaced far less prominently than reviews below - just a
        // small count/link, so a lightweight count is all this page needs.
        const practiceResponse = await practiceService.getTeacherSessions();
        const cutoff = Date.now() - ONE_WEEK_MS;
        setPracticeSessionsThisWeek(
          (practiceResponse.sessions || []).filter(
            s => s.started_at && new Date(s.started_at).getTime() >= cutoff
          ).length
        );

        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load dashboard data');
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);
  
  const generateInvitation = async () => {
    try {
      setLoading(true);
      const response = await authService.generateInvitation();
      setInvitationCode(response.code);
      setInvitationDialog(true);
      setLoading(false);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to generate invitation code');
      setLoading(false);
    }
  };
  
  const handleCloseDialog = () => {
    setInvitationDialog(false);
  };
  
  const copyInvitationCode = () => {
    navigator.clipboard.writeText(invitationCode);
    dispatch(setAlert('Invitation code copied to clipboard', 'success'));
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
        Teacher Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Quick Actions */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                component={RouterLink}
                to="/tasks/create"
                fullWidth
              >
                Create New Task
              </Button>
              <Button
                variant="outlined"
                startIcon={<SchoolIcon />}
                onClick={generateInvitation}
                fullWidth
              >
                Generate Invitation Code
              </Button>
              <Button
                variant="outlined"
                startIcon={<InsightsIcon />}
                component={RouterLink}
                to="/stats"
                fullWidth
              >
                Student Stats
              </Button>
            </Box>
          </Paper>
        </Grid>
        
        {/* Pending Reviews */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Pending Reviews
            </Typography>
            <Divider sx={{ mb: 2 }} />
            {pendingSubmissions.length > 0 ? (
              <List>
                {pendingSubmissions.slice(0, 5).map((submission) => (
                  <ListItem
                    key={submission.id}
                    divider
                    secondaryAction={
                      <Button
                        variant="outlined"
                        size="small"
                        component={RouterLink}
                        to={`/submissions/${submission.id}/review`}
                      >
                        Review
                      </Button>
                    }
                  >
                    <ListItemText
                      primary={submission.task.title}
                      secondary={`Submitted by ${submission.student.username} on ${new Date(submission.submitted_at).toLocaleDateString()}`}
                    />
                  </ListItem>
                ))}
                {pendingSubmissions.length > 5 && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">
                      {pendingSubmissions.length - 5} more pending submissions
                    </Typography>
                  </Box>
                )}
              </List>
            ) : (
              <Typography variant="body1" color="text.secondary" sx={{ py: 4, textAlign: 'center' }}>
                No pending submissions to review
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Tasks Overview */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <AssignmentIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Recent Tasks
              </Typography>
              <Button 
                variant="text" 
                size="small"
                component={RouterLink}
                to="/tasks"
              >
                View All
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              {tasks.slice(0, 4).map((task) => (
                <Grid item xs={12} sm={6} key={task.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {task.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {task.description}
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button 
                        size="small" 
                        component={RouterLink}
                        to={`/tasks/${task.id}`}
                      >
                        View Details
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
              {tasks.length === 0 && (
                <Grid item xs={12}>
                  <Typography variant="body1" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                    No tasks created yet
                  </Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>
        
        {/* Submission Stats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                <GradingIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
                Submission Statistics
              </Typography>
              <Chip 
                label={`${submissions.length} Total`} 
                color="primary" 
                variant="outlined" 
              />
            </Box>
            <Divider sx={{ mb: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Paper elevation={0} sx={{ p: 2, bgcolor: '#f0f7ff', textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {pendingSubmissions.length}
                  </Typography>
                  <Typography variant="body2">Pending Review</Typography>
                </Paper>
              </Grid>
              <Grid item xs={6}>
                <Paper elevation={0} sx={{ p: 2, bgcolor: '#f0fff4', textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {submissions.filter(s => s.status === 'reviewed').length}
                  </Typography>
                  <Typography variant="body2">Reviewed</Typography>
                </Paper>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Practice sessions are intentionally understated here - a plain text link, not a
          card - since they matter far less than the reviews above. */}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Button
          variant="text"
          size="small"
          color="inherit"
          component={RouterLink}
          to="/practice-review"
          sx={{ color: 'text.secondary' }}
        >
          {practiceSessionsThisWeek} practice session{practiceSessionsThisWeek === 1 ? '' : 's'} this week &rarr;
        </Button>
      </Box>

      {/* Invitation Code Dialog */}
      <Dialog
        open={invitationDialog}
        onClose={handleCloseDialog}
      >
        <DialogTitle>Invitation Code Generated</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Share this code with your students to invite them to your class:
          </DialogContentText>
          <Paper
            elevation={0}
            sx={{
              p: 2,
              mt: 2,
              bgcolor: '#f0f7ff',
              textAlign: 'center',
              fontFamily: 'monospace',
              fontSize: '1.5rem',
              letterSpacing: '0.1em'
            }}
          >
            {invitationCode}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Close</Button>
          <Button variant="contained" onClick={copyInvitationCode}>
            Copy Code
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TeacherDashboard;