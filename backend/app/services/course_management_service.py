"""
Course management service - for teachers to create and manage courses.
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.course import Course, Module, Lesson, Quiz, QuizQuestion

logger = logging.getLogger(__name__)
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.course import (
    CourseCreateDTO, 
    CourseUpdateDTO, 
    ModuleCreateDTO, 
    LessonCreateDTO,
    QuizCreateDTO
)


class CourseManagementService:
    """
    Service for course management operations (teacher functions).
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_course(self, current_user: User, data: CourseCreateDTO) -> Course:
        """
        Create a new course.
        Admins can create courses for any teacher by specifying teacher_id.
        """
        if current_user.role == UserRole.ADMIN:
            teacher_id = self._resolve_teacher_id(data.teacher_id)
        else:
            teacher_id = current_user.id
            if data.teacher_id and data.teacher_id != teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Teachers cannot assign courses to other instructors"
                )

        course = Course(
            teacher_id=teacher_id,
            title=data.title,
            description=data.description,
            price=data.price,
            category=data.category,
            level=data.level,
            is_published=False
        )
        
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def update_course(self, course_id: int, current_user: User, data: CourseUpdateDTO) -> Course:
        """
        Update an existing course.
        
        Args:
            course_id: Course ID
            teacher_id: Teacher's user ID (for authorization)
            data: Course update data
        
        Returns:
            Updated Course instance
        
        Raises:
            HTTPException: If course not found or unauthorized
        """
        course = self._get_course_with_access(course_id, current_user)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def delete_course(self, course_id: int, current_user: User) -> bool:
        """Delete a course."""
        course = self._get_course_with_access(course_id, current_user)
        self.db.delete(course)
        self.db.commit()
        return True
    
    def add_module(self, course_id: int, current_user: User, data: ModuleCreateDTO) -> Module:
        """
        Add a module to a course.
        
        Args:
            course_id: Course ID
            teacher_id: Teacher's user ID
            data: Module creation data
        
        Returns:
            Created Module instance
        """
        course = self._get_course_with_access(course_id, current_user)
        
        # Get next order number
        max_order = max((m.order for m in course.modules), default=-1)
        
        module = Module(
            course_id=course_id,
            title=data.title,
            order=data.order if data.order > 0 else max_order + 1
        )
        
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module
    
    def update_module(self, module_id: int, current_user: User, title: str) -> Module:
        """Update a module's title."""
        module = self._get_module_with_access(module_id, current_user)
        module.title = title
        self.db.commit()
        self.db.refresh(module)
        return module
    
    def delete_module(self, module_id: int, current_user: User) -> bool:
        """Delete a module."""
        module = self._get_module_with_access(module_id, current_user)
        self.db.delete(module)
        self.db.commit()
        return True
    
    def add_lesson(self, module_id: int, current_user: User, data: LessonCreateDTO) -> Lesson:
        """
        Add a lesson to a module.
        
        Args:
            module_id: Module ID
            current_user: Authenticated user
            data: Lesson creation data
        
        Returns:
            Created Lesson instance
        """
        module = self._get_module_with_access(module_id, current_user)
        
        # Get next order number
        max_order = max((l.order for l in module.lessons), default=-1)
        
        from app.models.enums import LessonType
        
        # Отримуємо значення lesson_type
        lesson_type_value = None
        if data.lesson_type:
            if hasattr(data.lesson_type, 'value'):
                lesson_type_value = data.lesson_type.value
            else:
                lesson_type_value = data.lesson_type
        else:
            lesson_type_value = LessonType.TEXT.value
        
        # Визначаємо, який тип уроку
        is_video = (data.lesson_type == LessonType.VIDEO) or (isinstance(data.lesson_type, str) and data.lesson_type == LessonType.VIDEO.value)
        is_text = (data.lesson_type == LessonType.TEXT) or (isinstance(data.lesson_type, str) and data.lesson_type == LessonType.TEXT.value)
        
        lesson = Lesson(
            module_id=module_id,
            title=data.title,
            lesson_type=lesson_type_value,
            video_url=data.video_url if is_video else None,
            content_text=data.content_text if is_text else None,
            duration_minutes=data.duration_minutes,
            order=data.order if data.order > 0 else max_order + 1
        )
        
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson
    
    def update_lesson(self, lesson_id: int, current_user: User, data: LessonCreateDTO) -> Lesson:
        """Update a lesson."""
        from app.models.enums import LessonType
        
        lesson = self._get_lesson_with_access(lesson_id, current_user)
        
        lesson.title = data.title
        if data.lesson_type:
            lesson.lesson_type = data.lesson_type.value if hasattr(data.lesson_type, 'value') else data.lesson_type
        
        # Отримуємо поточний тип уроку
        current_type = lesson.lesson_type or LessonType.TEXT.value
        
        # Оновлюємо поля залежно від типу уроку
        if current_type == LessonType.VIDEO.value:
            lesson.video_url = data.video_url
            lesson.content_text = None
        elif current_type == LessonType.TEXT.value:
            lesson.content_text = data.content_text
            lesson.video_url = None
        elif current_type == LessonType.QUIZ.value:
            lesson.video_url = None
            lesson.content_text = None
        else:
            # Якщо тип не вказано, зберігаємо обидва поля
            if data.video_url is not None:
                lesson.video_url = data.video_url
            if data.content_text is not None:
                lesson.content_text = data.content_text
        
        lesson.duration_minutes = data.duration_minutes
        if data.order > 0:
            lesson.order = data.order
        
        self.db.commit()
        self.db.refresh(lesson)
        return lesson
    
    def delete_lesson(self, lesson_id: int, current_user: User) -> bool:
        """Delete a lesson."""
        lesson = self._get_lesson_with_access(lesson_id, current_user)
        self.db.delete(lesson)
        self.db.commit()
        return True
    
    def add_quiz(self, lesson_id: int, current_user: User, data: QuizCreateDTO) -> Quiz:
        """
        Add a quiz to a lesson.
        
        Args:
            lesson_id: Lesson ID
            current_user: Authenticated user
            data: Quiz creation data
        
        Returns:
            Created Quiz instance
        """
        lesson = self._get_lesson_with_access(lesson_id, current_user)
        
        # Check if quiz already exists
        if lesson.quiz:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson already has a quiz"
            )
        
        quiz = Quiz(
            lesson_id=lesson_id,
            title=data.title,
            passing_score=data.passing_score
        )
        
        self.db.add(quiz)
        self.db.flush()  # Get quiz ID
        
        # Add questions (якщо вони є)
        if data.questions:
            for q_data in data.questions:
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q_data.question_text,
                    options=q_data.options,
                    correct_option_index=q_data.correct_option_index,
                    points=q_data.points if hasattr(q_data, 'points') and q_data.points else 1
                )
                self.db.add(question)
        
        self.db.commit()
        self.db.refresh(quiz)
        return quiz
    
    def update_quiz(self, lesson_id: int, current_user: User, data: QuizCreateDTO) -> Quiz:
        """
        Update quiz for a lesson (delete old questions and add new ones).
        
        Args:
            lesson_id: Lesson ID
            current_user: Authenticated user
            data: Quiz update data
        
        Returns:
            Updated Quiz instance
        """
        lesson = self._get_lesson_with_access(lesson_id, current_user)
        
        if not lesson.quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found for this lesson"
            )
        
        quiz = lesson.quiz
        
        # Update quiz title and passing score (завжди оновлюємо, навіть якщо порожні)
        quiz.title = data.title if data.title else quiz.title
        quiz.passing_score = data.passing_score if data.passing_score is not None else quiz.passing_score
        
        # Delete old questions using query to ensure they are deleted
        from sqlalchemy.orm import joinedload
        # Спочатку завантажуємо всі питання
        old_questions = self.db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz.id).all()
        logger.info(f"Deleting {len(old_questions)} old questions for quiz {quiz.id}")
        for question in old_questions:
            self.db.delete(question)
        self.db.flush()  # Виконуємо видалення перед додаванням нових
        
        # Add new questions (якщо вони є)
        questions_count = len(data.questions) if data.questions else 0
        logger.info(f"Updating quiz {quiz.id}: received {questions_count} questions")
        logger.info(f"Quiz data: title='{data.title}', passing_score={data.passing_score}")
        
        if data.questions and len(data.questions) > 0:
            for idx, q_data in enumerate(data.questions):
                logger.info(f"Adding question {idx + 1}: text='{q_data.question_text[:50]}...', options={len(q_data.options) if q_data.options else 0}, correct={q_data.correct_option_index}, points={q_data.points if hasattr(q_data, 'points') else 1}")
                question = QuizQuestion(
                    quiz_id=quiz.id,
                    question_text=q_data.question_text,
                    options=q_data.options,
                    correct_option_index=q_data.correct_option_index,
                    points=q_data.points if hasattr(q_data, 'points') and q_data.points else 1
                )
                self.db.add(question)
        else:
            logger.info(f"No questions to add for quiz {quiz.id}")
        
        try:
            self.db.commit()
            logger.info(f"Quiz {quiz.id} commit successful")
        except Exception as e:
            logger.error(f"Error committing quiz {quiz.id}: {e}")
            self.db.rollback()
            raise
        
        # Перезавантажуємо quiz з питаннями після commit (використовуємо новий query)
        quiz_loaded = self.db.query(Quiz).options(joinedload(Quiz.questions)).filter(Quiz.id == quiz.id).first()
        
        if not quiz_loaded:
            logger.error(f"Quiz {quiz.id} not found after commit!")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Quiz not found after update")
        
        # Перевіряємо, чи питання збереглися
        questions_saved = len(quiz_loaded.questions) if quiz_loaded.questions else 0
        logger.info(f"Quiz {quiz.id} after update: {questions_saved} questions saved in DB")
        if questions_saved > 0:
            for idx, q in enumerate(quiz_loaded.questions):
                logger.info(f"  Saved question {idx + 1}: {q.question_text[:50]}... ({len(q.options)} options, correct={q.correct_option_index}, points={q.points})")
        else:
            logger.warning(f"Quiz {quiz.id} has no questions after update!")
        
        return quiz_loaded
    
    def delete_course(self, course_id: int, current_user: User) -> bool:
        course = self._get_course_with_access(course_id, current_user)
        self.db.delete(course)
        self.db.commit()
        return True
    
    def publish_course(self, course_id: int, current_user: User) -> bool:
        """Publish a course."""
        course = self._get_course_with_access(course_id, current_user)
        
        if not course.modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course must have at least one module to publish"
            )
        
        course.is_published = True
        self.db.commit()
        return True
    
    def unpublish_course(self, course_id: int, current_user: User) -> bool:
        """Unpublish a course."""
        course = self._get_course_with_access(course_id, current_user)
        course.is_published = False
        self.db.commit()
        return True
    
    # ===== Helper methods =====
    def _resolve_teacher_id(self, teacher_id: Optional[int]) -> int:
        """Validate and return teacher_id for admin operations."""
        if not teacher_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="teacher_id is required for admin operations"
            )
        
        teacher = self.db.query(User).filter(
            User.id == teacher_id,
            User.role == UserRole.TEACHER
        ).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified teacher not found"
            )
        return teacher.id
    
    def _has_admin_privileges(self, user: User) -> bool:
        return user.role == UserRole.ADMIN
    
    def _get_course_with_access(self, course_id: int, current_user: User) -> Course:
        """Retrieve a course ensuring the user has permission."""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        if not self._has_admin_privileges(current_user) and course.teacher_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this course"
            )
        return course
    
    def _get_module_with_access(self, module_id: int, current_user: User) -> Module:
        """Retrieve a module ensuring the user has permission via course."""
        module = self.db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        self._get_course_with_access(module.course_id, current_user)
        return module
    
    def _get_lesson_with_access(self, lesson_id: int, current_user: User) -> Lesson:
        """Retrieve a lesson ensuring the user has permission via module/course."""
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        self._get_module_with_access(lesson.module_id, current_user)
        return lesson


