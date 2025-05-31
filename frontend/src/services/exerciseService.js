// frontend/src/services/exerciseService.js
import api from '../utils/api';

const exerciseService = {
  // Generate a new exercise
  generateExercise: async (submissionId, sentence, imageUrl) => {
    const response = await api.post('/exercises/generate', {
      submission_id: submissionId,
      sentence,
      image_url: imageUrl
    });
    
    return response.data;
  },
  
  // Get all exercises for the user
  getExercises: async () => {
    const response = await api.get('/exercises');
    return response.data;
  },
  
  // Get a specific exercise
  getExercise: async (exerciseId) => {
    const response = await api.get(`/exercises/${exerciseId}`);
    return response.data;
  },
  
  // Submit an exercise attempt
  submitAttempt: async (exerciseId, responses) => {
    const response = await api.post(`/exercises/${exerciseId}/attempt`, {
      responses
    });
    
    return response.data;
  },
  
  // Get attempts for an exercise
  getExerciseAttempts: async (exerciseId) => {
    const response = await api.get(`/exercises/${exerciseId}/attempts`);
    return response.data;
  },

  // Get sentences from the database
  getSentenceDatabase: async (errorType) => {
    const params = errorType ? { error_type: errorType } : {};
    const response = await api.get('/exercises/sentence-database', { params });
    return response.data;
  },

  // Get sentence database status
  getSentenceDatabaseStatus: async () => {
    const response = await api.get('/exercises/sentence-database/status');
    return response.data;
  },

  // Publish a draft exercise
  publishExercise: async (exerciseId) => {
    const response = await api.post(`/exercises/${exerciseId}/publish`);
    return response.data;
  },

  // Update an exercise
  updateExercise: async (exerciseId, exerciseData) => {
    const response = await api.put(`/exercises/${exerciseId}/update`, exerciseData);
    return response.data;
  }
};

export default exerciseService;