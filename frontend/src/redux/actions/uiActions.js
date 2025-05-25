// Create file: frontend/src/redux/actions/uiActions.js
import { SET_ALERT, CLEAR_ALERT, START_LOADING, STOP_LOADING } from '../types';

// Set alert action
export const setAlert = (message, type) => (dispatch) => {
  dispatch({
    type: SET_ALERT,
    payload: { message, type }
  });
  
  // Auto clear after 5 seconds
  setTimeout(() => dispatch(clearAlert()), 5000);
};

// Clear alert action
export const clearAlert = () => ({
  type: CLEAR_ALERT
});

// Start loading action
export const startLoading = () => ({
  type: START_LOADING
});

// Stop loading action
export const stopLoading = () => ({
  type: STOP_LOADING
});