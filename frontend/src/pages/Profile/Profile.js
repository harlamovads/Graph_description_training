import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Divider,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Chip,
  Grid,
  Alert,
  TextField,
  MenuItem,
  Snackbar
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SchoolIcon from '@mui/icons-material/School';
import LockResetIcon from '@mui/icons-material/LockReset';
import BarChartIcon from '@mui/icons-material/BarChart';
import SaveIcon from '@mui/icons-material/Save';

import authService from '../../services/authService';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorBox from '../../components/common/ErrorBox';
import ChangePasswordDialog from '../../components/common/ChangePasswordDialog';

// Fixed choices, so the study can group by this. Leaving it as "Not specified" is always
// available, which is how someone declines to answer.
const GENDER_OPTIONS = ['Female', 'Male'];

// CEFR, plus an honest escape hatch - a student who has never been assessed shouldn't guess.
const ENGLISH_LEVELS = [
  { value: 'A1', label: 'A1 - Beginner' },
  { value: 'A2', label: 'A2 - Elementary' },
  { value: 'B1', label: 'B1 - Intermediate' },
  { value: 'B2', label: 'B2 - Upper-intermediate' },
  { value: 'C1', label: 'C1 - Advanced' },
  { value: 'C2', label: 'C2 - Proficient' },
  { value: 'Not sure', label: "Not sure" }
];

const Profile = () => {
  const { user } = useSelector((state) => state.auth);
  const isTeacher = user?.role === 'teacher';

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profile, setProfile] = useState(null);
  const [passwordDialog, setPasswordDialog] = useState(false);
  const [background, setBackground] = useState({
    age: '', gender: '', native_language: '', english_level: ''
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await authService.getProfile();
        setProfile(data);
        setBackground({
          age: data?.user?.age ?? '',
          gender: data?.user?.gender ?? '',
          native_language: data?.user?.native_language ?? '',
          english_level: data?.user?.english_level ?? ''
        });
        setLoading(false);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load your profile');
        setLoading(false);
      }
    };
    load();
  }, []);

  const saveBackground = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      // Empty strings are sent as null, which is how the backend clears a field - otherwise
      // there would be no way to undo an answer once given.
      const response = await authService.updateProfile({
        age: background.age === '' ? null : background.age,
        gender: background.gender || null,
        native_language: background.native_language || null,
        english_level: background.english_level || null
      });
      setProfile({ ...profile, user: response.user });
      setSaved(true);
    } catch (err) {
      setSaveError(err.response?.data?.error || 'Could not save your details');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner message="Loading profile..." />;
  if (error) return <ErrorBox error={error} />;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Profile</Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              {isTeacher ? <SchoolIcon color="primary" /> : <PersonIcon color="primary" />}
              <Typography variant="h6">{profile?.user?.username}</Typography>
            </Box>
            <Typography variant="body2" color="text.secondary">
              {profile?.user?.email}
            </Typography>
            <Chip
              size="small"
              sx={{ mt: 1 }}
              label={isTeacher ? 'Teacher account' : 'Student account'}
              color={isTeacher ? 'primary' : 'default'}
              variant="outlined"
            />

            {isTeacher && profile?.invitation_code && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>Your invitation code</Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Share this with your students - it is permanent and works for any number of them.
                </Typography>
                <Typography variant="h6" sx={{ fontFamily: 'monospace', mt: 1 }}>
                  {profile.invitation_code}
                </Typography>
              </>
            )}

            {!isTeacher && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2" gutterBottom>Your teacher</Typography>
                {profile?.teacher ? (
                  <>
                    <Typography variant="body1">{profile.teacher.username}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {profile.teacher.email}
                    </Typography>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    You are not linked to a teacher through an invitation code.
                  </Typography>
                )}
              </>
            )}

            <Divider sx={{ my: 2 }} />
            <Button
              variant="outlined"
              startIcon={<LockResetIcon />}
              onClick={() => setPasswordDialog(true)}
            >
              Change password
            </Button>
          </Paper>
        </Grid>

        {isTeacher && (
          <Grid item xs={12} md={7}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                My students ({profile?.students?.length || 0})
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Open a student to see their statistics, error breakdown and past submitted work.
              </Typography>
              <Divider sx={{ mb: 1 }} />

              {profile?.students?.length ? (
                <List dense>
                  {profile.students.map((student) => (
                    <ListItemButton
                      key={student.id}
                      component={RouterLink}
                      // The statistics page opens on this student directly; it also still works
                      // on its own from the dashboard.
                      to={`/stats?student=${student.id}`}
                    >
                      <ListItemIcon><BarChartIcon fontSize="small" /></ListItemIcon>
                      <ListItemText primary={student.username} secondary={student.email} />
                    </ListItemButton>
                  ))}
                </List>
              ) : (
                <List dense>
                  <ListItem>
                    <ListItemText
                      secondary="No students yet - share your invitation code to get started."
                    />
                  </ListItem>
                </List>
              )}
            </Paper>
          </Grid>
        )}

        {!isTeacher && (
          <Grid item xs={12} md={7}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>About you</Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                All of this is optional, and none of it affects your tasks or feedback. It helps
                us understand the results of the study.
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {saveError && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSaveError(null)}>
                  {saveError}
                </Alert>
              )}

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Age"
                    type="number"
                    inputProps={{ min: 5, max: 120 }}
                    value={background.age}
                    onChange={(e) => setBackground({ ...background, age: e.target.value })}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="Gender"
                    value={background.gender}
                    onChange={(e) => setBackground({ ...background, gender: e.target.value })}
                  >
                    <MenuItem value=""><em>Not specified</em></MenuItem>
                    {GENDER_OPTIONS.map((option) => (
                      <MenuItem key={option} value={option}>{option}</MenuItem>
                    ))}
                  </TextField>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Native language"
                    value={background.native_language}
                    onChange={(e) =>
                      setBackground({ ...background, native_language: e.target.value })}
                  />
                </Grid>

                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="English level"
                    value={background.english_level}
                    onChange={(e) =>
                      setBackground({ ...background, english_level: e.target.value })}
                  >
                    <MenuItem value=""><em>Not specified</em></MenuItem>
                    {ENGLISH_LEVELS.map((level) => (
                      <MenuItem key={level.value} value={level.value}>{level.label}</MenuItem>
                    ))}
                  </TextField>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={saving}
                  onClick={saveBackground}
                >
                  {saving ? 'Saving...' : 'Save details'}
                </Button>
              </Box>
            </Paper>
          </Grid>
        )}
      </Grid>

      {!isTeacher && (
        <Alert severity="info" sx={{ mt: 3 }}>
          Your tasks, feedback and practice sessions live on your dashboard.
        </Alert>
      )}

      <Snackbar
        open={saved}
        autoHideDuration={3000}
        onClose={() => setSaved(false)}
        message="Your details were saved"
      />

      <ChangePasswordDialog open={passwordDialog} onClose={() => setPasswordDialog(false)} />
    </Box>
  );
};

export default Profile;
