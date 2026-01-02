import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import teachersAPI from '../api/teachers';
import { authAPI } from '../api/auth';
import './Dashboard.css';

import { getCategoryLabel, getLevelLabel, CATEGORIES, LEVELS } from '../utils/translations';

function TeacherDashboard() {
  const [courses, setCourses] = useState([]);
  const [revenue, setRevenue] = useState(null);
  const [popularity, setPopularity] = useState(null);
  const [teacherProfile, setTeacherProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: 0,
    category: 'guitar',
    level: 'beginner',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [coursesData, revenueData, popularityData, profileData] = await Promise.all([
        teachersAPI.getMyCourses(),
        teachersAPI.getRevenue(30),
        teachersAPI.getCoursePopularity(),
        authAPI.getCurrentUser(),
      ]);

      setCourses(coursesData);
      setRevenue(revenueData);
      setPopularity(popularityData);
      setTeacherProfile(profileData);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Не вдалося завантажити дані. Спробуйте пізніше.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    try {
      await teachersAPI.createCourse(formData);
      setShowCreateModal(false);
      setFormData({
        title: '',
        description: '',
        price: 0,
        category: 'guitar',
        level: 'beginner',
      });
      fetchData();
    } catch (err) {
      console.error('Error creating course:', err);
      alert('Не вдалося створити курс');
    }
  };

  const handleUpdateCourse = async (e) => {
    e.preventDefault();
    try {
      await teachersAPI.updateCourse(editingCourse.id, formData);
      setShowCreateModal(false);
      setEditingCourse(null);
      setFormData({
        title: '',
        description: '',
        price: 0,
        category: 'guitar',
        level: 'beginner',
      });
      fetchData();
    } catch (err) {
      console.error('Error updating course:', err);
      alert('Не вдалося оновити курс');
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цей курс?')) {
      return;
    }
    try {
      await teachersAPI.deleteCourse(courseId);
      fetchData();
    } catch (err) {
      console.error('Error deleting course:', err);
      alert('Не вдалося видалити курс');
    }
  };

  const handlePublishToggle = async (courseId, isPublished) => {
    try {
      if (isPublished) {
        await teachersAPI.unpublishCourse(courseId);
      } else {
        await teachersAPI.publishCourse(courseId);
      }
      fetchData();
    } catch (err) {
      console.error('Error toggling publish status:', err);
      alert('Не вдалося змінити статус публікації');
    }
  };

  const openEditModal = (course) => {
    setEditingCourse(course);
    setFormData({
      title: course.title,
      description: course.description || '',
      price: course.price,
      category: course.category,
      level: course.level,
    });
    setShowCreateModal(true);
  };

  if (loading) {
    return (
      <div className="dashboard-page">
        <Header />
        <div className="dashboard-loading">Завантаження...</div>
        <Footer />
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-page">
        <Header />
        <div className="dashboard-error">{error}</div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      <Header />
      
      <div className="dashboard-container">
        <div className="dashboard-header">
          <h1>Кабінет викладача</h1>
          <button
            onClick={() => {
              setEditingCourse(null);
              setFormData({
                title: '',
                description: '',
                price: 0,
                category: 'guitar',
                level: 'beginner',
              });
              setShowCreateModal(true);
            }}
            className="btn-create-course"
          >
            + Створити курс
          </button>
        </div>

        {/* Statistics */}
        <section className="dashboard-section">
          <h2>Статистика</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📚</div>
              <div className="stat-value">{courses.length}</div>
              <div className="stat-label">Всього курсів</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">✅</div>
              <div className="stat-value">{courses.filter(c => c.is_published).length}</div>
              <div className="stat-label">Опубліковано</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <div className="stat-value">{revenue?.total_revenue || 0} ₴</div>
              <div className="stat-label">Дохід (30 днів)</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">👥</div>
              <div className="stat-value">{revenue?.total_students || 0}</div>
              <div className="stat-label">Студентів</div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">⭐</div>
              <div className="stat-value">
                {teacherProfile?.rating !== undefined
                  ? teacherProfile.rating.toFixed(1)
                  : '0.0'}
              </div>
              <div className="stat-label">
                Середній рейтинг
                {teacherProfile?.rating_count
                  ? ` (${teacherProfile.rating_count})`
                  : ''}
              </div>
            </div>
          </div>
        </section>

        {/* Course Management */}
        <section className="dashboard-section">
          <h2>Мої курси</h2>
          {courses.length === 0 ? (
            <div className="empty-state">
              <p>Ви ще не створили жодного курсу</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-primary"
              >
                Створити перший курс
              </button>
            </div>
          ) : (
            <div className="courses-list">
              {courses.map((course) => (
                <div key={course.id} className="course-management-card">
                  <div className="course-management-header">
                    <h3>{course.title}</h3>
                    <span className={`course-status ${course.is_published ? 'published' : 'draft'}`}>
                      {course.is_published ? 'Опубліковано' : 'Чернетка'}
                    </span>
                  </div>
                  <div className="course-management-info">
                    <p>{course.description || 'Без опису'}</p>
                    <div className="course-management-meta">
                      <span>{CATEGORIES[course.category] || course.category}</span>
                      <span>{LEVELS[course.level] || course.level}</span>
                      <span>⭐ {course.rating.toFixed(1)}</span>
                      <span>{course.price === 0 ? 'Безкоштовно' : `${course.price} ₴`}</span>
                    </div>
                  </div>
                  <div className="course-management-actions">
                    <Link
                      to={`/course-editor/${course.id}`}
                      className="btn-edit"
                      style={{ textDecoration: 'none', display: 'inline-block' }}
                    >
                      Управління курсом
                    </Link>
                    <button
                      onClick={() => openEditModal(course)}
                      className="btn-edit"
                    >
                      Редагувати
                    </button>
                    <button
                      onClick={() => handlePublishToggle(course.id, course.is_published)}
                      className={course.is_published ? 'btn-unpublish' : 'btn-publish'}
                    >
                      {course.is_published ? 'Зняти з публікації' : 'Опублікувати'}
                    </button>
                    <button
                      onClick={() => handleDeleteCourse(course.id)}
                      className="btn-delete"
                    >
                      Видалити
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Student Success Statistics */}
        {popularity && (
          <section className="dashboard-section">
            <h2>Статистика успішності студентів</h2>
            <div className="popularity-stats">
              <p>Загальна статистика популярності курсів на платформі</p>
              {/* Тут можна додати більше деталей статистики */}
            </div>
          </section>
        )}
      </div>

      {/* Create/Edit Course Modal */}
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>{editingCourse ? 'Редагувати курс' : 'Створити курс'}</h2>
              <button
                className="modal-close"
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingCourse(null);
                }}
                aria-label="Закрити"
              >
                <span>×</span>
              </button>
            </div>
            <form onSubmit={editingCourse ? handleUpdateCourse : handleCreateCourse}>
              <div className="form-group">
                <label>Назва курсу</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Опис</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows="4"
                />
              </div>
              <div className="form-group">
                <label>Ціна (₴)</label>
                <input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                  min="0"
                  step="0.01"
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Категорія</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    required
                  >
                    {Object.entries(CATEGORIES).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Рівень</label>
                  <select
                    value={formData.level}
                    onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                    required
                  >
                    {Object.entries(LEVELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-cancel">
                  Скасувати
                </button>
                <button type="submit" className="btn-submit">
                  {editingCourse ? 'Зберегти зміни' : 'Створити курс'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

export default TeacherDashboard;

