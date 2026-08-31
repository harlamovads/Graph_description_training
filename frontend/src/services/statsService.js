import api from '../utils/api';

const statsService = {
  // Summary stats for every student belonging to the current teacher
  getStudentsSummary: async () => {
    const response = await api.get('/stats/students');
    return response.data;
  },

  // Detailed stats for one student: time per task/exercise, attempts, error distribution
  getStudentDetail: async (studentId) => {
    const response = await api.get(`/stats/students/${studentId}`);
    return response.data;
  }
};

export default statsService;
