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

  regenerateInvitation: async () => {
    const response = await api.post('/auth/regenerate-invitation');
    return response.data;
  },

  // Teacher resets a student's password; the temporary one comes back once, in the response.
  resetStudentPassword: async (studentId) => {
    const response = await api.post(`/auth/students/${studentId}/reset-password`);
    return response.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return response.data;
  },

  // Profile page data: a teacher's students and invitation code, or a student's teacher.
  getProfile: async () => {
    const response = await api.get('/auth/profile');
    return response.data;
  },

  // A student saving their own background (age, gender, native language, English level).
  updateProfile: async (fields) => {
    const response = await api.put('/auth/profile', fields);
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