import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import adminAPI from '../api/admin';
import { authAPI } from '../api/auth';
import { CATEGORIES, LEVELS, getCategoryLabel, getLevelLabel } from '../utils/translations';
import './Dashboard.css';

const currencyFormatter = new Intl.NumberFormat('uk-UA', {
  style: 'currency',
  currency: 'UAH',
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat('uk-UA');

const sortOptions = [
  { value: 'newest', label: 'Найновіші' },
  { value: 'title', label: 'За назвою' },
  { value: 'price_desc', label: 'Ціна ↓' },
  { value: 'price_asc', label: 'Ціна ↑' },
  { value: 'rating', label: 'Рейтинг' },
  { value: 'popularity', label: 'Популярність' },
];

function AdminDashboard() {
  const [user, setUser] = useState(null);
  const [overview, setOverview] = useState(null);
  const [courses, setCourses] = useState([]);
  const [teacherOptions, setTeacherOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    teacherId: '',
    category: 'all',
    level: 'all',
    includeUnpublished: true,
    sortBy: 'newest',
  });
  const [showModal, setShowModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: 0,
    category: 'guitar',
    level: 'beginner',
    teacher_id: '',
  });

  useEffect(() => {
    const init = async () => {
      try {
        const currentUser = await authAPI.getCurrentUser();
        if (currentUser.role !== 'admin') {
          setError('Доступ заборонений. Ця сторінка тільки для адміністраторів.');
          setLoading(false);
          return;
        }
        setUser(currentUser);
        const overviewPromise = fetchOverview();
        const coursesPromise = fetchCourses({
          category: filters.category,
          level: filters.level,
          teacherId: filters.teacherId,
          includeUnpublished: filters.includeUnpublished,
          sortBy: filters.sortBy,
        });
        await Promise.all([overviewPromise, coursesPromise]);
      } catch (err) {
        console.error('Admin dashboard auth error:', err);
        setError('Не вдалося завантажити дані користувача.');
      }
    };
    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!user || user.role !== 'admin') return;
    fetchCourses({
      category: filters.category,
      level: filters.level,
      teacherId: filters.teacherId,
      includeUnpublished: filters.includeUnpublished,
      sortBy: filters.sortBy,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.teacherId, filters.category, filters.level, filters.includeUnpublished, filters.sortBy]);

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const data = await adminAPI.getOverview();
      setOverview(data);
      if (data.teacher_options) {
        setTeacherOptions(data.teacher_options);
        setFormData((prev) => ({
          ...prev,
          teacher_id: prev.teacher_id || (data.teacher_options[0]?.id ?? ''),
        }));
      }
    } catch (err) {
      console.error('Failed to load admin overview:', err);
      setError('Не вдалося завантажити аналітику.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async ({
    category,
    level,
    teacherId,
    includeUnpublished,
    sortBy,
  }) => {
    try {
      setLoading(true);
      const data = await adminAPI.getAllCourses({
        category: category && category !== 'all' ? category : undefined,
        level: level && level !== 'all' ? level : undefined,
        sortBy,
        teacherId: teacherId || undefined,
        includeUnpublished,
      });
      setCourses(data);
    } catch (err) {
      console.error('Failed to load courses:', err);
      setError('Не вдалося завантажити курси.');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    await Promise.all([
      fetchOverview(),
      fetchCourses({
        category: filters.category,
        level: filters.level,
        teacherId: filters.teacherId,
        includeUnpublished: filters.includeUnpublished,
        sortBy: filters.sortBy,
      }),
    ]);
  };

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const openCreateModal = () => {
    setEditingCourse(null);
    setFormData({
      title: '',
      description: '',
      price: 0,
      category: 'guitar',
      level: 'beginner',
      teacher_id: teacherOptions[0]?.id || '',
    });
    setShowModal(true);
  };

  const openEditModal = (course) => {
    setEditingCourse(course);
    setFormData({
      title: course.title,
      description: course.description || '',
      price: course.price,
      category: course.category,
      level: course.level,
      teacher_id: course.teacher?.id || '',
    });
    setShowModal(true);
  };

  const handleModalSubmit = async (e) => {
    e.preventDefault();
    try {
      if (!formData.teacher_id) {
        alert('Оберіть викладача для курсу');
        return;
      }
      if (editingCourse) {
        await adminAPI.updateCourse(editingCourse.id, formData);
      } else {
        await adminAPI.createCourse(formData);
      }
      setShowModal(false);
      setEditingCourse(null);
      await refreshData();
    } catch (err) {
      console.error('Failed to save course:', err);
      alert('Не вдалося зберегти курс. Перевірте заповнені поля.');
    }
  };

  const handleDeleteCourse = async (courseId) => {
    if (!window.confirm('Видалити цей курс?')) return;
    try {
      await adminAPI.deleteCourse(courseId);
      await refreshData();
    } catch (err) {
      console.error('Delete course error:', err);
      alert('Не вдалося видалити курс.');
    }
  };

  const handlePublishToggle = async (courseId, isPublished) => {
    try {
      if (isPublished) {
        await adminAPI.unpublishCourse(courseId);
      } else {
        await adminAPI.publishCourse(courseId);
      }
      await refreshData();
    } catch (err) {
      console.error('Publish toggle error:', err);
      alert('Не вдалося змінити статус курсу.');
    }
  };

  const metricCards = useMemo(() => {
    if (!overview) return [];
    return [
      {
        icon: '💰',
        label: 'Сумарний дохід',
        value: currencyFormatter.format(overview.financials.total_revenue || 0),
      },
      {
        icon: '🧾',
        label: 'Транзакцій',
        value: numberFormatter.format(overview.financials.total_transactions || 0),
      },
      {
        icon: '🎓',
        label: 'Зарахувань',
        value: numberFormatter.format(overview.financials.total_enrollments || 0),
      },
      {
        icon: '📚',
        label: 'Курсів / Опубліковано',
        value: `${overview.metrics.total_courses} / ${overview.metrics.published_courses}`,
      },
      {
        icon: '👩‍🎓',
        label: 'Студентів',
        value: numberFormatter.format(overview.metrics.total_students || 0),
      },
      {
        icon: '👨‍🏫',
        label: 'Викладачів',
        value: numberFormatter.format(overview.metrics.total_teachers || 0),
      },
    ];
  }, [overview]);

  if (loading && !overview && !courses.length) {
    return (
      <div className="dashboard-page">
        <Header />
        <div className="dashboard-loading">Завантаження адмін-панелі...</div>
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
    <div className="dashboard-page admin-dashboard">
      <Header />
      <div className="dashboard-container">
        <div className="dashboard-header">
          <div>
            <h1>Адмін-панель</h1>
            <p>Керуйте курсами, викладачами та фінансами платформи</p>
          </div>
          <div className="admin-actions">
            <button className="btn-primary" onClick={openCreateModal}>
              + Створити курс
            </button>
          </div>
        </div>

        {/* Metrics */}
        <section className="dashboard-section">
          <h2>Ключові показники</h2>
          <div className="stats-grid">
            {metricCards.map((card) => (
              <div key={card.label} className="stat-card">
                <div className="stat-icon">{card.icon}</div>
                <div className="stat-value">{card.value}</div>
                <div className="stat-label">{card.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Popular courses & teachers */}
        <section className="dashboard-section">
          <div className="admin-grid">
            <div>
              <h2>Популярні курси</h2>
              <div className="admin-card-list">
                {overview?.popular_courses?.length ? (
                  overview.popular_courses.map((course) => (
                    <div key={course.id} className="admin-card">
                      <div className="admin-card-header">
                        <div>
                          <h3>{course.title}</h3>
                          <p className="admin-card-subtitle">{course.teacher}</p>
                        </div>
                        <span className="admin-badge">⭐ {course.rating.toFixed(1)}</span>
                      </div>
                      <div className="admin-card-meta">
                        <span>{numberFormatter.format(course.enrollments)} студентів</span>
                        <span>{course.price === 0 ? 'Безкоштовно' : currencyFormatter.format(course.price)}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="muted">Немає даних про популярність</p>
                )}
              </div>
            </div>

            <div>
              <h2>Рейтинг викладачів</h2>
              <div className="admin-card-list">
                {overview?.top_teachers?.length ? (
                  overview.top_teachers.map((teacher) => (
                    <div key={teacher.id} className="admin-card">
                      <div className="admin-card-header">
                        <div>
                          <h3>{teacher.full_name}</h3>
                          <p className="admin-card-subtitle">
                            {teacher.courses} курсів · {teacher.students} студентів
                          </p>
                        </div>
                        <span className="admin-badge">
                          ⭐ {teacher.rating?.toFixed(1) ?? '0.0'} ({teacher.rating_count})
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="muted">Немає даних про викладачів</p>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Course list */}
        <section className="dashboard-section">
          <div className="admin-section-header">
            <div>
              <h2>Всі курси платформи</h2>
              <p>Фільтруйте, редагуйте та публікуйте курси будь-якого викладача</p>
            </div>
            <div className="admin-filters">
              <select
                value={filters.teacherId}
                onChange={(e) => handleFilterChange('teacherId', e.target.value)}
              >
                <option value="">Всі викладачі</option>
                {teacherOptions.map((teacher) => (
                  <option key={teacher.id} value={teacher.id}>
                    {teacher.full_name}
                  </option>
                ))}
              </select>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
              >
                <option value="all">Всі категорії</option>
                {Object.entries(CATEGORIES).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              <select
                value={filters.level}
                onChange={(e) => handleFilterChange('level', e.target.value)}
              >
                <option value="all">Всі рівні</option>
                {Object.entries(LEVELS).map(([key, label]) => (
                  <option key={key} value={key}>
                    {label}
                  </option>
                ))}
              </select>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              <label className="admin-checkbox">
                <input
                  type="checkbox"
                  checked={filters.includeUnpublished}
                  onChange={(e) => handleFilterChange('includeUnpublished', e.target.checked)}
                />
                <span>Показати чернетки</span>
              </label>
            </div>
          </div>

          <div className="admin-table-wrapper">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Назва</th>
                  <th>Викладач</th>
                  <th>Категорія</th>
                  <th>Рівень</th>
                  <th>Ціна</th>
                  <th>Рейтинг</th>
                  <th>Статус</th>
                  <th>Дії</th>
                </tr>
              </thead>
              <tbody>
                {courses.length ? (
                  courses.map((course) => (
                    <tr key={course.id}>
                      <td>
                        <strong>{course.title}</strong>
                        <p className="muted small-text">{course.description || 'Без опису'}</p>
                      </td>
                      <td>{course.teacher?.full_name || '—'}</td>
                      <td>{getCategoryLabel(course.category)}</td>
                      <td>{getLevelLabel(course.level)}</td>
                      <td>{course.price === 0 ? 'Free' : currencyFormatter.format(course.price)}</td>
                      <td>⭐ {course.rating?.toFixed(1) ?? '0.0'}</td>
                      <td>
                        <span className={`course-status ${course.is_published ? 'published' : 'draft'}`}>
                          {course.is_published ? 'Опубліковано' : 'Чернетка'}
                        </span>
                      </td>
                      <td className="admin-table-actions">
                        <Link to={`/course-editor/${course.id}`} className="btn-manage">
                          Модулі та уроки
                        </Link>
                        <button className="btn-edit" onClick={() => openEditModal(course)}>
                          Редагувати курс
                        </button>
                        <button
                          className={course.is_published ? 'btn-unpublish' : 'btn-publish'}
                          onClick={() => handlePublishToggle(course.id, course.is_published)}
                        >
                          {course.is_published ? 'Зняти' : 'Опублікувати'}
                        </button>
                        <button className="btn-delete" onClick={() => handleDeleteCourse(course.id)}>
                          Видалити
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={8} className="muted text-center">
                      Немає курсів за вибраними фільтрами
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>{editingCourse ? 'Редагувати курс' : 'Створити курс'}</h2>
              <button className="modal-close" onClick={() => setShowModal(false)} aria-label="Закрити">
                <span>×</span>
              </button>
            </div>
            <form onSubmit={handleModalSubmit}>
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
                  rows="4"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Ціна (₴)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
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
                      <option key={key} value={key}>
                        {label}
                      </option>
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
                      <option key={key} value={key}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="form-group">
                <label>Викладач</label>
                <select
                  value={formData.teacher_id}
                  onChange={(e) => setFormData({ ...formData, teacher_id: Number(e.target.value) })}
                  required
                >
                  <option value="">Оберіть викладача</option>
                  {teacherOptions.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.full_name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowModal(false)}>
                  Скасувати
                </button>
                <button type="submit" className="btn-submit">
                  {editingCourse ? 'Зберегти' : 'Створити'}
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

export default AdminDashboard;
