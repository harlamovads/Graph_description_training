import api from '../utils/api';

const authService = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  getStudents: async () => {
  const response = await api.get('/auth/students');
  return response.data;
  },
  
  getUser: async () => {
    const response = await api.get('/auth/user');
    return response.data;
  },

  generateInvitation: async () => {
    const response = await api.post('/auth/generate-invitation');
    return response.data;
  }
};

export default authService;