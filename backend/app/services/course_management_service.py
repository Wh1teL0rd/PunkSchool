"""
Course management service - for teachers to create and manage courses.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.course import Course, Module, Lesson, Quiz, QuizQuestion
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
    
    def create_course(self, teacher_id: int, data: CourseCreateDTO) -> Course:
        """
        Create a new course.
        
        Args:
            teacher_id: Teacher's user ID
            data: Course creation data
        
        Returns:
            Created Course instance
        """
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
    
    def update_course(self, course_id: int, teacher_id: int, data: CourseUpdateDTO) -> Course:
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
        course = self._get_teacher_course(course_id, teacher_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(course, field, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course
    
    def delete_course(self, course_id: int, teacher_id: int) -> bool:
        """Delete a course."""
        course = self._get_teacher_course(course_id, teacher_id)
        self.db.delete(course)
        self.db.commit()
        return True
    
    def add_module(self, course_id: int, teacher_id: int, data: ModuleCreateDTO) -> Module:
        """
        Add a module to a course.
        
        Args:
            course_id: Course ID
            teacher_id: Teacher's user ID
            data: Module creation data
        
        Returns:
            Created Module instance
        """
        course = self._get_teacher_course(course_id, teacher_id)
        
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
    
    def update_module(self, module_id: int, teacher_id: int, title: str) -> Module:
        """Update a module's title."""
        module = self._get_teacher_module(module_id, teacher_id)
        module.title = title
        self.db.commit()
        self.db.refresh(module)
        return module
    
    def delete_module(self, module_id: int, teacher_id: int) -> bool:
        """Delete a module."""
        module = self._get_teacher_module(module_id, teacher_id)
        self.db.delete(module)
        self.db.commit()
        return True
    
    def add_lesson(self, module_id: int, teacher_id: int, data: LessonCreateDTO) -> Lesson:
        """
        Add a lesson to a module.
        
        Args:
            module_id: Module ID
            teacher_id: Teacher's user ID
            data: Lesson creation data
        
        Returns:
            Created Lesson instance
        """
        module = self._get_teacher_module(module_id, teacher_id)
        
        # Get next order number
        max_order = max((l.order for l in module.lessons), default=-1)
        
        lesson = Lesson(
            module_id=module_id,
            title=data.title,
            video_url=data.video_url,
            content_text=data.content_text,
            duration_minutes=data.duration_minutes,
            order=data.order if data.order > 0 else max_order + 1
        )
        
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson
    
    def update_lesson(self, lesson_id: int, teacher_id: int, data: LessonCreateDTO) -> Lesson:
        """Update a lesson."""
        lesson = self._get_teacher_lesson(lesson_id, teacher_id)
        
        lesson.title = data.title
        lesson.video_url = data.video_url
        lesson.content_text = data.content_text
        lesson.duration_minutes = data.duration_minutes
        if data.order > 0:
            lesson.order = data.order
        
        self.db.commit()
        self.db.refresh(lesson)
        return lesson
    
    def delete_lesson(self, lesson_id: int, teacher_id: int) -> bool:
        """Delete a lesson."""
        lesson = self._get_teacher_lesson(lesson_id, teacher_id)
        self.db.delete(lesson)
        self.db.commit()
        return True
    
    def add_quiz(self, lesson_id: int, teacher_id: int, data: QuizCreateDTO) -> Quiz:
        """
        Add a quiz to a lesson.
        
        Args:
            lesson_id: Lesson ID
            teacher_id: Teacher's user ID
            data: Quiz creation data
        
        Returns:
            Created Quiz instance
        """
        lesson = self._get_teacher_lesson(lesson_id, teacher_id)
        
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
        
        # Add questions
        for q_data in data.questions:
            question = QuizQuestion(
                quiz_id=quiz.id,
                question_text=q_data.question_text,
                options=q_data.options,
                correct_option_index=q_data.correct_option_index
            )
            self.db.add(question)
        
        self.db.commit()
        self.db.refresh(quiz)
        return quiz
    
    def publish_course(self, course_id: int, teacher_id: int) -> bool:
        """
        Publish a course (make it visible to students).
        
        Args:
            course_id: Course ID
            teacher_id: Teacher's user ID
        
        Returns:
            True if published successfully
        """
        course = self._get_teacher_course(course_id, teacher_id)
        
        # Validate course has content
        if not course.modules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course must have at least one module to publish"
            )
        
        course.is_published = True
        self.db.commit()
        return True
    
    def unpublish_course(self, course_id: int, teacher_id: int) -> bool:
        """Unpublish a course."""
        course = self._get_teacher_course(course_id, teacher_id)
        course.is_published = False
        self.db.commit()
        return True
    
    def _get_teacher_course(self, course_id: int, teacher_id: int) -> Course:
        """Get course and verify teacher ownership."""
        course = self.db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        if course.teacher_id != teacher_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to modify this course"
            )
        
        return course
    
    def _get_teacher_module(self, module_id: int, teacher_id: int) -> Module:
        """Get module and verify teacher ownership via course."""
        module = self.db.query(Module).filter(Module.id == module_id).first()
        
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        # Verify ownership through course
        self._get_teacher_course(module.course_id, teacher_id)
        return module
    
    def _get_teacher_lesson(self, lesson_id: int, teacher_id: int) -> Lesson:
        """Get lesson and verify teacher ownership via module/course."""
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Verify ownership through module -> course
        self._get_teacher_module(lesson.module_id, teacher_id)
        return lesson

