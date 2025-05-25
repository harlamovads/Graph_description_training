import React from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Snackbar, Alert as MuiAlert } from '@mui/material';
import { clearAlert } from '../../redux/actions/uiActions';

const Alert = () => {
  const dispatch = useDispatch();
  const { alert } = useSelector(state => state.ui);

  const handleClose = (event, reason) => {
    if (reason === 'clickaway') {
      return;
    }

    dispatch(clearAlert());
  };

  return (
    <Snackbar
      open={Boolean(alert)}
      autoHideDuration={6000}
      onClose={handleClose}
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      {alert && (
        <MuiAlert
          elevation={6}
          variant="filled"
          onClose={handleClose}
          severity={alert.type}
        >
          {alert.message}
        </MuiAlert>
      )}
    </Snackbar>
  );
};

export default Alert;