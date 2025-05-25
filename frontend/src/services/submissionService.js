import api from '../utils/api';

const submissionService = {
  // Create a new submission
  createSubmission: async (submissionData) => {
    const response = await api.post('/submissions', submissionData);
    return response.data;
  },
  
  // Get a specific submission
  getSubmission: async (submissionId) => {
    const response = await api.get(`/submissions/${submissionId}`);
    return response.data;
  },
  
  // Get submissions for a teacher
  getTeacherSubmissions: async () => {
    const response = await api.get('/submissions/teacher');
    return response.data;
  },
  
  // Get submissions for a student
  getStudentSubmissions: async () => {
    const response = await api.get('/submissions/student');
    return response.data;
  },
  
  // Review a submission (teacher only)
  reviewSubmission: async (submissionId, feedback) => {
    const response = await api.post(`/submissions/${submissionId}/review`, {
      feedback
    });
    
    return response.data;
  }
};

export default submissionService;