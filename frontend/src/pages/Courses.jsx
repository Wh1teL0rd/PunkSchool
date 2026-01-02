import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import coursesAPI from '../api/courses';
import studentsAPI from '../api/students';
import { authAPI } from '../api/auth';
import { CATEGORIES, LEVELS } from '../utils/translations';
import './Courses.css';

function Courses() {
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [user, setUser] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [enrollingCourseId, setEnrollingCourseId] = useState(null);
  
  // Filters
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedLevel, setSelectedLevel] = useState('');
  const [teacherSearch, setTeacherSearch] = useState('');
  const [sortBy, setSortBy] = useState('newest');
  
  // Course preview
  const [previewCourse, setPreviewCourse] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // Filters modal
  const [showFiltersModal, setShowFiltersModal] = useState(false);

  // Завантажуємо курси та дані користувача
  useEffect(() => {
    fetchCourses();
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    if (authAPI.isAuthenticated()) {
      try {
        const userData = await authAPI.getCurrentUser();
        setUser(userData);
        // Завантажуємо enrollments для студентів
        if (userData.role === 'student') {
          try {
            const enrollmentsData = await studentsAPI.getEnrollments();
            setEnrollments(enrollmentsData);
          } catch (err) {
            console.error('Error fetching enrollments:', err);
          }
        }
      } catch (err) {
        console.error('Error fetching user data:', err);
      }
    }
  };

  const fetchCourses = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters = {
        category: selectedCategory || undefined,
        level: selectedLevel || undefined,
        teacher_search: teacherSearch.trim() || undefined,
        sort_by: sortBy,
      };
      
      const coursesData = await coursesAPI.getCourses(filters);
      setCourses(coursesData);
    } catch (err) {
      console.error('Error fetching courses:', err);
      setError('Не вдалося завантажити курси. Спробуйте пізніше.');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyFilters = () => {
    fetchCourses();
    setShowFiltersModal(false);
  };

  const handlePreviewCourse = async (courseId) => {
    try {
      const courseDetails = await coursesAPI.getCourseDetails(courseId);
      setPreviewCourse(courseDetails);
      setShowPreview(true);
    } catch (err) {
      console.error('Error fetching course details:', err);
      alert('Не вдалося завантажити деталі курсу');
    }
  };

  const clearFilters = async () => {
    setSelectedCategory('');
    setSelectedLevel('');
    setTeacherSearch('');
    setSortBy('newest');
    // Застосовуємо фільтри після очищення
    setLoading(true);
    setError(null);
    try {
      const filters = {
        category: undefined,
        level: undefined,
        teacher_search: undefined,
        sort_by: 'newest',
      };
      const coursesData = await coursesAPI.getCourses(filters);
      setCourses(coursesData);
    } catch (err) {
      console.error('Error fetching courses:', err);
      setError('Не вдалося завантажити курси. Спробуйте пізніше.');
    } finally {
      setLoading(false);
    }
  };

  const hasActiveFilters = selectedCategory || selectedLevel || teacherSearch.trim();

  const isEnrolled = (courseId) => {
    return enrollments.some(e => e.course?.id === courseId);
  };

  const handleEnroll = async (courseId) => {
    if (!user) {
      navigate('/login');
      return;
    }

    if (user.role !== 'student') {
      alert('Тільки студенти можуть записуватись на курси');
      return;
    }

    if (isEnrolled(courseId)) {
      navigate(`/course-learning/${courseId}`);
      return;
    }

    setEnrollingCourseId(courseId);
    try {
      await studentsAPI.enrollInCourse(courseId);
      alert('Успішно записано на курс!');
      // Оновлюємо дані
      await fetchUserData();
      await fetchCourses();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Не вдалося записатись на курс';
      alert(errorMessage);
    } finally {
      setEnrollingCourseId(null);
    }
  };

  const renderCourseActions = (course) => {
    const previewButton = (
      <button
        onClick={() => handlePreviewCourse(course.id)}
        className="btn-secondary"
      >
        Переглянути програму
      </button>
    );

    if (user && user.role === 'student') {
      if (isEnrolled(course.id)) {
        return (
          <>
            <button
              onClick={() => navigate(`/course-learning/${course.id}`)}
              className="btn-preview"
            >
              Продовжити навчання
            </button>
            {previewButton}
          </>
        );
      }
      return (
        <>
          <button
            onClick={() => handleEnroll(course.id)}
            className="btn-preview"
            disabled={enrollingCourseId === course.id}
          >
            {enrollingCourseId === course.id
              ? 'Записуємось...'
              : course.price === 0
              ? 'Записатись безкоштовно'
              : `Записатись за ${course.price} ₴`}
          </button>
          {previewButton}
        </>
      );
    }

    return previewButton;
  };

  return (
    <div className="courses-page">
      <Header />
      <div className="courses-header">
        <h1>Каталог курсів</h1>
        <p>Оберіть курс, який вас цікавить</p>
      </div>

      <div className="courses-container">
        {/* Courses List */}
        <main className="courses-main">
          <div className="courses-actions">
            <button
              onClick={() => setShowFiltersModal(true)}
              className="filters-button"
            >
              🔍 Фільтри
              {hasActiveFilters && <span className="filter-badge"></span>}
            </button>
          </div>
          {loading ? (
            <div className="loading">Завантаження курсів...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : courses.length === 0 ? (
            <div className="no-courses">
              <p>Курси не знайдено</p>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="clear-filters-button">
                  Очистити фільтри
                </button>
              )}
            </div>
          ) : (
            <>
              <div className="courses-count">
                Знайдено курсів: {courses.length}
              </div>
              <div className="courses-grid">
                {courses.map((course) => (
                  <div key={course.id} className="course-card">
                    <div className="course-header">
                      <h3>{course.title}</h3>
                      <span className="course-category">
                        {CATEGORIES[course.category] || course.category}
                      </span>
                    </div>
                    
                    {course.teacher && (
                      <div className="course-teacher">
                        <strong>Викладач:</strong> {course.teacher.full_name || course.teacher.email}
                      </div>
                    )}
                    
                    <div className="course-meta">
                      <span className="course-level">
                        {LEVELS[course.level] || course.level}
                      </span>
                      <span className="course-rating">
                        ⭐ {course.rating.toFixed(1)}
                      </span>
                    </div>
                    
                    <div className="course-price">
                      {course.price === 0 ? (
                        <span className="price-free">Безкоштовно</span>
                      ) : (
                        <span className="price-amount">{course.price} ₴</span>
                      )}
                    </div>
                    
                    <div className="course-actions">
                      {renderCourseActions(course)}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </main>
      </div>

      {/* Course Preview Modal */}
      {showPreview && previewCourse && (
        <div className="preview-modal-overlay">
          <div className="preview-modal">
            <button
              className="preview-close"
              onClick={() => setShowPreview(false)}
              aria-label="Закрити"
            >
              <span>×</span>
            </button>
            
            <div className="preview-header">
              <h2>{previewCourse.title}</h2>
              <div className="preview-meta">
                <span>{CATEGORIES[previewCourse.category]}</span>
                <span>{LEVELS[previewCourse.level]}</span>
                <span>⭐ {previewCourse.rating.toFixed(1)}</span>
              </div>
            </div>
            
            {previewCourse.description && (
              <div className="preview-description">
                <h3>Опис</h3>
                <p>{previewCourse.description}</p>
              </div>
            )}
            
            {previewCourse.teacher && (
              <div className="preview-teacher">
                <h3>Викладач</h3>
                <p>{previewCourse.teacher.full_name || previewCourse.teacher.email}</p>
              </div>
            )}
            
            <div className="preview-stats">
              <div className="stat-item">
                <strong>Уроків:</strong> {previewCourse.total_lessons || 0}
              </div>
              <div className="stat-item">
                <strong>Тривалість:</strong> {previewCourse.total_duration || 0} хв
              </div>
              <div className="stat-item">
                <strong>Ціна:</strong> {previewCourse.price === 0 ? 'Безкоштовно' : `${previewCourse.price} ₴`}
              </div>
            </div>
            
            {previewCourse.modules && previewCourse.modules.length > 0 && (
              <div className="preview-program">
                <h3>Програма курсу</h3>
                <div className="modules-list">
                  {previewCourse.modules.map((module, moduleIndex) => (
                    <div key={module.id} className="module-item">
                      <div className="module-header">
                        <span className="module-number">{moduleIndex + 1}</span>
                        <h4>{module.title}</h4>
                      </div>
                      {module.lessons && module.lessons.length > 0 && (
                        <ul className="lessons-list">
                          {module.lessons.map((lesson, lessonIndex) => (
                            <li key={lesson.id} className="lesson-item">
                              <span className="lesson-number">
                                {moduleIndex + 1}.{lessonIndex + 1}
                              </span>
                              <span className="lesson-title">{lesson.title}</span>
                              {lesson.duration_minutes > 0 && (
                                <span className="lesson-duration">
                                  {lesson.duration_minutes} хв
                                </span>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Filters Modal */}
      {showFiltersModal && (
        <div className="filters-modal-overlay">
          <div className="filters-modal">
            <div className="filters-modal-header">
              <h3>Фільтри</h3>
              <button
                className="filters-modal-close"
                onClick={() => setShowFiltersModal(false)}
                aria-label="Закрити"
              >
                <span>×</span>
              </button>
            </div>
            
            <div className="filters-modal-content">
              <div className="filter-group">
                <label>Категорія</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="filter-select"
                >
                  <option value="">Всі категорії</option>
                  {Object.entries(CATEGORIES).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Рівень складності</label>
                <select
                  value={selectedLevel}
                  onChange={(e) => setSelectedLevel(e.target.value)}
                  className="filter-select"
                >
                  <option value="">Всі рівні</option>
                  {Object.entries(LEVELS).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>

              <div className="filter-group">
                <label>Пошук за викладачем</label>
                <input
                  type="text"
                  value={teacherSearch}
                  onChange={(e) => setTeacherSearch(e.target.value)}
                  placeholder="Ім'я або email викладача"
                  className="filter-input"
                />
              </div>

              <div className="filter-group">
                <label>Сортування</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="filter-select"
                >
                  <option value="newest">Найновіші</option>
                  <option value="title">За назвою</option>
                  <option value="price_asc">Ціна: від низької</option>
                  <option value="price_desc">Ціна: від високої</option>
                  <option value="rating">За рейтингом</option>
                </select>
              </div>

              <div className="filters-modal-actions">
                <button
                  onClick={handleApplyFilters}
                  className="apply-filters-button"
                >
                  Застосувати фільтри
                </button>
                {hasActiveFilters && (
                  <button onClick={clearFilters} className="clear-filters-button">
                    Очистити фільтри
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

export default Courses;

