import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import coursesAPI from '../api/courses';
import studentsAPI from '../api/students';
import { authAPI } from '../api/auth';
import { getCategoryLabel, getLevelLabel } from '../utils/translations';
import './CourseLearning.css';

function CourseLearning() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [enrollment, setEnrollment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [completingLessonId, setCompletingLessonId] = useState(null);
  const [completingModuleId, setCompletingModuleId] = useState(null);
  const [completingCourse, setCompletingCourse] = useState(false);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [showLessonModal, setShowLessonModal] = useState(false);
  const [lessonQuiz, setLessonQuiz] = useState(null);
  const [loadingQuiz, setLoadingQuiz] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState({}); // {questionId: selectedOptionIndex}
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizResult, setQuizResult] = useState(null);
  const [submittingQuiz, setSubmittingQuiz] = useState(false);
  const [resettingLessonId, setResettingLessonId] = useState(null);

  useEffect(() => {
    fetchCourseData();
  }, [courseId]);

  const fetchCourseData = async () => {
    if (!authAPI.isAuthenticated()) {
      navigate('/login');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [courseData, enrollmentData] = await Promise.all([
        coursesAPI.getCourseDetails(courseId),
        studentsAPI.getEnrollment(courseId).catch(() => null)
      ]);

      if (!enrollmentData) {
        setError('Ви не записані на цей курс');
        return;
      }

      setCourse(courseData);
      setEnrollment(enrollmentData);
    } catch (err) {
      console.error('Error fetching course data:', err);
      setError('Не вдалося завантажити дані курсу');
    } finally {
      setLoading(false);
    }
  };

  const isLessonCompleted = (lessonId) => {
    return enrollment?.completed_lessons?.includes(lessonId) || false;
  };

  const isModuleCompleted = (module) => {
    if (!module.lessons || module.lessons.length === 0) return false;
    return module.lessons.every(lesson => isLessonCompleted(lesson.id));
  };

  const isCourseCompleted = () => {
    if (!course || !course.modules) return false;
    return course.modules.every(module => isModuleCompleted(module));
  };

  const handleCompleteLesson = async (lessonId) => {
    setCompletingLessonId(lessonId);
    try {
      const updatedEnrollment = await studentsAPI.completeLesson(lessonId);
      setEnrollment(updatedEnrollment);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Не вдалося завершити урок';
      alert(errorMessage);
    } finally {
      setCompletingLessonId(null);
    }
  };

  const handleCompleteModule = async (moduleId) => {
    setCompletingModuleId(moduleId);
    try {
      const updatedEnrollment = await studentsAPI.completeModule(moduleId);
      setEnrollment(updatedEnrollment);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Не вдалося завершити модуль';
      alert(errorMessage);
    } finally {
      setCompletingModuleId(null);
    }
  };

  const handleCompleteCourse = async () => {
    setCompletingCourse(true);
    try {
      const updatedEnrollment = await studentsAPI.completeCourse(courseId);
      setEnrollment(updatedEnrollment);
      alert('Вітаємо! Ви успішно завершили курс!');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Не вдалося завершити курс';
      alert(errorMessage);
    } finally {
      setCompletingCourse(false);
    }
  };

  const handleOpenLesson = async (lesson) => {
    setShowLessonModal(true);
    setQuizAnswers({});
    setQuizSubmitted(false);
    setQuizResult(null);
    setLessonQuiz(null);

    // Завантажуємо повну інформацію про урок (включаючи quiz, якщо є)
    if (lesson.lesson_type === 'quiz') {
      setLoadingQuiz(true);
    }
    
    try {
      const lessonDetails = await studentsAPI.getLesson(lesson.id);
      setSelectedLesson(lessonDetails);
      
      // Quiz завантажується разом з уроком
      if (lessonDetails.quiz) {
        setLessonQuiz(lessonDetails.quiz);
      } else {
        setLessonQuiz(null);
      }
    } catch (err) {
      console.error('Error loading lesson details:', err);
      setSelectedLesson(lesson); // Використовуємо базові дані, якщо не вдалося завантажити
      setLessonQuiz(null);
    } finally {
      setLoadingQuiz(false);
    }
  };

  const handleCloseLessonModal = () => {
    setShowLessonModal(false);
    setSelectedLesson(null);
    setLessonQuiz(null);
    setQuizAnswers({});
    setQuizSubmitted(false);
    setQuizResult(null);
  };

  const handleQuizAnswerChange = (questionId, optionIndex) => {
    if (quizSubmitted) return; // Не дозволяємо змінювати після відправки
    setQuizAnswers(prev => ({
      ...prev,
      [questionId]: optionIndex
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!lessonQuiz) return;

    // Перевіряємо, чи всі питання відповідені
    const allQuestionsAnswered = lessonQuiz.questions.every(q => 
      quizAnswers[q.id] !== undefined && quizAnswers[q.id] !== null
    );

    if (!allQuestionsAnswered) {
      alert('Будь ласка, відповідьте на всі питання');
      return;
    }

    setSubmittingQuiz(true);
    try {
      // Формуємо відповіді у форматі {question_id: selected_option_index}
      const answers = {};
      lessonQuiz.questions.forEach(q => {
        answers[q.id] = quizAnswers[q.id];
      });

      const result = await studentsAPI.submitQuiz(lessonQuiz.id, { answers });
      setQuizResult(result);
      setQuizSubmitted(true);
    } catch (err) {
      console.error('Error submitting quiz:', err);
      alert('Не вдалося відправити тест: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmittingQuiz(false);
    }
  };

  const handleRetakeQuiz = () => {
    setQuizAnswers({});
    setQuizSubmitted(false);
    setQuizResult(null);
  };

  const handleResetLesson = async (lessonId) => {
    setResettingLessonId(lessonId);
    try {
      const updatedEnrollment = await studentsAPI.resetLesson(lessonId);
      setEnrollment(updatedEnrollment);
      setQuizAnswers({});
      setQuizSubmitted(false);
      setQuizResult(null);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Не вдалося скинути прогрес уроку';
      alert(errorMessage);
    } finally {
      setResettingLessonId(null);
    }
  };

  const totalLessons = course?.modules?.reduce((sum, module) => {
    return sum + (module.lessons?.length || 0);
  }, 0) || 0;

  const completedLessonsCount = enrollment?.completed_lessons?.length || 0;

  const calculatedProgress = totalLessons > 0
    ? Math.round((completedLessonsCount / totalLessons) * 100)
    : Math.round(enrollment?.progress_percent || 0);

  if (loading) {
    return (
      <div className="course-learning-page">
        <Header />
        <div className="loading-container">
          <div className="loading">Завантаження...</div>
        </div>
        <Footer />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="course-learning-page">
        <Header />
        <div className="error-container">
          <div className="error">{error || 'Курс не знайдено'}</div>
          <button onClick={() => navigate('/courses')} className="btn-back">
            Повернутися до каталогу
          </button>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="course-learning-page">
      <Header />
      <div className="course-learning-container">
        <div className="course-learning-header">
          <button onClick={() => navigate('/courses')} className="btn-back">
            ← Назад до каталогу
          </button>
          <h1>{course.title}</h1>
          <div className="course-meta-info">
            <span>{getCategoryLabel(course.category)}</span>
            <span>{getLevelLabel(course.level)}</span>
            <span>Прогрес: {calculatedProgress}%</span>
          </div>
        </div>

        {course.description && (
          <div className="course-description">
            <p>{course.description}</p>
          </div>
        )}

        <div className="modules-section">
          {course.modules && course.modules.length > 0 ? (
            course.modules.map((module, moduleIndex) => {
              const moduleCompleted = isModuleCompleted(module);
              const allLessonsCompleted = module.lessons?.every(lesson => isLessonCompleted(lesson.id)) || false;

              return (
                <div key={module.id} className="module-card">
                  <div className="module-header">
                    <h2>
                      Модуль {moduleIndex + 1}: {module.title}
                      {moduleCompleted && <span className="completed-badge">✓ Завершено</span>}
                    </h2>
                  </div>

                  {module.lessons && module.lessons.length > 0 ? (
                    <div className="lessons-list">
                      {module.lessons.map((lesson, lessonIndex) => {
                        const lessonCompleted = isLessonCompleted(lesson.id);

                        return (
                          <div key={lesson.id} className={`lesson-item ${lessonCompleted ? 'completed' : ''}`}>
                            <div 
                              className="lesson-header clickable"
                              onClick={() => handleOpenLesson(lesson)}
                              style={{ cursor: 'pointer' }}
                            >
                              <div className="lesson-info">
                                <span className="lesson-number">Урок {lessonIndex + 1}</span>
                                <h3>{lesson.title}</h3>
                                {lessonCompleted && <span className="lesson-completed">✓ Завершено</span>}
                                <span className="lesson-type-badge">
                                  {lesson.lesson_type === 'video' ? '🎥 Відео' : 
                                   lesson.lesson_type === 'quiz' ? '📝 Тест' : 
                                   '📄 Текст'}
                                </span>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="no-lessons">Поки немає уроків у цьому модулі</p>
                  )}

                  {allLessonsCompleted && !moduleCompleted && (
                    <div className="module-complete-section">
                      <button
                        onClick={() => handleCompleteModule(module.id)}
                        className="btn-complete-module"
                        disabled={completingModuleId === module.id}
                      >
                        {completingModuleId === module.id ? 'Завершуємо...' : 'Завершити модуль'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="no-modules">
              <p>Поки немає модулів у цьому курсі</p>
            </div>
          )}

          {isCourseCompleted() && !enrollment?.is_completed && (
            <div className="course-complete-section">
              <button
                onClick={handleCompleteCourse}
                className="btn-complete-course"
                disabled={completingCourse}
              >
                {completingCourse ? 'Завершуємо...' : 'Завершити курс'}
              </button>
            </div>
          )}

          {enrollment?.is_completed && (
            <div className="course-completed-message">
              <h2>🎉 Вітаємо! Ви успішно завершили курс!</h2>
              <p>Ви можете отримати сертифікат про завершення курсу.</p>
            </div>
          )}
        </div>
      </div>

      {/* Lesson Modal */}
      {showLessonModal && selectedLesson && (
        <div className="lesson-modal-overlay" onClick={handleCloseLessonModal}>
          <div className="lesson-modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="lesson-modal-close"
              onClick={handleCloseLessonModal}
              aria-label="Закрити"
            >
              <span>×</span>
            </button>
            
            <div className="lesson-modal-header">
              <h2>{selectedLesson.title}</h2>
              <span className="lesson-type-badge-modal">
                {selectedLesson.lesson_type === 'video' ? '🎥 Відео' : 
                 selectedLesson.lesson_type === 'quiz' ? '📝 Тест' : 
                 '📄 Текст'}
              </span>
            </div>

            <div className="lesson-modal-body">
              {selectedLesson.lesson_type === 'video' && selectedLesson.video_url && (
                <div className="video-container-modal">
                  <iframe
                    src={`https://www.youtube.com/embed/${extractYouTubeId(selectedLesson.video_url)}`}
                    title={selectedLesson.title}
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
              )}

              {selectedLesson.lesson_type === 'text' && selectedLesson.content_text && (
                <div className="text-content-modal">
                  <p>{selectedLesson.content_text}</p>
                </div>
              )}

              {selectedLesson.lesson_type === 'quiz' && (
                <div className="quiz-content-modal">
                  {loadingQuiz ? (
                    <div className="loading">Завантаження тесту...</div>
                  ) : lessonQuiz ? (
                    <div className="quiz-details">
                      <h3>{lessonQuiz.title}</h3>
                      <p className="quiz-passing-score">
                        Мінімальний бал для проходження: {lessonQuiz.passing_score} балів
                      </p>
                      {quizSubmitted && quizResult && (
                        <div className={`quiz-result ${quizResult.passed ? 'passed' : 'failed'}`}>
                          <h4>{quizResult.passed ? '✅ Тест пройдено!' : '❌ Тест не пройдено'}</h4>
                          <p>Ваш результат: {quizResult.score} балів з {quizResult.total_score || 0} можливих</p>
                          <p>Мінімальний бал: {lessonQuiz.passing_score} балів</p>
                        </div>
                      )}
                      {quizSubmitted && quizResult && !quizResult.passed && (
                        <div className="quiz-retake-section">
                          <p className="quiz-retake-hint">
                            Ви можете перепройти тест, щоб розблокувати завершення уроку.
                          </p>
                          <button
                            type="button"
                            className="btn-retake-quiz"
                            onClick={handleRetakeQuiz}
                          >
                            Перепройти опитування
                          </button>
                        </div>
                      )}
                      {lessonQuiz.questions && lessonQuiz.questions.length > 0 ? (
                        <div className="quiz-questions">
                          {lessonQuiz.questions.map((question, qIndex) => {
                            const selectedAnswer = quizAnswers[question.id];
                            
                            return (
                              <div key={question.id || qIndex} className="quiz-question-item">
                                <h4>Питання {qIndex + 1}: {question.question_text}</h4>
                                {question.points && (
                                  <p className="question-points">Балів за питання: {question.points}</p>
                                )}
                                <div className="quiz-options">
                                  {question.options && question.options.map((option, optIndex) => (
                                    <div key={optIndex} className="quiz-option">
                                      <input
                                        type="radio"
                                        name={`question-${question.id || qIndex}`}
                                        id={`option-${question.id || qIndex}-${optIndex}`}
                                        value={optIndex}
                                        checked={selectedAnswer === optIndex}
                                        onChange={() => handleQuizAnswerChange(question.id, optIndex)}
                                        disabled={quizSubmitted}
                                      />
                                      <label htmlFor={`option-${question.id || qIndex}-${optIndex}`}>
                                        {option}
                                      </label>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <p>Питання ще не додані до цього тесту.</p>
                      )}
                      {!quizSubmitted && (
                        <div className="quiz-submit-section">
                          <button
                            onClick={handleSubmitQuiz}
                            className="btn-submit-quiz"
                            disabled={submittingQuiz}
                          >
                            {submittingQuiz ? 'Відправляємо...' : 'Відправити тест'}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="quiz-loading-error">
                      <p>Не вдалося завантажити тест. Спробуйте пізніше.</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="lesson-modal-footer">
              {(() => {
                const lessonCompleted = isLessonCompleted(selectedLesson.id);
                const requiresQuizPass = selectedLesson.lesson_type === 'quiz';
                const quizPassed = requiresQuizPass ? !!quizResult?.passed : true;
                const shouldShowCompleteButton = !lessonCompleted;
                const completeDisabled =
                  completingLessonId === selectedLesson.id ||
                  (requiresQuizPass && !quizPassed);

                return (
                  <>
                    {shouldShowCompleteButton && (
                      <button
                        onClick={async () => {
                          await handleCompleteLesson(selectedLesson.id);
                          handleCloseLessonModal();
                        }}
                        className="btn-complete-lesson-modal"
                        disabled={completeDisabled}
                      >
                        {completingLessonId === selectedLesson.id ? 'Завершуємо...' : 'Завершити урок'}
                      </button>
                    )}
                    {requiresQuizPass && !quizPassed && (
                      <p className="quiz-completion-hint">
                        Пройдіть тест з потрібним балом, щоб розблокувати завершення уроку.
                      </p>
                    )}
                    {lessonCompleted && (
                      <div className="lesson-reset-section">
                        <div className="lesson-completed-message">
                          <span>✓ Урок завершено</span>
                        </div>
                        <button
                          type="button"
                          className="btn-reset-lesson"
                          onClick={() => handleResetLesson(selectedLesson.id)}
                          disabled={resettingLessonId === selectedLesson.id}
                        >
                          {resettingLessonId === selectedLesson.id ? 'Скидаємо...' : 'Повторити урок'}
                        </button>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
}

function extractYouTubeId(url) {
  if (!url) return '';
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : '';
}

export default CourseLearning;

