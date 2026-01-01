/**
 * API client for students endpoints
 */
import api from './auth';

const studentsAPI = {
  /**
   * Get all enrollments for the current student
   * @returns {Promise} API response with enrollments list
   */
  getEnrollments: async () => {
    const response = await api.get('/students/enrollments');
    return response.data;
  },

  /**
   * Get enrollment for a specific course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response with enrollment
   */
  getEnrollment: async (courseId) => {
    const response = await api.get(`/students/enrollments/${courseId}`);
    return response.data;
  },

  /**
   * Enroll in a course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response with enrollment
   */
  enrollInCourse: async (courseId) => {
    const response = await api.post(`/students/enroll/${courseId}`);
    return response.data;
  },

  /**
   * Get learning progress statistics
   * @returns {Promise} API response with progress stats
   */
  getProgress: async () => {
    const response = await api.get('/students/progress');
    return response.data;
  },
};

export default studentsAPI;

