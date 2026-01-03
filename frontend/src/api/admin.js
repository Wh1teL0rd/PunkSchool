import api from './auth';

const adminAPI = {
  getOverview: async () => {
    const response = await api.get('/analytics/admin/overview');
    return response.data;
  },

  getAllCourses: async ({
    category,
    level,
    sortBy = 'newest',
    teacherId,
    includeUnpublished = true,
  } = {}) => {
    const params = new URLSearchParams();
    if (category && category !== 'all') {
      params.append('category', category);
    }
    if (level && level !== 'all') {
      params.append('level', level);
    }
    if (teacherId) {
      params.append('teacher_id', teacherId);
    }
    if (sortBy) {
      params.append('sort_by', sortBy);
    }
    params.append('include_unpublished', includeUnpublished ? 'true' : 'false');
    const query = params.toString();
    const response = await api.get(`/courses/admin/all${query ? `?${query}` : ''}`);
    return response.data;
  },

  createCourse: async (courseData) => {
    const response = await api.post('/courses', courseData);
    return response.data;
  },

  updateCourse: async (courseId, courseData) => {
    const response = await api.put(`/courses/${courseId}`, courseData);
    return response.data;
  },

  deleteCourse: async (courseId) => {
    const response = await api.delete(`/courses/${courseId}`);
    return response.data;
  },

  publishCourse: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/publish`);
    return response.data;
  },

  unpublishCourse: async (courseId) => {
    const response = await api.post(`/courses/${courseId}/unpublish`);
    return response.data;
  },

  getUsers: async (role) => {
    const params = role ? `?role=${role}` : '';
    const response = await api.get(`/admin/users${params}`);
    return response.data;
  },

  deleteUser: async (userId) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },

  updateUserBalance: async (userId, balance) => {
    const response = await api.put(`/admin/users/${userId}/balance`, { balance });
    return response.data;
  },
};

export default adminAPI;
