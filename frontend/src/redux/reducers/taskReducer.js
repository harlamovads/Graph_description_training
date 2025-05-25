// Create file: frontend/src/redux/reducers/taskReducer.js
import {
  FETCH_TASKS_REQUEST,
  FETCH_TASKS_SUCCESS,
  FETCH_TASKS_FAILURE,
  FETCH_TASK_REQUEST,
  FETCH_TASK_SUCCESS,
  FETCH_TASK_FAILURE,
  CREATE_TASK_REQUEST,
  CREATE_TASK_SUCCESS,
  CREATE_TASK_FAILURE,
  ASSIGN_TASK_REQUEST,
  ASSIGN_TASK_SUCCESS,
  ASSIGN_TASK_FAILURE
} from '../types';

const initialState = {
  tasks: [],
  task: null,
  loading: false,
  error: null
};

const taskReducer = (state = initialState, action) => {
  switch (action.type) {
    case FETCH_TASKS_REQUEST:
    case FETCH_TASK_REQUEST:
    case CREATE_TASK_REQUEST:
    case ASSIGN_TASK_REQUEST:
      return {
        ...state,
        loading: true,
        error: null
      };
    case FETCH_TASKS_SUCCESS:
      return {
        ...state,
        tasks: action.payload,
        loading: false,
        error: null
      };
    case FETCH_TASK_SUCCESS:
      return {
        ...state,
        task: action.payload,
        loading: false,
        error: null
      };
    case CREATE_TASK_SUCCESS:
      return {
        ...state,
        tasks: [...state.tasks, action.payload],
        loading: false,
        error: null
      };
    case ASSIGN_TASK_SUCCESS:
      return {
        ...state,
        loading: false,
        error: null
      };
    case FETCH_TASKS_FAILURE:
    case FETCH_TASK_FAILURE:
    case CREATE_TASK_FAILURE:
    case ASSIGN_TASK_FAILURE:
      return {
        ...state,
        loading: false,
        error: action.payload
      };
    default:
      return state;
  }
};

export default taskReducer;