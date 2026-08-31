import { configureStore } from '@reduxjs/toolkit';
import authReducer from './reducers/authReducer';
import taskReducer from './reducers/taskReducer';
import submissionReducer from './reducers/submissionReducer';
import uiReducer from './reducers/uiReducer';

const store = configureStore({
  reducer: {
    auth: authReducer,
    tasks: taskReducer,
    submissions: submissionReducer,
    ui: uiReducer
  }
});

export default store;