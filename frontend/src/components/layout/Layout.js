import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Outlet } from 'react-router-dom';
import { Box, Toolbar, Container } from '@mui/material';
import { logout } from '../../redux/actions/authActions';

import Navbar from './Navbar';
import Sidebar from './Sidebar';
import Alert from '../common/Alert';

const Layout = () => {
  const dispatch = useDispatch();
  const { isAuthenticated, user } = useSelector(state => state.auth);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const toggleDrawer = () => {
    setDrawerOpen(!drawerOpen);
  };

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <Navbar 
        toggleDrawer={toggleDrawer} 
        isAuthenticated={isAuthenticated}
        user={user}
        onLogout={handleLogout}
      />
      
      <Sidebar 
        open={drawerOpen} 
        toggleDrawer={toggleDrawer}
        user={user}
      />
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          height: '100vh',
          overflow: 'auto',
        }}
      >
        <Toolbar />
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Alert />
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
};

export default Layout;