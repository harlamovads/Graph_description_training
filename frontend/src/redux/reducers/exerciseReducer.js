// Create file: frontend/src/redux/reducers/exerciseReducer.js
import {
  FETCH_EXERCISES_REQUEST,
  FETCH_EXERCISES_SUCCESS,
  FETCH_EXERCISES_FAILURE,
  FETCH_EXERCISE_REQUEST,
  FETCH_EXERCISE_SUCCESS,
  FETCH_EXERCISE_FAILURE,
  CREATE_EXERCISE_REQUEST,
  CREATE_EXERCISE_SUCCESS,
  CREATE_EXERCISE_FAILURE,
  SUBMIT_EXERCISE_ATTEMPT_REQUEST,
  SUBMIT_EXERCISE_ATTEMPT_SUCCESS,
  SUBMIT_EXERCISE_ATTEMPT_FAILURE,
  FETCH_EXERCISE_ATTEMPTS_REQUEST,
  FETCH_EXERCISE_ATTEMPTS_SUCCESS,
  FETCH_EXERCISE_ATTEMPTS_FAILURE
} from '../types';

const initialState = {
  exercises: [],
  exercise: null,
  attempts: [],
  loading: false,
  error: null
};

const exerciseReducer = (state = initialState, action) => {
  switch (action.type) {
    case FETCH_EXERCISES_REQUEST:
    case FETCH_EXERCISE_REQUEST:
    case CREATE_EXERCISE_REQUEST:
    case SUBMIT_EXERCISE_ATTEMPT_REQUEST:
    case FETCH_EXERCISE_ATTEMPTS_REQUEST:
      return {
        ...state,
        loading: true,
        error: null
      };
    case FETCH_EXERCISES_SUCCESS:
      return {
        ...state,
        exercises: action.payload,
        loading: false,
        error: null
      };
    case FETCH_EXERCISE_SUCCESS:
      return {
        ...state,
        exercise: action.payload,
        loading: false,
        error: null
      };
    case CREATE_EXERCISE_SUCCESS:
      return {
        ...state,
        exercises: [...state.exercises, action.payload],
        exercise: action.payload,
        loading: false,
        error: null
      };
    case SUBMIT_EXERCISE_ATTEMPT_SUCCESS:
      return {
        ...state,
        attempts: [...state.attempts, action.payload],
        loading: false,
        error: null
      };
    case FETCH_EXERCISE_ATTEMPTS_SUCCESS:
      return {
        ...state,
        attempts: action.payload,
        loading: false,
        error: null
      };
    case FETCH_EXERCISES_FAILURE:
    case FETCH_EXERCISE_FAILURE:
    case CREATE_EXERCISE_FAILURE:
    case SUBMIT_EXERCISE_ATTEMPT_FAILURE:
    case FETCH_EXERCISE_ATTEMPTS_FAILURE:
      return {
        ...state,
        loading: false,
        error: action.payload
      };
    default:
      return state;
  }
};

export default exerciseReducer;