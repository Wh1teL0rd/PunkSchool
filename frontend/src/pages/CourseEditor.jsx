import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import teachersAPI from '../api/teachers';
import coursesAPI from '../api/courses';
import { authAPI } from '../api/auth';
import { getCategoryLabel, getLevelLabel } from '../utils/translations';
import './CourseEditor.css';

function CourseEditor() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Module management
  const [showModuleModal, setShowModuleModal] = useState(false);
  const [editingModule, setEditingModule] = useState(null);
  const [moduleFormData, setModuleFormData] = useState({ title: '', order: 0 });
  
  // Lesson management
  const [showLessonModal, setShowLessonModal] = useState(false);
  const [selectedModule, setSelectedModule] = useState(null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [lessonFormData, setLessonFormData] = useState({
    title: '',
    lessonType: 'text', // 'video', 'text', 'quiz'
    video_url: '',
    content_text: '',
    duration_minutes: 0,
    order: 0,
  });
  
  // Quiz management
  const [quizFormData, setQuizFormData] = useState({
    title: '',
    passing_score: 70,
    questions: [],
  });
  const [currentQuestion, setCurrentQuestion] = useState({
    question_text: '',
    options: ['', ''],
    correct_option_index: 0,
    points: 1,
  });
  const [questionOptionsCount, setQuestionOptionsCount] = useState(2);
  const [editingQuestionIndex, setEditingQuestionIndex] = useState(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const user = await authAPI.getCurrentUser();
        setCurrentUser(user);
      } catch (err) {
        console.error('Error loading current user:', err);
      }
    };
    fetchCurrentUser();
  }, []);

  useEffect(() => {
    if (courseId) {
      fetchCourseDetails();
    }
  }, [courseId]);

  const fetchCourseDetails = async () => {
    setLoading(true);
    setError(null);
    try {
      const courseData = await coursesAPI.getCourseDetails(courseId);
      setCourse(courseData);
    } catch (err) {
      console.error('Error fetching course details:', err);
      setError('Не вдалося завантажити деталі курсу');
    } finally {
      setLoading(false);
    }
  };

  const handleAddModule = async (e) => {
    e.preventDefault();
    try {
      await teachersAPI.addModule(courseId, moduleFormData);
      setShowModuleModal(false);
      setModuleFormData({ title: '', order: 0 });
      fetchCourseDetails();
    } catch (err) {
      console.error('Error adding module:', err);
      alert('Не вдалося додати модуль');
    }
  };

  const handleUpdateModule = async (e) => {
    e.preventDefault();
    try {
      await teachersAPI.updateModule(editingModule.id, moduleFormData.title);
      setShowModuleModal(false);
      setEditingModule(null);
      setModuleFormData({ title: '', order: 0 });
      fetchCourseDetails();
    } catch (err) {
      console.error('Error updating module:', err);
      alert('Не вдалося оновити модуль');
    }
  };

  const handleDeleteModule = async (moduleId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цей модуль? Всі уроки також будуть видалені.')) {
      return;
    }
    try {
      await teachersAPI.deleteModule(moduleId);
      fetchCourseDetails();
    } catch (err) {
      console.error('Error deleting module:', err);
      alert('Не вдалося видалити модуль');
    }
  };

  const handleAddLesson = async (e) => {
    e.preventDefault();
    try {
      const lessonData = {
        title: lessonFormData.title,
        lesson_type: lessonFormData.lessonType,
        order: lessonFormData.order,
        duration_minutes: lessonFormData.duration_minutes,
      };

      if (lessonFormData.lessonType === 'video') {
        lessonData.video_url = lessonFormData.video_url;
      } else if (lessonFormData.lessonType === 'text') {
        lessonData.content_text = lessonFormData.content_text;
      }

      const lesson = await teachersAPI.addLesson(selectedModule.id, lessonData);

      // If it's a quiz lesson, add quiz after creating lesson (завжди створюємо, навіть якщо немає питань)
      if (lessonFormData.lessonType === 'quiz') {
        try {
          console.log('Adding quiz with data:', {
            title: quizFormData.title,
            passing_score: quizFormData.passing_score,
            questions_count: quizFormData.questions?.length || 0
          });
          await teachersAPI.addQuiz(lesson.id, {
            title: quizFormData.title || '',
            passing_score: quizFormData.passing_score || 70,
            questions: quizFormData.questions || [],
          });
        } catch (err) {
          console.error('Error adding quiz:', err);
          // Не викидаємо помилку, щоб урок все одно створився
        }
      }

      setShowLessonModal(false);
      setSelectedModule(null);
      setLessonFormData({
        title: '',
        lessonType: 'text',
        video_url: '',
        content_text: '',
        duration_minutes: 0,
        order: 0,
      });
      setQuizFormData({
        title: '',
        passing_score: 70,
        questions: [],
      });
      
      // Очікуємо трохи перед оновленням, щоб БД встигла зберегти дані
      await new Promise(resolve => setTimeout(resolve, 200));
      await fetchCourseDetails();
    } catch (err) {
      console.error('Error adding lesson:', err);
      alert('Не вдалося додати урок');
    }
  };

  const handleUpdateLesson = async (e) => {
    e.preventDefault();
    try {
      const lessonData = {
        title: lessonFormData.title,
        lesson_type: lessonFormData.lessonType,
        order: lessonFormData.order,
        duration_minutes: lessonFormData.duration_minutes,
      };

      if (lessonFormData.lessonType === 'video') {
        lessonData.video_url = lessonFormData.video_url;
        lessonData.content_text = null;
      } else if (lessonFormData.lessonType === 'text') {
        lessonData.content_text = lessonFormData.content_text;
        lessonData.video_url = null;
      } else if (lessonFormData.lessonType === 'quiz') {
        lessonData.video_url = null;
        lessonData.content_text = null;
      }

      await teachersAPI.updateLesson(editingLesson.id, lessonData);
      
      // If it's a quiz lesson, update quiz (завжди зберігаємо назву та passing_score)
      if (lessonFormData.lessonType === 'quiz') {
        try {
          // Завжди оновлюємо тест, навіть якщо немає питань (щоб зберегти назву та passing_score)
          const quizDataToSave = {
            title: quizFormData.title || '',
            passing_score: quizFormData.passing_score || 70,
            questions: quizFormData.questions || [],
          };
          
          console.log('=== SAVING QUIZ ===');
          console.log('Quiz data to save:', JSON.stringify(quizDataToSave, null, 2));
          console.log('Questions count:', quizDataToSave.questions.length);
          console.log('Questions details:', quizDataToSave.questions.map((q, i) => ({
            index: i,
            question_text: q.question_text,
            options_count: q.options?.length || 0,
            correct_option_index: q.correct_option_index,
            points: q.points
          })));
          
          const updatedQuiz = await teachersAPI.updateQuiz(editingLesson.id, quizDataToSave);
          console.log('=== QUIZ UPDATED SUCCESSFULLY ===');
          console.log('Updated quiz response:', updatedQuiz);
          console.log('Questions in response:', updatedQuiz.questions?.length || 0);
          console.log('Questions details:', updatedQuiz.questions);
        } catch (err) {
          console.error('Error updating quiz:', err);
          console.error('Error details:', err.response?.data);
          // Якщо тест ще не існує, створюємо його
          if (err.response?.status === 404) {
            console.log('Quiz not found, creating new one');
            try {
              const newQuiz = await teachersAPI.addQuiz(editingLesson.id, {
                title: quizFormData.title || '',
                passing_score: quizFormData.passing_score || 70,
                questions: quizFormData.questions || [],
              });
              console.log('Quiz created successfully:', newQuiz);
            } catch (createErr) {
              console.error('Failed to create quiz:', createErr);
              alert('Не вдалося створити тест: ' + (createErr.response?.data?.detail || createErr.message));
              throw createErr;
            }
          } else {
            // Якщо це інша помилка, викидаємо її далі
            console.error('Failed to update quiz:', err);
            alert('Не вдалося оновити тест: ' + (err.response?.data?.detail || err.message));
            throw err;
          }
        }
      }
      
      setShowLessonModal(false);
      setEditingLesson(null);
      setSelectedModule(null);
      setLessonFormData({
        title: '',
        lessonType: 'text',
        video_url: '',
        content_text: '',
        duration_minutes: 0,
        order: 0,
      });
      setQuizFormData({
        title: '',
        passing_score: 70,
        questions: [],
      });
      
      // Очікуємо трохи перед оновленням, щоб БД встигла зберегти дані
      await new Promise(resolve => setTimeout(resolve, 200));
      await fetchCourseDetails();
    } catch (err) {
      console.error('Error updating lesson:', err);
      console.error('Error details:', err.response?.data);
      alert('Не вдалося оновити урок: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteLesson = async (lessonId) => {
    if (!window.confirm('Ви впевнені, що хочете видалити цей урок?')) {
      return;
    }
    try {
      await teachersAPI.deleteLesson(lessonId);
      fetchCourseDetails();
    } catch (err) {
      console.error('Error deleting lesson:', err);
      alert('Не вдалося видалити урок');
    }
  };

  const openModuleModal = (module = null) => {
    if (module) {
      setEditingModule(module);
      setModuleFormData({ title: module.title, order: module.order });
    } else {
      setEditingModule(null);
      setModuleFormData({ title: '', order: course?.modules?.length || 0 });
    }
    setShowModuleModal(true);
  };

  const openLessonModal = async (module, lesson = null) => {
    setSelectedModule(module);
    if (lesson) {
      setEditingLesson(lesson);
      
      // Завжди завантажуємо повну інформацію про урок через API для отримання актуальних даних
      try {
        // Завантажуємо повну інформацію про урок через API
        const fullLesson = await teachersAPI.getLessonDetails(lesson.id);
        
        // Визначаємо тип уроку - використовуємо lesson_type з API
        const lessonType = fullLesson.lesson_type || 'text';
        
        setLessonFormData({
          title: fullLesson.title || lesson.title || '',
          lessonType,
          video_url: fullLesson.video_url || '',
          content_text: fullLesson.content_text || '',
          duration_minutes: fullLesson.duration_minutes || lesson.duration_minutes || 0,
          order: fullLesson.order || lesson.order || 0,
        });
        
        // Якщо це урок типу "quiz", завантажуємо дані тесту
        if (lessonType === 'quiz') {
          try {
            console.log('=== LOADING QUIZ DATA ===');
            console.log('Loading quiz data for lesson:', lesson.id);
            const quiz = await teachersAPI.getQuiz(lesson.id);
            console.log('Loaded quiz data:', quiz);
            console.log('Quiz title:', quiz.title);
            console.log('Quiz passing_score:', quiz.passing_score);
            console.log('Quiz questions count:', quiz.questions?.length || 0);
            console.log('Quiz questions raw:', quiz.questions);
            
            const questionsData = quiz.questions?.map((q, idx) => {
              const mapped = {
                question_text: q.question_text || '',
                options: q.options || ['', ''],
                correct_option_index: q.correct_option_index || 0,
                points: q.points || 1,
              };
              console.log(`Question ${idx + 1} mapped:`, mapped);
              return mapped;
            }) || [];
            
            console.log('=== MAPPED QUESTIONS ===');
            console.log('Total questions mapped:', questionsData.length);
            console.log('Mapped questions:', questionsData);
            
            const finalQuizData = {
              title: quiz.title || '',
              passing_score: quiz.passing_score || 70,
              questions: questionsData,
            };
            
            console.log('=== SETTING QUIZ FORM DATA ===');
            console.log('Final quiz form data:', finalQuizData);
            
            setQuizFormData(finalQuizData);
            
            console.log('=== QUIZ FORM DATA SET ===');
            console.log('Title:', finalQuizData.title);
            console.log('Passing score:', finalQuizData.passing_score);
            console.log('Questions count:', finalQuizData.questions.length);
          } catch (err) {
            console.error('Error loading quiz data:', err);
            // Якщо тест ще не створений, залишаємо порожні дані
            setQuizFormData({
              title: '',
              passing_score: 70,
              questions: [],
            });
          }
        } else {
          // Очищаємо дані тесту для інших типів уроків
          setQuizFormData({
            title: '',
            passing_score: 70,
            questions: [],
          });
          setQuestionOptionsCount(2);
          setCurrentQuestion({
            question_text: '',
            options: Array(2).fill(''),
            correct_option_index: 0,
            points: 1,
          });
          setEditingQuestionIndex(null);
        }
      } catch (err) {
        console.error('Error loading lesson details:', err);
        // Якщо не вдалося завантажити, використовуємо базові дані
        setLessonFormData({
          title: lesson.title || '',
          lessonType: 'text',
          video_url: '',
          content_text: '',
          duration_minutes: lesson.duration_minutes || 0,
          order: lesson.order || 0,
        });
      }
    } else {
      setEditingLesson(null);
      setLessonFormData({
        title: '',
        lessonType: 'text',
        video_url: '',
        content_text: '',
        duration_minutes: 0,
        order: module.lessons?.length || 0,
      });
      setQuizFormData({
        title: '',
        passing_score: 70,
        questions: [],
      });
    }
    setShowLessonModal(true);
  };

  const addQuestion = () => {
    if (!currentQuestion.question_text || currentQuestion.options.some(opt => !opt.trim())) {
      alert('Заповніть всі поля питання');
      return;
    }
    if (currentQuestion.options.length < 2) {
      alert('Питання має містити мінімум 2 варіанти відповіді');
      return;
    }
    
    if (editingQuestionIndex !== null) {
      // Редагуємо існуюче питання
      const updatedQuestions = [...quizFormData.questions];
      updatedQuestions[editingQuestionIndex] = { ...currentQuestion };
      setQuizFormData({
        ...quizFormData,
        questions: updatedQuestions,
      });
      setEditingQuestionIndex(null);
    } else {
      // Додаємо нове питання
      setQuizFormData({
        ...quizFormData,
        questions: [...quizFormData.questions, { ...currentQuestion }],
      });
    }
    
    setCurrentQuestion({
      question_text: '',
      options: Array(questionOptionsCount).fill(''),
      correct_option_index: 0,
      points: 1,
    });
  };

  const editQuestion = (index) => {
    const question = quizFormData.questions[index];
    setCurrentQuestion({
      question_text: question.question_text || '',
      options: [...question.options],
      correct_option_index: question.correct_option_index || 0,
      points: question.points || 1,
    });
    setQuestionOptionsCount(question.options.length);
    setEditingQuestionIndex(index);
  };

  const cancelEditQuestion = () => {
    setCurrentQuestion({
      question_text: '',
      options: Array(questionOptionsCount).fill(''),
      correct_option_index: 0,
      points: 1,
    });
    setEditingQuestionIndex(null);
  };

  const updateQuestionOptionsCount = (count) => {
    const minCount = 2;
    const newCount = Math.max(minCount, parseInt(count) || minCount);
    setQuestionOptionsCount(newCount);
    setCurrentQuestion({
      ...currentQuestion,
      options: Array(newCount).fill('').map((_, i) => currentQuestion.options[i] || ''),
      correct_option_index: Math.min(currentQuestion.correct_option_index, newCount - 1),
      points: currentQuestion.points || 1,
    });
  };

  const removeQuestion = (index) => {
    setQuizFormData({
      ...quizFormData,
      questions: quizFormData.questions.filter((_, i) => i !== index),
    });
  };

  const extractYoutubeId = (url) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
  };

  if (loading) {
    return (
      <div className="course-editor-page">
        <Header />
        <div className="editor-loading">Завантаження...</div>
        <Footer />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="course-editor-page">
        <Header />
        <div className="editor-error">{error || 'Курс не знайдено'}</div>
        <Footer />
      </div>
    );
  }

  const backDashboardPath = currentUser?.role === 'admin' ? '/dashboard/admin' : '/dashboard/teacher';

  return (
    <div className="course-editor-page">
      <Header />
      
      <div className="course-editor-container">
        <div className="editor-header">
          <div>
            <h1>{course.title}</h1>
            <p>Управління модулями та уроками</p>
          </div>
          <button onClick={() => navigate(backDashboardPath)} className="btn-back">
            ← Назад до кабінету
          </button>
        </div>

        {/* Course Info */}
        <div className="course-info-card">
          <div className="course-info-item">
            <strong>Категорія:</strong> {getCategoryLabel(course.category)}
          </div>
          <div className="course-info-item">
            <strong>Рівень:</strong> {getLevelLabel(course.level)}
          </div>
          <div className="course-info-item">
            <strong>Ціна:</strong> {course.price === 0 ? 'Безкоштовно' : `${course.price} ₴`}
          </div>
          <div className="course-info-item">
            <strong>Статус:</strong> {course.is_published ? 'Опубліковано' : 'Чернетка'}
          </div>
        </div>

        {/* Modules */}
        <div className="modules-section">
          <div className="section-header">
            <h2>Модулі курсу</h2>
            <button onClick={() => openModuleModal()} className="btn-add-module">
              + Додати модуль
            </button>
          </div>

          {course.modules && course.modules.length > 0 ? (
            <div className="modules-list">
              {course.modules.map((module, moduleIndex) => (
                <div key={module.id} className="module-card">
                  <div className="module-header">
                    <div className="module-title-section">
                      <span className="module-number">{moduleIndex + 1}</span>
                      <h3>{module.title}</h3>
                    </div>
                    <div className="module-actions">
                      <button
                        onClick={() => openModuleModal(module)}
                        className="btn-edit-small"
                      >
                        Редагувати
                      </button>
                      <button
                        onClick={() => handleDeleteModule(module.id)}
                        className="btn-delete-small"
                      >
                        Видалити
                      </button>
                    </div>
                  </div>

                  {/* Lessons */}
                  <div className="lessons-section">
                    <div className="lessons-header">
                      <h4>Уроки ({module.lessons?.length || 0})</h4>
                      <button
                        onClick={() => openLessonModal(module)}
                        className="btn-add-lesson"
                      >
                        + Додати урок
                      </button>
                    </div>

                    {module.lessons && module.lessons.length > 0 ? (
                      <div className="lessons-list">
                        {module.lessons.map((lesson, lessonIndex) => (
                          <div key={lesson.id} className="lesson-item">
                            <div className="lesson-info">
                              <span className="lesson-number">
                                {moduleIndex + 1}.{lessonIndex + 1}
                              </span>
                              <div className="lesson-details">
                                <strong>{lesson.title}</strong>
                                <div className="lesson-meta">
                                  {lesson.video_url && <span className="lesson-type">🎥 Відео</span>}
                                  {lesson.content_text && !lesson.video_url && <span className="lesson-type">📝 Текст</span>}
                                  {lesson.duration_minutes > 0 && (
                                    <span>{lesson.duration_minutes} хв</span>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="lesson-actions">
                              <button
                                onClick={() => openLessonModal(module, lesson)}
                                className="btn-edit-small"
                              >
                                Редагувати
                              </button>
                              <button
                                onClick={() => handleDeleteLesson(lesson.id)}
                                className="btn-delete-small"
                              >
                                Видалити
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="empty-lessons">Поки немає уроків у цьому модулі</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-modules">
              <p>Поки немає модулів. Створіть перший модуль для додавання уроків.</p>
            </div>
          )}
        </div>
      </div>

      {/* Module Modal */}
      {showModuleModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>{editingModule ? 'Редагувати модуль' : 'Додати модуль'}</h2>
              <button className="modal-close" onClick={() => setShowModuleModal(false)} aria-label="Закрити">
                <span>×</span>
              </button>
            </div>
            <form onSubmit={editingModule ? handleUpdateModule : handleAddModule}>
              <div className="form-group">
                <label>Назва модуля</label>
                <input
                  type="text"
                  value={moduleFormData.title}
                  onChange={(e) => setModuleFormData({ ...moduleFormData, title: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Порядок</label>
                <input
                  type="number"
                  value={moduleFormData.order}
                  onChange={(e) => setModuleFormData({ ...moduleFormData, order: parseInt(e.target.value) || 0 })}
                  min="0"
                />
              </div>
              <div className="modal-actions">
                <button type="button" onClick={() => setShowModuleModal(false)} className="btn-cancel">
                  Скасувати
                </button>
                <button type="submit" className="btn-submit">
                  {editingModule ? 'Зберегти' : 'Додати'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lesson Modal */}
      {showLessonModal && selectedModule && (
        <div className="modal-overlay">
          <div className="modal-content modal-content-large">
            <div className="modal-header">
              <h2>{editingLesson ? 'Редагувати урок' : 'Додати урок'}</h2>
              <button className="modal-close" onClick={() => setShowLessonModal(false)} aria-label="Закрити">
                <span>×</span>
              </button>
            </div>
            <form onSubmit={editingLesson ? handleUpdateLesson : handleAddLesson}>
              <div className="form-group">
                <label>Назва уроку</label>
                <input
                  type="text"
                  value={lessonFormData.title}
                  onChange={(e) => setLessonFormData({ ...lessonFormData, title: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Тип уроку</label>
                <select
                  value={lessonFormData.lessonType}
                  onChange={(e) => {
                    const newType = e.target.value;
                    setLessonFormData({ 
                      ...lessonFormData, 
                      lessonType: newType,
                      // Очищаємо дані інших типів при зміні типу (якщо не редагуємо)
                      video_url: newType === 'video' ? lessonFormData.video_url : '',
                      content_text: newType === 'text' ? lessonFormData.content_text : '',
                    });
                  }}
                >
                  <option value="text">Текст</option>
                  <option value="video">Відео (YouTube)</option>
                  <option value="quiz">Тест/Опитування</option>
                </select>
              </div>

              {lessonFormData.lessonType === 'video' && (
                <div className="form-group">
                  <label>Посилання на YouTube</label>
                  <input
                    type="text"
                    value={lessonFormData.video_url}
                    onChange={(e) => setLessonFormData({ ...lessonFormData, video_url: e.target.value })}
                    placeholder="https://www.youtube.com/watch?v=..."
                    required={lessonFormData.lessonType === 'video'}
                  />
                  {lessonFormData.video_url && extractYoutubeId(lessonFormData.video_url) && (
                    <div className="video-preview">
                      <iframe
                        width="100%"
                        height="315"
                        src={`https://www.youtube.com/embed/${extractYoutubeId(lessonFormData.video_url)}`}
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                      ></iframe>
                    </div>
                  )}
                </div>
              )}

              {lessonFormData.lessonType === 'text' && (
                <div className="form-group">
                  <label>Текст уроку</label>
                  <textarea
                    value={lessonFormData.content_text}
                    onChange={(e) => setLessonFormData({ ...lessonFormData, content_text: e.target.value })}
                    rows="10"
                    required={lessonFormData.lessonType === 'text'}
                  />
                </div>
              )}

              {lessonFormData.lessonType === 'quiz' && (
                <div className="quiz-section">
                  <div className="form-group">
                    <label>Назва тесту</label>
                    <input
                      type="text"
                      value={quizFormData.title}
                      onChange={(e) => setQuizFormData({ ...quizFormData, title: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Мінімальний бал для проходження (%)</label>
                    <input
                      type="number"
                      value={quizFormData.passing_score}
                      onChange={(e) => setQuizFormData({ ...quizFormData, passing_score: parseInt(e.target.value) || 70 })}
                      min="0"
                      max="100"
                    />
                  </div>

                  <div className="questions-section">
                    <h4>Питання тесту</h4>
                    {quizFormData.questions.map((question, index) => (
                      <div key={index} className="question-item">
                        <div className="question-header">
                          <div>
                            <strong>Питання {index + 1}</strong>
                            <span className="question-points">({question.points || 1} {question.points === 1 ? 'бал' : 'балів'})</span>
                          </div>
                          <div>
                            <button
                              type="button"
                              onClick={() => editQuestion(index)}
                              className="btn-edit-question"
                            >
                              Редагувати
                            </button>
                            <button
                              type="button"
                              onClick={() => removeQuestion(index)}
                              className="btn-remove-question"
                            >
                              Видалити
                            </button>
                          </div>
                        </div>
                        <p>{question.question_text}</p>
                        <ul>
                          {question.options.map((option, optIndex) => (
                            <li key={optIndex} className={optIndex === question.correct_option_index ? 'correct-answer' : ''}>
                              {option} {optIndex === question.correct_option_index && '✓ (правильна відповідь)'}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}

                    <div className="add-question-form">
                      <h4>{editingQuestionIndex !== null ? 'Редагувати питання' : 'Додати питання'}</h4>
                      {editingQuestionIndex !== null && (
                        <button
                          type="button"
                          onClick={cancelEditQuestion}
                          className="btn-cancel-edit"
                          style={{ marginBottom: '1rem' }}
                        >
                          Скасувати редагування
                        </button>
                      )}
                      <div className="form-group">
                        <label>Текст питання</label>
                        <input
                          type="text"
                          value={currentQuestion.question_text}
                          onChange={(e) => setCurrentQuestion({ ...currentQuestion, question_text: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label>Кількість варіантів відповідей</label>
                        <input
                          type="number"
                          min="2"
                          value={questionOptionsCount}
                          onChange={(e) => updateQuestionOptionsCount(e.target.value)}
                          className="options-count-input"
                          style={{ width: '100px', marginBottom: '1rem' }}
                        />
                      </div>
                      <div className="form-group">
                        <label>Варіанти відповідей</label>
                        {currentQuestion.options.map((option, index) => (
                          <div key={index} className="option-input">
                            <input
                              type="text"
                              value={option}
                              onChange={(e) => {
                                const newOptions = [...currentQuestion.options];
                                newOptions[index] = e.target.value;
                                setCurrentQuestion({ ...currentQuestion, options: newOptions });
                              }}
                              placeholder={`Варіант ${index + 1}`}
                            />
                            <label className="radio-label">
                              <input
                                type="radio"
                                name="correct_option"
                                checked={currentQuestion.correct_option_index === index}
                                onChange={() => setCurrentQuestion({ ...currentQuestion, correct_option_index: index })}
                              />
                              Правильна
                            </label>
                          </div>
                        ))}
                      </div>
                      <div className="form-group">
                        <label>Балів за правильну відповідь</label>
                        <input
                          type="number"
                          min="1"
                          value={currentQuestion.points || 1}
                          onChange={(e) => setCurrentQuestion({ ...currentQuestion, points: parseInt(e.target.value) || 1 })}
                          className="points-input"
                          style={{ width: '100px' }}
                        />
                      </div>
                      <button
                        type="button"
                        onClick={addQuestion}
                        className="btn-add-question"
                      >
                        {editingQuestionIndex !== null ? 'Зберегти зміни' : 'Додати питання'}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div className="form-row">
                <div className="form-group">
                  <label>Тривалість (хвилин)</label>
                  <input
                    type="number"
                    value={lessonFormData.duration_minutes}
                    onChange={(e) => setLessonFormData({ ...lessonFormData, duration_minutes: parseInt(e.target.value) || 0 })}
                    min="0"
                  />
                </div>
                <div className="form-group">
                  <label>Порядок</label>
                  <input
                    type="number"
                    value={lessonFormData.order}
                    onChange={(e) => setLessonFormData({ ...lessonFormData, order: parseInt(e.target.value) || 0 })}
                    min="0"
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowLessonModal(false)} className="btn-cancel">
                  Скасувати
                </button>
                <button type="submit" className="btn-submit">
                  {editingLesson ? 'Зберегти' : 'Додати'}
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

export default CourseEditor;

