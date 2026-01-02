/**
 * API client for courses endpoints
 */
import api from './auth';

const coursesAPI = {
  /**
   * Get all courses with optional filters
   * @param {Object} filters - Filter options
   * @param {string} filters.category - Course category (guitar, drums, vocals, keyboards, theory)
   * @param {string} filters.level - Difficulty level (beginner, intermediate, advanced, master)
   * @param {number} filters.min_price - Minimum price
   * @param {number} filters.max_price - Maximum price
   * @param {string} filters.teacher_search - Search by teacher name or email
   * @param {string} filters.sort_by - Sort option (price_asc, price_desc, rating, popularity, newest, title)
   * @returns {Promise} API response with courses list
   */
  getCourses: async (filters = {}) => {
    const params = new URLSearchParams();
    
    if (filters.category) params.append('category', filters.category);
    if (filters.level) params.append('level', filters.level);
    if (filters.min_price !== undefined) params.append('min_price', filters.min_price);
    if (filters.max_price !== undefined) params.append('max_price', filters.max_price);
    if (filters.teacher_search) params.append('teacher_search', filters.teacher_search);
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    
    const queryString = params.toString();
    const url = queryString ? `/courses?${queryString}` : '/courses';
    
    const response = await api.get(url);
    return response.data;
  },

  /**
   * Search courses by keyword
   * @param {string} keyword - Search keyword
   * @returns {Promise} API response with courses list
   */
  searchCourses: async (keyword) => {
    const response = await api.get(`/courses/search?q=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  /**
   * Get course details by ID
   * @param {number} courseId - Course ID
   * @returns {Promise} API response with course details
   */
  getCourseDetails: async (courseId) => {
    const response = await api.get(`/courses/${courseId}`);
    return response.data;
  },
};

export default coursesAPI;

