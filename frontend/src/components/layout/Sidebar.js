import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Drawer,
  Box,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
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

// Wider than MUI's usual 240: the account row at the bottom carries a username and an email,
// which wrapped awkwardly at the narrower width.
const drawerWidth = 288;

const Sidebar = ({ open, toggleDrawer, user }) => {
  const isTeacher = user?.role === 'teacher';

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        // Only reserve space while the drawer is actually open. A persistent Drawer slides its
        // paper out of view when closed but its root keeps whatever width it was given, so a
        // fixed width here left an empty gutter down the left of every page with the menu shut.
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        transition: (theme) => theme.transitions.create('width', {
          easing: theme.transitions.easing.sharp,
          duration: theme.transitions.duration.enteringScreen,
        }),
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <Box sx={{ overflow: 'auto', mt: 2, '& .MuiListItemText-primary': { fontSize: '1rem' } }}>
        <Box sx={{ px: 2.5, mb: 2 }}>
          <Typography variant="h6" color="primary">
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
          
          {/* Practice Sessions (Teacher only) - students enter practice contextually, from a
              submission or their dashboard's assigned-practice panel, not a browsable list. */}
          {isTeacher && (
            <ListItem button component={RouterLink} to="/practice-review">
              <ListItemIcon>
                <FitnessCenterIcon />
              </ListItemIcon>
              <ListItemText primary="Practice Sessions" />
            </ListItem>
          )}
        </List>
        
        <Divider sx={{ my: 2 }} />
        
        <List>
          {/* The account row doubles as the way into the profile page - it is where people
              already look for "my account". */}
          <ListItemButton component={RouterLink} to="/profile">
            <ListItemIcon>
              {isTeacher ? <SchoolIcon /> : <PersonIcon />}
            </ListItemIcon>
            <ListItemText
              primary={user?.username || (isTeacher ? 'Teacher Account' : 'Student Account')}
              secondary={isTeacher ? 'Teacher - view profile' : 'Student - view profile'}
              primaryTypographyProps={{ fontWeight: 500 }}
            />
          </ListItemButton>
        </List>
      </Box>
    </Drawer>
  );
};

export default Sidebar;