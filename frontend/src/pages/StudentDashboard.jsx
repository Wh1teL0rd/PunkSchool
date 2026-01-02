import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import studentsAPI from '../api/students';
import coursesAPI from '../api/courses';
import { CATEGORIES, LEVELS } from '../utils/translations';
import './Dashboard.css';

function StudentDashboard() {
  const [enrollments, setEnrollments] = useState([]);
  const [progress, setProgress] = useState(null);
  const [recommendedCourses, setRecommendedCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [certificateLoading, setCertificateLoading] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [enrollmentsData, progressData, coursesData] = await Promise.all([
        studentsAPI.getEnrollments(),
        studentsAPI.getProgress(),
        coursesAPI.getCourses({ sort_by: 'rating' }),
      ]);

      setEnrollments(enrollmentsData);
      setProgress(progressData);
      
      // Get recommended courses (top rated, not enrolled)
      const enrolledCourseIds = new Set(enrollmentsData.map(e => e.course?.id));
      const recommended = coursesData
        .filter(course => !enrolledCourseIds.has(course.id))
        .slice(0, 6);
      setRecommendedCourses(recommended);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Не вдалося завантажити дані. Спробуйте пізніше.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('uk-UA', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const updateEnrollmentCertificate = (enrollmentId, certificate) => {
    setEnrollments((prev) =>
      prev.map((enrollment) =>
        enrollment.id === enrollmentId ? { ...enrollment, certificate } : enrollment
      )
    );
  };

  const handleGenerateCertificate = async (enrollmentId) => {
    setCertificateLoading((prev) => ({ ...prev, [enrollmentId]: 'generate' }));
    try {
      const certificate = await studentsAPI.generateCertificate(enrollmentId);
      updateEnrollmentCertificate(enrollmentId, certificate);
    } catch (err) {
      console.error('Error generating certificate:', err);
      alert(err.response?.data?.detail || 'Не вдалося згенерувати сертифікат');
    } finally {
      setCertificateLoading((prev) => ({ ...prev, [enrollmentId]: null }));
    }
  };

  const handleDownloadCertificate = async (certificate) => {
    const enrollmentId = certificate?.enrollment_id;
    if (!certificate?.id || !enrollmentId) return;

    setCertificateLoading((prev) => ({ ...prev, [enrollmentId]: 'download' }));
    try {
      const response = await studentsAPI.downloadCertificate(certificate.id);
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      const studentName = certificate.student_name || 'certificate';
      const courseTitle = certificate.course_title || 'course';
      link.href = url;
      link.setAttribute('download', `${studentName} - ${courseTitle}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading certificate:', err);
      alert('Не вдалося скачати сертифікат');
    } finally {
      setCertificateLoading((prev) => ({ ...prev, [enrollmentId]: null }));
    }
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
          <h1>Мій кабінет</h1>
          <p>Відстежуйте свій прогрес та продовжуйте навчання</p>
        </div>

        {/* Progress Statistics */}
        {progress && (
          <section className="dashboard-section">
            <h2>Статистика прогресу</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📚</div>
                <div className="stat-value">{progress?.total_courses || 0}</div>
                <div className="stat-label">Активних курсів</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-value">{progress?.completed_courses || 0}</div>
                <div className="stat-label">Завершених курсів</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📖</div>
                <div className="stat-value">{progress?.total_lessons_completed || 0}</div>
                <div className="stat-label">Завершених уроків</div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🎯</div>
                <div className="stat-value">{progress?.average_progress || 0}%</div>
                <div className="stat-label">Середній прогрес</div>
              </div>
            </div>
          </section>
        )}

        {/* Learning History */}
        <section className="dashboard-section">
          <h2>Історія навчання</h2>
          {enrollments.length === 0 ? (
            <div className="empty-state">
              <p>Ви ще не записалися на жоден курс</p>
              <Link to="/courses" className="btn-primary">
                Переглянути курси
              </Link>
            </div>
          ) : (
            <div className="enrollments-list">
              {enrollments.map((enrollment) => (
                <div key={enrollment.id} className="enrollment-card">
                  <div className="enrollment-header">
                    <h3>{enrollment.course?.title || 'Курс'}</h3>
                    <span className={`enrollment-status ${enrollment.is_completed ? 'completed' : 'in-progress'}`}>
                      {enrollment.is_completed ? 'Завершено' : 'В процесі'}
                    </span>
                  </div>
                  <div className="enrollment-info">
                    <div className="enrollment-meta">
                      <span>📅 Записався: {formatDate(enrollment.enrolled_at)}</span>
                      {enrollment.course && (
                        <>
                          <span>{CATEGORIES[enrollment.course.category] || enrollment.course.category}</span>
                          <span>{LEVELS[enrollment.course.level] || enrollment.course.level}</span>
                        </>
                      )}
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${enrollment.progress_percent || 0}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">{Math.round(enrollment.progress_percent || 0)}%</span>
                    </div>
                    {enrollment.course && (
                      <Link
                        to={`/course-learning/${enrollment.course.id}`}
                        className="btn-continue-learning"
                      >
                        {enrollment.is_completed ? 'Переглянути курс' : 'Продовжити навчання'}
                      </Link>
                    )}
                  </div>
                  {enrollment.is_completed && (
                    <div className="enrollment-certificate">
                      {enrollment.certificate ? (
                        <>
                          <div className="certificate-info">
                            <div>
                              🎓 Сертифікат видано {formatDate(enrollment.certificate.issued_at)}
                            </div>
                            {enrollment.certificate.total_hours && (
                              <div>⏱️ {enrollment.certificate.total_hours} годин навчання</div>
                            )}
                          </div>
                          <div className="certificate-actions">
                            <button
                              className="btn-download-certificate"
                              onClick={() => handleDownloadCertificate(enrollment.certificate)}
                              disabled={certificateLoading[enrollment.id] === 'download'}
                            >
                              {certificateLoading[enrollment.id] === 'download'
                                ? 'Готуємо PDF...'
                                : 'Завантажити сертифікат'}
                            </button>
                          </div>
                        </>
                      ) : (
                        <>
                          <p>Після завершення курсу ви можете отримати офіційний сертифікат.</p>
                          <button
                            className="btn-generate-certificate"
                            onClick={() => handleGenerateCertificate(enrollment.id)}
                            disabled={certificateLoading[enrollment.id] === 'generate'}
                          >
                            {certificateLoading[enrollment.id] === 'generate'
                              ? 'Формуємо...'
                              : 'Отримати сертифікат'}
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Recommended Courses */}
        {recommendedCourses.length > 0 && (
          <section className="dashboard-section">
            <h2>Рекомендовані курси</h2>
            <div className="recommended-courses">
              {recommendedCourses.map((course) => (
                <div key={course.id} className="course-card-small">
                  <div className="course-card-header">
                    <h4>{course.title}</h4>
                    <span className="course-category-small">
                      {CATEGORIES[course.category] || course.category}
                    </span>
                  </div>
                  <div className="course-card-meta">
                    <span>{LEVELS[course.level] || course.level}</span>
                    <span>⭐ {course.rating.toFixed(1)}</span>
                  </div>
                  <div className="course-card-price">
                    {course.price === 0 ? 'Безкоштовно' : `${course.price} ₴`}
                  </div>
                  <Link to={`/courses`} className="course-card-link">
                    Детальніше →
                  </Link>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      <Footer />
    </div>
  );
}

export default StudentDashboard;

