import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const ErrorBox = ({ error }) => {
  return (
    <Paper
      elevation={3}
      sx={{
        padding: 3,
        backgroundColor: '#fff8f8',
        borderLeft: '5px solid #f44336',
        mb: 3
      }}
    >
      <Typography variant="h6" color="error" gutterBottom>
        Error
      </Typography>
      <Typography variant="body1">
        {error || 'An unexpected error occurred. Please try again later.'}
      </Typography>
    </Paper>
  );
};

export default ErrorBox;