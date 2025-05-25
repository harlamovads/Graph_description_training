import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Routes, Route, Navigate } from 'react-router-dom';
import { checkAuth } from './redux/actions/authActions';
import { CircularProgress, Box } from '@mui/material';

// Layout
import Layout from './components/layout/Layout';

// Auth Pages
import Login from './pages/Auth/Login';
import Register from './pages/Auth/Register';

// Dashboard Pages
import TeacherDashboard from './pages/Dashboard/TeacherDashboard';
import StudentDashboard from './pages/Dashboard/StudentDashboard';

// Task Pages
import TaskList from './pages/Tasks/TaskList';
import TaskCreate from './pages/Tasks/TaskCreate';
import TaskDetails from './pages/Tasks/TaskDetails';

// Submission Pages
import SubmissionCreate from './pages/Submissions/SubmissionCreate';
import SubmissionDetails from './pages/Submissions/SubmissionDetails';
import SubmissionReview from './pages/Submissions/SubmissionReview';

// Exercise Pages
import ExerciseList from './pages/Exercises/ExerciseList';
import ExerciseCreate from './pages/Exercises/ExerciseCreate';
import ExerciseAttempt from './pages/Exercises/ExerciseAttempt';
import ExerciseResults from './pages/Exercises/ExerciseResults';
import ExercisePreview from './pages/Exercises/ExercisePreview';

// Protected Route Component
const ProtectedRoute = ({ children, role }) => {
  const { isAuthenticated, user, loading } = useSelector(state => state.auth);
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (role && user.role !== role) {
    return <Navigate to="/" />;
  }
  
  return children;
};

function App() {
  const dispatch = useDispatch();
  const { loading } = useSelector(state => state.auth);
  
  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }
  
  return (
    <Routes>
      {/* Auth Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Routes */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        {/* Dashboard Routes */}
        <Route 
          path="" 
          element={
            <ProtectedRoute>
              <Navigate to="/dashboard" />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="dashboard" 
          element={
            <ProtectedRoute role="teacher">
              <TeacherDashboard />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="student-dashboard" 
          element={
            <ProtectedRoute role="student">
              <StudentDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Task Routes */}
        <Route 
          path="tasks" 
          element={
            <ProtectedRoute>
              <TaskList />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="tasks/create" 
          element={
            <ProtectedRoute role="teacher">
              <TaskCreate />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="tasks/:id" 
          element={
            <ProtectedRoute>
              <TaskDetails />
            </ProtectedRoute>
          } 
        />
        
        {/* Submission Routes */}
        <Route 
          path="submissions/:id/create" 
          element={
            <ProtectedRoute role="student">
              <SubmissionCreate />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="submissions/:id" 
          element={
            <ProtectedRoute>
              <SubmissionDetails />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="submissions/:id/review" 
          element={
            <ProtectedRoute role="teacher">
              <SubmissionReview />
            </ProtectedRoute>
          } 
        />
        
        {/* Exercise Routes */}
        <Route 
          path="exercises" 
          element={
            <ProtectedRoute>
              <ExerciseList />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="exercises/create/:submissionId" 
          element={
            <ProtectedRoute>
              <ExerciseCreate />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="exercises/:id/attempt" 
          element={
            <ProtectedRoute role="student">
              <ExerciseAttempt />
            </ProtectedRoute>
          } 
        />
        <Route 
          path="exercises/:id/results" 
          element={
            <ProtectedRoute>
              <ExerciseResults />
            </ProtectedRoute>
          } 
        />
      </Route>
      <Route 
        path="exercises/:id/preview" 
        element={
          <ProtectedRoute role="teacher">
            <ExercisePreview />
          </ProtectedRoute>
        } 
        />
      
      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

export default App;