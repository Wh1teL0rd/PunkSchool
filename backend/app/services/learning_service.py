"""
Learning service - for students to enroll and progress through courses.
"""
import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.course import (
    Course, Module, Lesson, Enrollment, 
    Quiz, QuizQuestion, QuizAttempt, Certificate, Transaction
)
from app.models.user import User


class LearningService:
    """
    Service for student learning operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def enroll_student(self, student_id: int, course_id: int) -> Enrollment:
        """
        Enroll a student in a course with payment processing.
        
        Args:
            student_id: Student's user ID
            course_id: Course ID
        
        Returns:
            Created Enrollment instance
        
        Raises:
            HTTPException: If already enrolled, course not found, or insufficient balance
        """
        # Check if course exists and is published
        course = self.db.query(Course).filter(
            Course.id == course_id,
            Course.is_published == True
        ).first()
        
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or not published"
            )
        
        # Check if already enrolled
        existing = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already enrolled in this course"
            )
        
        # Get student and teacher
        student = self.db.query(User).filter(User.id == student_id).first()
        teacher = self.db.query(User).filter(User.id == course.teacher_id).first()
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )
        
        # Check balance if course is not free
        if course.price > 0:
            if student.balance < course.price:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient balance. Required: {course.price} ₴, Available: {student.balance} ₴"
                )
            
            # Deduct from student balance
            student.balance -= course.price
            
            # Add to teacher balance
            teacher.balance += course.price
        
        # Create enrollment
        enrollment = Enrollment(
            student_id=student_id,
            course_id=course_id,
            progress_percent=0.0,
            is_completed=False,
            completed_lessons=[]
        )
        
        self.db.add(enrollment)
        
        # Create transaction record
        transaction = Transaction(
            user_id=student_id,
            course_id=course_id,
            amount=course.price,
            date=datetime.utcnow()
        )
        self.db.add(transaction)
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def complete_module(self, student_id: int, module_id: int) -> Enrollment:
        """
        Mark a module as completed for a student (only if all lessons are completed).
        
        Args:
            student_id: Student's user ID
            module_id: Module ID
        
        Returns:
            Updated Enrollment instance
        
        Raises:
            HTTPException: If module not found, not enrolled, or not all lessons completed
        """
        # Get module and its course
        module = self.db.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Module not found"
            )
        
        course = module.course
        enrollment = self.get_enrollment(student_id, course.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        # Check if all lessons in module are completed
        completed_lessons = enrollment.completed_lessons or []
        module_lesson_ids = [lesson.id for lesson in module.lessons]
        
        if not module_lesson_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Module has no lessons"
            )
        
        if not all(lesson_id in completed_lessons for lesson_id in module_lesson_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not all lessons in this module are completed"
            )
        
        # Module is already effectively completed if all lessons are done
        # Recalculate progress
        total_lessons = sum(len(m.lessons) for m in course.modules)
        enrollment.update_progress(len(completed_lessons), total_lessons)
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def complete_course(self, student_id: int, course_id: int) -> Enrollment:
        """
        Mark a course as completed for a student (only if all modules are completed).
        
        Args:
            student_id: Student's user ID
            course_id: Course ID
        
        Returns:
            Updated Enrollment instance
        
        Raises:
            HTTPException: If course not found, not enrolled, or not all modules completed
        """
        # Get course
        course = self.db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        enrollment = self.get_enrollment(student_id, course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        # Check if all lessons in all modules are completed
        completed_lessons = enrollment.completed_lessons or []
        all_lesson_ids = []
        for module in course.modules:
            all_lesson_ids.extend([lesson.id for lesson in module.lessons])
        
        if not all_lesson_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course has no lessons"
            )
        
        if not all(lesson_id in completed_lessons for lesson_id in all_lesson_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not all lessons in this course are completed"
            )
        
        # Mark course as completed
        enrollment.is_completed = True
        enrollment.progress_percent = 100.0
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def get_student_enrollments(self, student_id: int) -> List[Enrollment]:
        """Get all enrollments for a student."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
    
    def get_enrollment(self, student_id: int, course_id: int) -> Optional[Enrollment]:
        """Get specific enrollment."""
        return self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id
        ).first()
    
    def complete_lesson(self, student_id: int, lesson_id: int) -> Enrollment:
        """
        Mark a lesson as completed for a student.
        
        Args:
            student_id: Student's user ID
            lesson_id: Lesson ID
        
        Returns:
            Updated Enrollment instance
        """
        # Get lesson and its course
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Get enrollment through module -> course
        module = lesson.module
        course = module.course
        
        enrollment = self.get_enrollment(student_id, course.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        # Add lesson to completed list if not already there
        completed = enrollment.completed_lessons or []
        if lesson_id not in completed:
            completed.append(lesson_id)
            enrollment.completed_lessons = completed
            
            # Calculate progress
            total_lessons = sum(len(m.lessons) for m in course.modules)
            enrollment.update_progress(len(completed), total_lessons)
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment
    
    def submit_quiz(self, student_id: int, quiz_id: int, answers: dict) -> QuizAttempt:
        """
        Submit quiz answers and get results.
        
        Args:
            student_id: Student's user ID
            quiz_id: Quiz ID
            answers: Dictionary of {question_id: selected_option_index}
        
        Returns:
            QuizAttempt with results
        """
        quiz = self.db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found"
            )
        
        # Verify enrollment
        lesson = quiz.lesson
        module = lesson.module
        course = module.course
        
        enrollment = self.get_enrollment(student_id, course.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        # Calculate score in points (not percentage)
        total_score = 0
        score = 0
        
        for question in quiz.questions:
            points = question.points if hasattr(question, 'points') and question.points else 1
            total_score += points
            
            # Handle both string and int question IDs
            student_answer = answers.get(str(question.id)) or answers.get(question.id)
            if student_answer is not None:
                try:
                    if int(student_answer) == question.correct_option_index:
                        score += points
                except (ValueError, TypeError):
                    pass
        
        passed = score >= quiz.passing_score
        
        # Create attempt record
        attempt = QuizAttempt(
            student_id=student_id,
            quiz_id=quiz_id,
            score=score,
            passed=passed,
            answers=answers
        )
        
        self.db.add(attempt)
        
        # If passed, mark lesson as completed
        if passed:
            self.complete_lesson(student_id, lesson.id)
        
        self.db.commit()
        self.db.refresh(attempt)
        
        # Add total_score as attribute for response
        attempt.total_score = total_score
        return attempt
    
    def get_quiz_attempts(self, student_id: int, quiz_id: int) -> List[QuizAttempt]:
        """Get all attempts for a quiz by a student."""
        return self.db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id,
            QuizAttempt.quiz_id == quiz_id
        ).order_by(QuizAttempt.attempted_at.desc()).all()
    
    def generate_certificate(self, enrollment_id: int) -> Certificate:
        """
        Generate a completion certificate for an enrollment.
        
        Args:
            enrollment_id: Enrollment ID
        
        Returns:
            Created Certificate instance
        
        Raises:
            HTTPException: If course not completed or certificate exists
        """
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.id == enrollment_id
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found"
            )
        
        if not enrollment.is_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course not completed yet"
            )
        
        # Check if certificate already exists
        if enrollment.certificate:
            return enrollment.certificate
        
        # Generate certificate
        certificate = Certificate(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment_id,
            issued_at=datetime.utcnow(),
            pdf_url=None  # Would be generated by a separate service
        )
        
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        return certificate
    
    def get_lesson_details(self, student_id: int, lesson_id: int) -> Lesson:
        """
        Get lesson details (only if enrolled).
        
        Args:
            student_id: Student's user ID
            lesson_id: Lesson ID
        
        Returns:
            Lesson instance with quiz loaded if exists
        """
        from sqlalchemy.orm import joinedload
        
        lesson = self.db.query(Lesson).options(
            joinedload(Lesson.quiz).joinedload(Quiz.questions)
        ).filter(Lesson.id == lesson_id).first()
        
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Verify enrollment
        course = lesson.module.course
        enrollment = self.get_enrollment(student_id, course.id)
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        return lesson
