import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Toolbar,
  Typography
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssignmentIcon from '@mui/icons-material/Assignment';
import CreateIcon from '@mui/icons-material/Create';
import FitnessCenterIcon from '@mui/icons-material/FitnessCenter';
import PersonIcon from '@mui/icons-material/Person';
import SchoolIcon from '@mui/icons-material/School';

const drawerWidth = 240;

const Sidebar = ({ open, toggleDrawer, user }) => {
  const isTeacher = user?.role === 'teacher';

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto', mt: 2 }}>
        <Box sx={{ px: 2, mb: 2 }}>
          <Typography variant="subtitle1" color="primary">
            {isTeacher ? 'Teacher Portal' : 'Student Portal'}
          </Typography>
        </Box>
        
        <List>
          {/* Dashboard */}
          <ListItem 
            button 
            component={RouterLink} 
            to={isTeacher ? '/dashboard' : '/student-dashboard'}
          >
            <ListItemIcon>
              <DashboardIcon />
            </ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItem>
          
          {/* Tasks */}
          <ListItem button component={RouterLink} to="/tasks">
            <ListItemIcon>
              <AssignmentIcon />
            </ListItemIcon>
            <ListItemText primary="Tasks" />
          </ListItem>
          
          {/* Create Task (Teacher only) */}
          {isTeacher && (
            <ListItem button component={RouterLink} to="/tasks/create">
              <ListItemIcon>
                <CreateIcon />
              </ListItemIcon>
              <ListItemText primary="Create Task" />
            </ListItem>
          )}
          
          {/* Exercises */}
          <ListItem button component={RouterLink} to="/exercises">
            <ListItemIcon>
              <FitnessCenterIcon />
            </ListItemIcon>
            <ListItemText primary="Exercises" />
          </ListItem>
        </List>
        
        <Divider sx={{ my: 2 }} />
        
        <List>
          {/* User Role Indicator */}
          <ListItem>
            <ListItemIcon>
              {isTeacher ? <SchoolIcon /> : <PersonIcon />}
            </ListItemIcon>
            <ListItemText 
              primary={isTeacher ? 'Teacher Account' : 'Student Account'}
              secondary={user?.email}
            />
          </ListItem>
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;