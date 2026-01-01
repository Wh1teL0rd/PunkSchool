/**
 * API client for teachers endpoints
 */
import api from './auth';

const teachersAPI = {
  /**
   * Get all courses created by the current teacher
   * @returns {Promise} API response with courses list
   */
  getMyCourses: async () => {
    const response = await api.get('/courses/my/teaching');
    return response.data;
  },

  /**
   * Create a new course
   * @param {Object} courseData - Course data
   * @returns {Promise} API response with created course
   */
  createCourse: async (courseData) => {
    const response = await api.post('/courses', courseData);
    return response.data;
  },

  /**
   * Update a course
   * @param {number} courseId - Course ID
   * @param {Object} courseData - Course data to update
   * @returns {Promise} API response with updated course
   */
  updateCourse: async (courseId, courseData) => {
    const response = await api.put(`/courses/${courseId}`, courseData);
    return response.data;
  },

  /**
   * Delete a course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response
   */
  deleteCourse: async (courseId) => {
    const response = await api.delete(`/courses/${courseId}`);
    return response.data;
  },

  /**
   * Publish a course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response
   */
  publishCourse: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/publish`);
    return response.data;
  },

  /**
   * Unpublish a course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response
   */
  unpublishCourse: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/unpublish`);
    return response.data;
  },

  /**
   * Get teacher revenue statistics
   * @param {number} days - Number of days to look back (default: 30)
   * @returns {Promise} API response with revenue stats
   */
  getRevenue: async (days = 30) => {
    const response = await api.get(`/analytics/teacher/revenue?days=${days}`);
    return response.data;
  },

  /**
   * Get course popularity statistics
   * @returns {Promise} API response with popularity stats
   */
  getCoursePopularity: async () => {
    const response = await api.get('/analytics/courses/popularity');
    return response.data;
  },
};

export default teachersAPI;

