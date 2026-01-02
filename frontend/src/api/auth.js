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
  timeout: 10000, // 10 секунд timeout для всіх запитів
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
   * Check if backend is available
   * @returns {Promise<boolean>} True if backend is reachable
   */
  checkBackendHealth: async () => {
    try {
      // Health endpoint знаходиться на кореневому шляху, не під /api
      const healthUrl = API_BASE_URL.replace('/api', '') + '/health';
      const response = await axios.get(healthUrl, { timeout: 3000 });
      return response.status === 200;
    } catch (error) {
      console.error('Backend health check failed:', error);
      return false;
    }
  },

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
    
    try {
      console.log('Auth API: Attempting login to:', API_BASE_URL + '/auth/login');
      console.log('Auth API: Request data:', { username: email, password: '***' });
      
      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        timeout: 15000, // 15 секунд timeout для логіну
      });
      
      console.log('Auth API: Login response received:', response.status, response.data);
      
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        console.log('Auth API: Token saved to localStorage:', response.data.access_token.substring(0, 20) + '...');
      } else {
        console.error('Auth API: No access_token in response:', response.data);
        throw new Error('No access token received from server');
      }
      
      return response.data;
    } catch (error) {
      console.error('Auth API: Login error details:', {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status,
        config: {
          url: error.config?.url,
          baseURL: error.config?.baseURL,
          method: error.config?.method,
        }
      });
      
      // Більш детальна обробка помилок
      if (error.code === 'ECONNABORTED') {
        throw new Error('Час очікування вичерпано. Перевірте, чи запущений бекенд сервер на http://localhost:8000');
      } else if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        throw new Error('Не вдалося підключитися до сервера. Перевірте, чи запущений бекенд на http://localhost:8000');
      } else if (error.response) {
        // Сервер відповів, але з помилкою
        const detail = error.response.data?.detail || error.response.data?.message || 'Помилка входу';
        throw new Error(detail);
      } else {
        // Інша помилка
        throw new Error(error.message || 'Помилка входу. Спробуйте пізніше.');
      }
    }
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

