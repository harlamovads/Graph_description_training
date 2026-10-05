import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, TextField, Alert
} from '@mui/material';

import { setAlert } from '../../redux/actions/uiActions';
import authService from '../../services/authService';

/** Lets any signed-in user change their own password (current password required). */
const ChangePasswordDialog = ({ open, onClose }) => {
  const dispatch = useDispatch();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const reset = () => {
    setCurrent(''); setNext(''); setConfirm(''); setError(null); setSaving(false);
  };

  const close = () => { reset(); onClose(); };

  const submit = async () => {
    setError(null);
    if (next.length < 8) {
      setError('New password must be at least 8 characters long.');
      return;
    }
    if (next !== confirm) {
      setError('The two new passwords do not match.');
      return;
    }
    try {
      setSaving(true);
      await authService.changePassword(current, next);
      dispatch(setAlert('Password changed successfully', 'success'));
      close();
    } catch (err) {
      setError(err.response?.data?.error || 'Could not change your password.');
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={close} maxWidth="xs" fullWidth>
      <DialogTitle>Change password</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          fullWidth margin="dense" type="password" label="Current password"
          value={current} onChange={(e) => setCurrent(e.target.value)}
        />
        <TextField
          fullWidth margin="dense" type="password" label="New password"
          value={next} onChange={(e) => setNext(e.target.value)}
          helperText="At least 8 characters"
        />
        <TextField
          fullWidth margin="dense" type="password" label="Repeat new password"
          value={confirm} onChange={(e) => setConfirm(e.target.value)}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={close} disabled={saving}>Cancel</Button>
        <Button
          variant="contained"
          onClick={submit}
          disabled={saving || !current || !next || !confirm}
        >
          {saving ? 'Saving...' : 'Change password'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ChangePasswordDialog;
