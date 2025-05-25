import React, { useState, useEffect } from 'react';
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
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AssessmentIcon from '@mui/icons-material/Assessment';

import exerciseService from '../../services/exerciseService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';

const ExerciseList = () => {
  const { user } = useSelector(state => state.auth);
  const isTeacher = user?.role === 'teacher';
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [tabValue, setTabValue] = useState(0);
  
  useEffect(() => {
    const fetchExercises = async () => {
      try {
        setLoading(true);
        
        const response = await exerciseService.getExercises();
        setExercises(response.exercises || []);
        
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load exercises');
        setLoading(false);
      }
    };
    
    fetchExercises();
  }, []);
  
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };
  
  // Filter exercises based on selected tab
  const getFilteredExercises = () => {
    if (isTeacher) {
      // For teachers: All exercises, Created by Me
      if (tabValue === 0) return exercises;
      if (tabValue === 1) return exercises.filter(ex => ex.creator_id === user.id);
    } else {
      // For students: All exercises, Not Attempted, Completed
      if (tabValue === 0) return exercises;
      if (tabValue === 1) return exercises.filter(ex => !(ex.attempts && ex.attempts.length > 0));
      if (tabValue === 2) return exercises.filter(ex => ex.attempts && ex.attempts.length > 0);
    }
    return exercises;
  };
  
  if (loading) {
    return <LoadingSpinner message="Loading exercises..." />;
  }
  
  if (error) {
    return <ErrorBox error={error} />;
  }
  
  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          <FitnessCenterIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
          Exercises
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Practice your writing skills with targeted grammar exercises
        </Typography>
      </Box>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="exercise tabs">
          <Tab label="All Exercises" />
          <Tab label={isTeacher ? "Created by Me" : "Not Attempted"} />
          {!isTeacher && <Tab label="Completed" />}
        </Tabs>
      </Box>
      
      {getFilteredExercises().length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 5 }}>
          <Typography variant="h6" color="text.secondary">
            No exercises found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            {isTeacher 
              ? "Create exercises from student submissions to help them practice." 
              : "Complete writing tasks to generate exercises."}
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {getFilteredExercises().map((exercise) => (
            <Grid item xs={12} sm={6} md={4} key={exercise.id}>
              <Card>
                {exercise.image_url && (
                  <CardMedia
                    component="img"
                    height="140"
                    image={exercise.image_url}
                    alt={exercise.title}
                  />
                )}
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {exercise.title}
                  </Typography>
                  
                  {!isTeacher && exercise.attempts && exercise.attempts.length > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Chip 
                        size="small"
                        label={`Score: ${exercise.attempts[0].score.toFixed(0)}%`}
                        color={exercise.attempts[0].score >= 70 ? 'success' : 'warning'}
                      />
                    </Box>
                  )}
                  
                  <Typography variant="body2" color="text.secondary">
                    {exercise.instructions}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {exercise.sentences ? `${exercise.sentences.length} sentences` : 'No sentences'}
                  </Typography>
                </CardContent>
                <Divider />
                <CardActions>
                  {isTeacher ? (
                    <Button 
                      size="small"
                      startIcon={<AssessmentIcon />}
                      component={RouterLink}
                      to={`/exercises/${exercise.id}/results`}
                    >
                      View Results
                    </Button>
                  ) : exercise.attempts && exercise.attempts.length > 0 ? (
                    <Button 
                      size="small"
                      component={RouterLink}
                      to={`/exercises/${exercise.id}/results`}
                    >
                      View Results
                    </Button>
                  ) : (
                    <Button 
                      size="small"
                      color="primary"
                      startIcon={<PlayArrowIcon />}
                      component={RouterLink}
                      to={`/exercises/${exercise.id}/attempt`}
                    >
                      Start Exercise
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

export default ExerciseList;