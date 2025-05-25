// Create file: frontend/src/redux/reducers/uiReducer.js
import { SET_ALERT, CLEAR_ALERT, START_LOADING, STOP_LOADING } from '../types';

const initialState = {
  alert: null,
  loading: false
};

const uiReducer = (state = initialState, action) => {
  switch (action.type) {
    case SET_ALERT:
      return {
        ...state,
        alert: action.payload
      };
    case CLEAR_ALERT:
      return {
        ...state,
        alert: null
      };
    case START_LOADING:
      return {
        ...state,
        loading: true
      };
    case STOP_LOADING:
      return {
        ...state,
        loading: false
      };
    default:
      return state;
  }
};

export default uiReducer;