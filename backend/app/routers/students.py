"""
Students API endpoints - Learning and progress.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.course import (
    EnrollmentResponse,
    EnrollmentProgressDTO,
    LessonResponse,
    QuizResponse,
    QuizSubmitDTO,
    QuizAttemptResponse,
    CertificateResponse,
)
from app.services.learning_service import LearningService
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/students", tags=["Students"])


# ============== Enrollment endpoints ==============

@router.post("/enroll/{course_id}", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def enroll_in_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Enroll in a course."""
    service = LearningService(db)
    enrollment = service.enroll_student(current_user.id, course_id)
    return enrollment


@router.get("/enrollments", response_model=List[EnrollmentResponse])
async def get_my_enrollments(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get all enrollments for the current student."""
    service = LearningService(db)
    return service.get_student_enrollments(current_user.id)


@router.get("/enrollments/{course_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get enrollment status for a specific course."""
    service = LearningService(db)
    enrollment = service.get_enrollment(current_user.id, course_id)
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not enrolled in this course"
        )
    
    return enrollment


# ============== Learning endpoints ==============

@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get lesson content (must be enrolled)."""
    service = LearningService(db)
    lesson = service.get_lesson_details(current_user.id, lesson_id)
    return lesson


@router.post("/lessons/{lesson_id}/complete", response_model=EnrollmentResponse)
async def complete_lesson(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Mark a lesson as completed."""
    service = LearningService(db)
    enrollment = service.complete_lesson(current_user.id, lesson_id)
    return enrollment


# ============== Quiz endpoints ==============

@router.get("/quizzes/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get quiz questions (must be enrolled)."""
    from app.models.course import Quiz
    
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found"
        )
    
    # Verify enrollment
    service = LearningService(db)
    course = quiz.lesson.module.course
    enrollment = service.get_enrollment(current_user.id, course.id)
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enrolled in this course"
        )
    
    return quiz


@router.post("/quizzes/{quiz_id}/submit", response_model=QuizAttemptResponse)
async def submit_quiz(
    quiz_id: int,
    data: QuizSubmitDTO,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results."""
    service = LearningService(db)
    attempt = service.submit_quiz(current_user.id, quiz_id, data.answers)
    return attempt


@router.get("/quizzes/{quiz_id}/attempts", response_model=List[QuizAttemptResponse])
async def get_quiz_attempts(
    quiz_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get all attempts for a quiz."""
    service = LearningService(db)
    return service.get_quiz_attempts(current_user.id, quiz_id)


# ============== Certificate endpoints ==============

@router.post("/enrollments/{enrollment_id}/certificate", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def generate_certificate(
    enrollment_id: int,
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Generate completion certificate."""
    # Verify ownership
    from app.models.course import Enrollment
    
    enrollment = db.query(Enrollment).filter(
        Enrollment.id == enrollment_id,
        Enrollment.student_id == current_user.id
    ).first()
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    service = LearningService(db)
    certificate = service.generate_certificate(enrollment_id)
    return certificate


# ============== Progress & Analytics endpoints ==============

@router.get("/progress", response_model=dict)
async def get_my_progress(
    current_user: User = Depends(require_role([UserRole.STUDENT])),
    db: Session = Depends(get_db)
):
    """Get learning progress statistics."""
    service = AnalyticsService(db)
    return service.get_student_progress_stats(current_user.id)
