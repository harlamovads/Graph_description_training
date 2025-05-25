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

const initialState = {
  isAuthenticated: false,
  user: null,
  loading: false,
  error: null,
  checking: true
};

const authReducer = (state = initialState, action) => {
  switch (action.type) {
    case LOGIN_REQUEST:
    case REGISTER_REQUEST:
    case AUTH_CHECK:
      return {
        ...state,
        loading: true,
        error: null
      };
    case LOGIN_SUCCESS:
    case REGISTER_SUCCESS:
    case AUTH_SUCCESS:
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        loading: false,
        checking: false,
        error: null
      };
    case LOGIN_FAILURE:
    case REGISTER_FAILURE:
    case AUTH_FAILURE:
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        checking: false,
        error: action.payload
      };
    case LOGOUT:
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        checking: false,
        error: null
      };
    default:
      return state;
  }
};

export default authReducer;