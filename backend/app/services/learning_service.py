"""
Learning service - for students to enroll and progress through courses.
"""
import os
import uuid
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import pdfkit

from app.core.config import settings
from app.models.course import (
    Course, Module, Lesson, Enrollment, 
    Quiz, QuizQuestion, QuizAttempt, Certificate, Transaction
)
from app.models.user import User


PDFKIT_OPTIONS = {
    "page-size": "A4",
    "margin-top": "0.75in",
    "margin-bottom": "0.75in",
    "margin-left": "0.75in",
    "margin-right": "0.75in",
    "encoding": "UTF-8",
}


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
    
    def reset_lesson_completion(self, student_id: int, lesson_id: int) -> Enrollment:
        """
        Remove a lesson from the completed list so student can retake it.
        """
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        course = lesson.module.course
        enrollment = self.get_enrollment(student_id, course.id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enrolled in this course"
            )
        
        completed = enrollment.completed_lessons or []
        if lesson_id in completed:
            completed.remove(lesson_id)
            enrollment.completed_lessons = completed
            
            total_lessons = sum(len(m.lessons) for m in course.modules)
            enrollment.update_progress(len(completed), total_lessons)
            if enrollment.progress_percent < 100:
                enrollment.is_completed = False
        
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
    
    def _prepare_enrollment_certificate(self, enrollment: Optional[Enrollment]) -> Optional[Enrollment]:
        if enrollment and enrollment.certificate:
            self._ensure_certificate_file(enrollment, enrollment.certificate)
            enrollment.certificate = self._attach_certificate_metadata(enrollment.certificate)
        return enrollment
    
    def get_student_enrollments(self, student_id: int) -> List[Enrollment]:
        """Get all enrollments for a student."""
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
        return [self._prepare_enrollment_certificate(enrollment) for enrollment in enrollments]
    
    def get_enrollment(self, student_id: int, course_id: int) -> Optional[Enrollment]:
        """Get specific enrollment."""
        enrollment = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id
        ).first()
        return self._prepare_enrollment_certificate(enrollment)
    
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
    
    def _get_certificate_base_dir(self) -> str:
        base_dir = os.path.abspath(settings.CERTIFICATES_DIR)
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    def _get_certificate_file_path(self, enrollment: Enrollment, certificate_id: str) -> str:
        base_dir = self._get_certificate_base_dir()
        student_dir = os.path.join(base_dir, f"student_{enrollment.student_id}")
        os.makedirs(student_dir, exist_ok=True)
        return os.path.join(student_dir, f"{certificate_id}.pdf")
    
    def _calculate_course_duration_minutes(self, course: Course) -> int:
        total_duration = 0
        for module in course.modules:
            total_duration += sum((lesson.duration_minutes or 0) for lesson in module.lessons)
        return total_duration
    
    def _build_certificate_html(self, *, student_name: str, course_title: str, issue_date: datetime, total_hours: float, certificate_id: str) -> str:
        issue_date_str = issue_date.strftime("%d.%m.%Y")
        total_hours_display = f"{total_hours:.1f}"
        return f"""
        <!DOCTYPE html>
        <html lang="uk">
          <head>
            <meta charset="UTF-8" />
            <style>
              body {{
                font-family: 'Segoe UI', 'Arial', sans-serif;
                background: #fdfcf8;
                color: #1f2937;
              }}
              .certificate-container {{
                border: 8px double #c4a36e;
                padding: 40px 50px;
                text-align: center;
              }}
              h1 {{
                font-size: 36px;
                margin-bottom: 0.5rem;
                letter-spacing: 4px;
                color: #8c6a27;
                text-transform: uppercase;
              }}
              h2 {{
                font-size: 28px;
                margin-top: 0;
                color: #374151;
              }}
              .student-name {{
                font-size: 32px;
                font-weight: 700;
                color: #111827;
                margin: 1.5rem 0 0.5rem;
              }}
              .divider {{
                width: 120px;
                height: 3px;
                background: linear-gradient(90deg, #f59e0b, #f97316);
                margin: 1rem auto 1.5rem;
              }}
              .details {{
                font-size: 18px;
                line-height: 1.7;
                color: #374151;
              }}
              .footer {{
                margin-top: 2rem;
                display: flex;
                justify-content: space-between;
                font-size: 16px;
                color: #4b5563;
              }}
              .signature {{
                margin-top: 2rem;
                font-weight: 600;
                color: #1f2937;
              }}
              .highlight {{
                color: #b45309;
                font-weight: 600;
              }}
            </style>
          </head>
          <body>
            <div class="certificate-container">
              <h1>Сертифікат</h1>
              <h2>про завершення курсу</h2>
              <div class="divider"></div>
              <div class="student-name">{student_name}</div>
              <p class="details">
                успішно завершив(ла) курс <br />
                <span class="highlight">«{course_title}»</span><br />
                загальною тривалістю <strong>{total_hours_display} годин</strong>.
              </p>
              <div class="footer">
                <div>
                  Дата видачі:<br />
                  <strong>{issue_date_str}</strong>
                </div>
                <div>
                  Номер сертифікату:<br />
                  <strong>{certificate_id}</strong>
                </div>
              </div>
              <div class="signature">
                Music Course Platform
              </div>
            </div>
          </body>
        </html>
        """
    
    def _attach_certificate_metadata(self, certificate: Certificate) -> Certificate:
        enrollment = certificate.enrollment
        course = enrollment.course
        total_minutes = self._calculate_course_duration_minutes(course)
        total_hours = round(max(total_minutes / 60.0, 1), 1)
        certificate.course_title = course.title
        certificate.student_name = enrollment.student.full_name
        certificate.total_hours = total_hours
        certificate.download_url = f"/api/students/certificates/{certificate.id}/download"
        return certificate
    
    def _ensure_certificate_file(self, enrollment: Enrollment, certificate: Certificate) -> None:
        pdf_path = self._get_certificate_file_path(enrollment, certificate.id)
        if os.path.exists(pdf_path):
            return
        
        total_minutes = self._calculate_course_duration_minutes(enrollment.course)
        total_hours = round(max(total_minutes / 60.0, 1), 1)
        html_content = self._build_certificate_html(
            student_name=enrollment.student.full_name,
            course_title=enrollment.course.title,
            issue_date=certificate.issued_at,
            total_hours=total_hours,
            certificate_id=certificate.id
        )
        
        try:
            pdfkit.from_string(html_content, pdf_path, options=PDFKIT_OPTIONS)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Не вдалося згенерувати PDF. Переконайтеся, що wkhtmltopdf встановлено на сервері."
            ) from exc
    
    def get_certificate_download(self, student_id: int, certificate_id: str) -> Tuple[Certificate, str]:
        certificate = self.db.query(Certificate).join(Enrollment).filter(
            Certificate.id == certificate_id,
            Enrollment.student_id == student_id
        ).first()
        
        if not certificate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certificate not found"
            )
        
        enrollment = certificate.enrollment
        self._ensure_certificate_file(enrollment, certificate)
        file_path = self._get_certificate_file_path(enrollment, certificate.id)
        certificate = self._attach_certificate_metadata(certificate)
        return certificate, file_path
    
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
            self._ensure_certificate_file(enrollment, enrollment.certificate)
            enrollment.certificate.pdf_url = f"/api/students/certificates/{enrollment.certificate.id}/download"
            return self._attach_certificate_metadata(enrollment.certificate)
        
        # Generate certificate record
        certificate = Certificate(
            id=str(uuid.uuid4()),
            enrollment_id=enrollment_id,
            issued_at=datetime.utcnow()
        )
        
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        
        # Render PDF and update metadata
        self._ensure_certificate_file(enrollment, certificate)
        certificate.pdf_url = f"/api/students/certificates/{certificate.id}/download"
        self.db.commit()
        self.db.refresh(certificate)
        return self._attach_certificate_metadata(certificate)
    
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
