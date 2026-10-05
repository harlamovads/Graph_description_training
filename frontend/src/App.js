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
import TeacherStats from './pages/Dashboard/TeacherStats';

// Task Pages
import TaskList from './pages/Tasks/TaskList';
import TaskCreate from './pages/Tasks/TaskCreate';
import TaskEdit from './pages/Tasks/TaskEdit';
import Profile from './pages/Profile/Profile';
import PracticeCompose from './pages/Practice/PracticeCompose';
import TaskDetails from './pages/Tasks/TaskDetails';

// Submission Pages
import SubmissionCreate from './pages/Submissions/SubmissionCreate';
import SubmissionDetails from './pages/Submissions/SubmissionDetails';
import SubmissionReview from './pages/Submissions/SubmissionReview';

// Practice Pages
import PracticeSession from './pages/Practice/PracticeSession';
import { PracticeSessionList, PracticeSessionDetail } from './pages/Practice/TeacherPracticeReview';

// Where each role's home lives. Both the index route and ProtectedRoute's role-mismatch
// redirect go through this: sending everyone to /dashboard (which is teacher-only) meant a
// logged-in student bounced / -> /dashboard -> / -> ... forever. Firefox rate-limits that many
// history calls and throws "The operation is insecure", which kills the render and leaves a
// blank page. Falling back to /login when there's no user keeps any future gap from looping.
const homePathFor = (user) => {
  if (!user) return '/login';
  return user.role === 'teacher' ? '/dashboard' : '/student-dashboard';
};

const HomeRedirect = () => {
  const { user } = useSelector(state => state.auth);
  return <Navigate to={homePathFor(user)} replace />;
};

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
    return <Navigate to="/login" replace />;
  }

  if (role && user.role !== role) {
    return <Navigate to={homePathFor(user)} replace />;
  }

  return children;
};

function App() {
  const dispatch = useDispatch();
  // `checking` (not `loading`) gates the initial render: it starts true and only flips once
  // checkAuth() has resolved either way (see authReducer's initialState). Gating on `loading`
  // instead - as this used to - let the very first render happen with the reducer's initial
  // isAuthenticated:false before checkAuth() (fired from the effect below, so necessarily
  // after that first render) had a chance to run. On any hard reload/deep link other than
  // /dashboard or /student-dashboard, that made ProtectedRoute redirect to /login for one
  // frame, which then bounced the user to their dashboard once auth actually resolved -
  // silently discarding whatever page they'd asked for.
  const { checking } = useSelector(state => state.auth);

  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

  if (checking) {
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
              <HomeRedirect />
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
        <Route
          path="stats"
          element={
            <ProtectedRoute role="teacher">
              <TeacherStats />
            </ProtectedRoute>
          }
        />

        <Route
          path="profile"
          element={
            <ProtectedRoute>
              <Profile />
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
        <Route
          path="tasks/:id/edit"
          element={
            <ProtectedRoute role="teacher">
              <TaskEdit />
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
        
        {/* Practice Routes */}
        <Route
          path="practice/new"
          element={
            <ProtectedRoute role="student">
              <PracticeCompose />
            </ProtectedRoute>
          }
        />
        <Route
          path="practice/:sessionId"
          element={
            <ProtectedRoute role="student">
              <PracticeSession />
            </ProtectedRoute>
          }
        />
        <Route
          path="practice-review"
          element={
            <ProtectedRoute role="teacher">
              <PracticeSessionList />
            </ProtectedRoute>
          }
        />
        <Route
          path="practice-review/:sessionId"
          element={
            <ProtectedRoute role="teacher">
              <PracticeSessionDetail />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;