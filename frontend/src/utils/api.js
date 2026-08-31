import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
// frontend/src/utils/api.js
// Update the request interceptor

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    
    if (token) {
      // Make sure the format matches what the backend expects
      config.headers['Authorization'] = `Bearer ${token}`;
      console.log(`Adding token to request: ${config.url} - Token: ${token.substring(0, 15)}...`);
    } else {
      console.log('No token available for request:', config.url);
    }
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Handle token expiration: try a silent refresh once before forcing a re-login, so a
// 1-hour access token doesn't throw the user back to /login while a valid refresh_token
// is sitting unused in localStorage.
let refreshPromise = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url?.includes('/auth/refresh') &&
      !originalRequest.url?.includes('/auth/login')
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          if (!refreshPromise) {
            refreshPromise = axios.post('/api/auth/refresh', {}, {
              headers: { Authorization: `Bearer ${refreshToken}` }
            }).finally(() => { refreshPromise = null; });
          }
          const { data } = await refreshPromise;
          localStorage.setItem('token', data.access_token);
          originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh token is invalid/expired too - fall through to logout below.
        }
      }

      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;