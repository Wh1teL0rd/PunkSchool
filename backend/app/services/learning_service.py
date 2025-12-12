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
        Enroll a student in a course.
        
        Args:
            student_id: Student's user ID
            course_id: Course ID
        
        Returns:
            Created Enrollment instance
        
        Raises:
            HTTPException: If already enrolled or course not found
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
        
        # Calculate score
        total_questions = len(quiz.questions)
        correct_answers = 0
        
        for question in quiz.questions:
            student_answer = answers.get(str(question.id))
            if student_answer == question.correct_option_index:
                correct_answers += 1
        
        score = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
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
            Lesson instance
        """
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
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
