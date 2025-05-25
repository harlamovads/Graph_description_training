import {
  LOGIN_REQUEST,
  LOGIN_SUCCESS,
  LOGIN_FAILURE,
  REGISTER_REQUEST,
  REGISTER_SUCCESS,
  REGISTER_FAILURE,
  LOGOUT,
  AUTH_CHECK,
  AUTH_SUCCESS,
  AUTH_FAILURE
} from '../types';
import authService from '../../services/authService';
import { setAlert } from './uiActions';

// Login action
export const login = (credentials) => async (dispatch) => {
  dispatch({ type: LOGIN_REQUEST });
  
  try {
    const response = await authService.login(credentials);
    
    // Important: Make sure we're storing the correct token format
    localStorage.setItem('token', response.access_token);
    // Also store the refresh token
    localStorage.setItem('refresh_token', response.refresh_token);
    
    console.log('Login successful, tokens stored');
    
    dispatch({
      type: LOGIN_SUCCESS,
      payload: response.user
    });
    
    dispatch(setAlert('Login successful', 'success'));
  } catch (error) {
    console.error('Login error:', error);
    
    dispatch({
      type: LOGIN_FAILURE,
      payload: error.response ? error.response.data.error : 'Login failed'
    });
    
    dispatch(setAlert(error.response ? error.response.data.error : 'Login failed', 'error'));
  }
};

// Register action
export const register = (userData) => async (dispatch) => {
  dispatch({ type: REGISTER_REQUEST });
  
  try {
    const response = await authService.register(userData);
    
    localStorage.setItem('token', response.access_token);
    
    dispatch({
      type: REGISTER_SUCCESS,
      payload: response.user
    });
    
    dispatch(setAlert('Registration successful', 'success'));
  } catch (error) {
    dispatch({
      type: REGISTER_FAILURE,
      payload: error.response ? error.response.data.error : 'Registration failed'
    });
    
    dispatch(setAlert(error.response ? error.response.data.error : 'Registration failed', 'error'));
  }
};

// Logout action
export const logout = () => (dispatch) => {
  localStorage.removeItem('token');
  
  dispatch({ type: LOGOUT });
  
  dispatch(setAlert('Logged out successfully', 'success'));
};

// Check auth status action
export const checkAuth = () => async (dispatch) => {
  const token = localStorage.getItem('token');
  
  if (!token) {
    dispatch({ type: AUTH_FAILURE });
    return;
  }
  
  dispatch({ type: AUTH_CHECK });
  
  try {
    const response = await authService.getUser();
    
    dispatch({
      type: AUTH_SUCCESS,
      payload: response
    });
  } catch (error) {
    localStorage.removeItem('token');
    
    dispatch({
      type: AUTH_FAILURE,
      payload: 'Authentication failed'
    });
  }
};