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

  /**
   * Generate completion certificate for enrollment
   * @param {number} enrollmentId - Enrollment ID
   * @returns {Promise} Certificate data
   */
  generateCertificate: async (enrollmentId) => {
    const response = await api.post(`/students/enrollments/${enrollmentId}/certificate`);
    return response.data;
  },

  /**
   * Download certificate PDF (returns axios response with blob data)
   * @param {string} certificateId - Certificate ID
   * @returns {Promise} Axios response
   */
  downloadCertificate: async (certificateId) => {
    return api.get(`/students/certificates/${certificateId}/download`, {
      responseType: 'blob',
    });
  },

  /**
   * Complete a lesson
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} API response with updated enrollment
   */
  completeLesson: async (lessonId) => {
    const response = await api.post(`/students/lessons/${lessonId}/complete`);
    return response.data;
  },

  /**
   * Reset lesson completion to retake it
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} API response with updated enrollment
   */
  resetLesson: async (lessonId) => {
    const response = await api.post(`/students/lessons/${lessonId}/reset`);
    return response.data;
  },

  /**
   * Complete a module
   * @param {number} moduleId - Module ID
   * @returns {Promise} API response with updated enrollment
   */
  completeModule: async (moduleId) => {
    const response = await api.post(`/students/modules/${moduleId}/complete`);
    return response.data;
  },

  /**
   * Complete a course
   * @param {number} courseId - Course ID
   * @returns {Promise} API response with updated enrollment
   */
  completeCourse: async (courseId) => {
    const response = await api.post(`/students/courses/${courseId}/complete`);
    return response.data;
  },

  /**
   * Get lesson details (for enrolled students)
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} API response with lesson details
   */
  getLesson: async (lessonId) => {
    const response = await api.get(`/students/lessons/${lessonId}`);
    return response.data;
  },

  /**
   * Get quiz for a lesson (for enrolled students)
   * @param {number} quizId - Quiz ID
   * @returns {Promise} API response with quiz data (without correct answers)
   */
  getQuiz: async (quizId) => {
    const response = await api.get(`/students/quizzes/${quizId}`);
    return response.data;
  },

  /**
   * Submit quiz answers
   * @param {number} quizId - Quiz ID
   * @param {Object} data - Quiz submission data {answers: {questionId: optionIndex}}
   * @returns {Promise} API response with quiz attempt results
   */
  submitQuiz: async (quizId, data) => {
    const response = await api.post(`/students/quizzes/${quizId}/submit`, data);
    return response.data;
  },

  /**
   * Submit or update course rating
   * @param {number} courseId
   * @param {Object} payload { rating: number, comment?: string }
   */
  rateCourse: async (courseId, payload) => {
    const response = await api.post(`/students/courses/${courseId}/rating`, payload);
    return response.data;
  },

  /**
   * Submit or update teacher rating for a course
   * @param {number} courseId
   * @param {Object} payload { rating: number }
   */
  rateTeacher: async (courseId, payload) => {
    const response = await api.post(
      `/students/courses/${courseId}/teacher-rating`,
      payload
    );
    return response.data;
  },
};

export default studentsAPI;

