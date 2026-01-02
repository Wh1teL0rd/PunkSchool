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

  /**
   * Get course details with modules and lessons
   * @param {number} courseId - Course ID
   * @returns {Promise} API response with course details
   */
  getCourseDetails: async (courseId) => {
    const response = await api.get(`/courses/${courseId}`);
    return response.data;
  },

  /**
   * Add a module to a course
   * @param {number} courseId - Course ID
   * @param {Object} moduleData - Module data {title, order}
   * @returns {Promise} API response with created module
   */
  addModule: async (courseId, moduleData) => {
    const response = await api.post(`/courses/${courseId}/modules`, moduleData);
    return response.data;
  },

  /**
   * Update a module
   * @param {number} moduleId - Module ID
   * @param {string} title - New title
   * @returns {Promise} API response with updated module
   */
  updateModule: async (moduleId, title) => {
    const response = await api.put(`/courses/modules/${moduleId}?title=${encodeURIComponent(title)}`);
    return response.data;
  },

  /**
   * Delete a module
   * @param {number} moduleId - Module ID
   * @returns {Promise} API response
   */
  deleteModule: async (moduleId) => {
    const response = await api.delete(`/courses/modules/${moduleId}`);
    return response.data;
  },

  /**
   * Add a lesson to a module
   * @param {number} moduleId - Module ID
   * @param {Object} lessonData - Lesson data
   * @returns {Promise} API response with created lesson
   */
  addLesson: async (moduleId, lessonData) => {
    const response = await api.post(`/courses/modules/${moduleId}/lessons`, lessonData);
    return response.data;
  },

  /**
   * Update a lesson
   * @param {number} lessonId - Lesson ID
   * @param {Object} lessonData - Lesson data
   * @returns {Promise} API response with updated lesson
   */
  updateLesson: async (lessonId, lessonData) => {
    const response = await api.put(`/courses/lessons/${lessonId}`, lessonData);
    return response.data;
  },

  /**
   * Delete a lesson
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} API response
   */
  deleteLesson: async (lessonId) => {
    const response = await api.delete(`/courses/lessons/${lessonId}`);
    return response.data;
  },

  /**
   * Get quiz for a lesson
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} API response with quiz data
   */
  getQuiz: async (lessonId) => {
    const response = await api.get(`/courses/lessons/${lessonId}/quiz`);
    return response.data;
  },

  /**
   * Add a quiz to a lesson
   * @param {number} lessonId - Lesson ID
   * @param {Object} quizData - Quiz data {title, passing_score, questions}
   * @returns {Promise} API response with created quiz
   */
  addQuiz: async (lessonId, quizData) => {
    const response = await api.post(`/courses/lessons/${lessonId}/quiz`, quizData);
    return response.data;
  },

  /**
   * Update quiz for a lesson
   * @param {number} lessonId - Lesson ID
   * @param {Object} quizData - Quiz data {title, passing_score, questions}
   * @returns {Promise} API response with updated quiz
   */
  updateQuiz: async (lessonId, quizData) => {
    const response = await api.put(`/courses/lessons/${lessonId}/quiz`, quizData);
    return response.data;
  },

  /**
   * Get lesson details (for teacher)
   * @param {number} lessonId - Lesson ID
   * @returns {Promise} Lesson details with full information
   */
  getLessonDetails: async (lessonId) => {
    const response = await api.get(`/courses/lessons/${lessonId}`);
    return response.data;
  },
};

export default teachersAPI;

