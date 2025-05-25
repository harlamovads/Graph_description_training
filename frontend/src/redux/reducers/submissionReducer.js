// Create file: frontend/src/redux/reducers/submissionReducer.js
import {
  FETCH_SUBMISSIONS_REQUEST,
  FETCH_SUBMISSIONS_SUCCESS,
  FETCH_SUBMISSIONS_FAILURE,
  FETCH_SUBMISSION_REQUEST,
  FETCH_SUBMISSION_SUCCESS,
  FETCH_SUBMISSION_FAILURE,
  CREATE_SUBMISSION_REQUEST,
  CREATE_SUBMISSION_SUCCESS,
  CREATE_SUBMISSION_FAILURE,
  REVIEW_SUBMISSION_REQUEST,
  REVIEW_SUBMISSION_SUCCESS,
  REVIEW_SUBMISSION_FAILURE
} from '../types';

const initialState = {
  submissions: [],
  submission: null,
  loading: false,
  error: null
};

const submissionReducer = (state = initialState, action) => {
  switch (action.type) {
    case FETCH_SUBMISSIONS_REQUEST:
    case FETCH_SUBMISSION_REQUEST:
    case CREATE_SUBMISSION_REQUEST:
    case REVIEW_SUBMISSION_REQUEST:
      return {
        ...state,
        loading: true,
        error: null
      };
    case FETCH_SUBMISSIONS_SUCCESS:
      return {
        ...state,
        submissions: action.payload,
        loading: false,
        error: null
      };
    case FETCH_SUBMISSION_SUCCESS:
      return {
        ...state,
        submission: action.payload,
        loading: false,
        error: null
      };
    case CREATE_SUBMISSION_SUCCESS:
      return {
        ...state,
        submissions: [...state.submissions, action.payload],
        submission: action.payload,
        loading: false,
        error: null
      };
    case REVIEW_SUBMISSION_SUCCESS:
      return {
        ...state,
        submission: action.payload,
        loading: false,
        error: null
      };
    case FETCH_SUBMISSIONS_FAILURE:
    case FETCH_SUBMISSION_FAILURE:
    case CREATE_SUBMISSION_FAILURE:
    case REVIEW_SUBMISSION_FAILURE:
      return {
        ...state,
        loading: false,
        error: action.payload
      };
    default:
      return state;
  }
};

export default submissionReducer;