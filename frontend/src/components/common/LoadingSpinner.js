// frontend/src/components/common/LoadingSpinner.js
import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

const LoadingSpinner = ({ message = 'Loading...', variant = 'default' }) => {
  const getIcon = () => {
    switch (variant) {
      case 'analysis':
        return '🧠';
      case 'database':
        return '📚';
      case 'exercise':
        return '💪';
      case 'neural':
        return '🤖';
      default:
        return '⏳';
    }
  };

  const getColor = () => {
    switch (variant) {
      case 'analysis':
        return 'secondary';
      case 'database':
        return 'primary';
      case 'exercise':
        return 'success';
      case 'neural':
        return 'info';
      default:
        return 'primary';
    }
  };

  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      minHeight="200px"
    >
      <CircularProgress 
        size={60} 
        thickness={4} 
        color={getColor()}
      />
      <Typography variant="h6" sx={{ mt: 2 }}>
        {getIcon()} {message}
      </Typography>
    </Box>
  );
};

export default LoadingSpinner;