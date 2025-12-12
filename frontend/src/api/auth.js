/**
 * API client for authentication endpoints
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('Auth API: Adding token to request:', config.url, 'Token:', token.substring(0, 20) + '...');
    } else {
      console.log('Auth API: No token found for request:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export const authAPI = {
  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @param {string} role - User role ('student' or 'teacher')
   * @returns {Promise} API response
   */
  register: async (userData, role = 'student') => {
    const response = await api.post(`/auth/register?role=${role}`, userData);
    return response.data;
  },

  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} API response with token
   */
  login: async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      console.log('Auth API: Token saved to localStorage:', response.data.access_token.substring(0, 20) + '...');
    } else {
      console.error('Auth API: No access_token in response:', response.data);
    }
    
    return response.data;
  },

  /**
   * Get current user info
   * @returns {Promise} Current user data
   */
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  /**
   * Logout user (clear token)
   */
  logout: () => {
    localStorage.removeItem('access_token');
  },

  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('access_token');
  },
};

export default api;

