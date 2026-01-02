"""
Analytics service - for reports and statistics.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.course import Course, Enrollment, Transaction, QuizAttempt
from app.models.user import User
from app.models.enums import UserRole


class AnalyticsService:
    """
    Service for analytics and reporting.
    Used by admins and teachers.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_teacher_revenue(self, teacher_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get revenue statistics for a teacher.
        
        Args:
            teacher_id: Teacher's user ID
            days: Number of days to look back
        
        Returns:
            Dictionary with revenue statistics
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total revenue
        total_revenue = self.db.query(func.sum(Transaction.amount)).join(
            Course, Transaction.course_id == Course.id
        ).filter(
            Course.teacher_id == teacher_id
        ).scalar() or 0.0
        
        # Get revenue in period
        period_revenue = self.db.query(func.sum(Transaction.amount)).join(
            Course, Transaction.course_id == Course.id
        ).filter(
            Course.teacher_id == teacher_id,
            Transaction.date >= since_date
        ).scalar() or 0.0
        
        # Get transaction count
        transaction_count = self.db.query(func.count(Transaction.id)).join(
            Course, Transaction.course_id == Course.id
        ).filter(
            Course.teacher_id == teacher_id,
            Transaction.date >= since_date
        ).scalar() or 0
        
        # Get revenue by course
        revenue_by_course = self.db.query(
            Course.title,
            func.sum(Transaction.amount).label('revenue'),
            func.count(Transaction.id).label('sales')
        ).join(
            Transaction, Transaction.course_id == Course.id
        ).filter(
            Course.teacher_id == teacher_id
        ).group_by(Course.id).all()
        
        return {
            "total_revenue": total_revenue,
            "period_revenue": period_revenue,
            "period_days": days,
            "transaction_count": transaction_count,
            "revenue_by_course": [
                {"title": r[0], "revenue": r[1], "sales": r[2]}
                for r in revenue_by_course
            ]
        }
    
    def get_course_popularity_stats(self) -> Dict[str, Any]:
        """
        Get course popularity statistics.
        
        Returns:
            Dictionary with popularity statistics
        """
        # Most enrolled courses
        popular_courses = self.db.query(
            Course.id,
            Course.title,
            Course.category,
            func.count(Enrollment.id).label('enrollment_count')
        ).outerjoin(
            Enrollment, Enrollment.course_id == Course.id
        ).filter(
            Course.is_published == True
        ).group_by(Course.id).order_by(
            func.count(Enrollment.id).desc()
        ).limit(10).all()
        
        # Category statistics
        category_stats = self.db.query(
            Course.category,
            func.count(Course.id).label('course_count'),
            func.count(Enrollment.id).label('total_enrollments')
        ).outerjoin(
            Enrollment, Enrollment.course_id == Course.id
        ).filter(
            Course.is_published == True
        ).group_by(Course.category).all()
        
        # Total counts
        total_courses = self.db.query(func.count(Course.id)).filter(
            Course.is_published == True
        ).scalar() or 0
        
        total_enrollments = self.db.query(func.count(Enrollment.id)).scalar() or 0
        
        return {
            "total_published_courses": total_courses,
            "total_enrollments": total_enrollments,
            "popular_courses": [
                {
                    "id": c[0],
                    "title": c[1],
                    "category": c[2].value,
                    "enrollment_count": c[3]
                }
                for c in popular_courses
            ],
            "category_stats": [
                {
                    "category": c[0].value,
                    "course_count": c[1],
                    "total_enrollments": c[2]
                }
                for c in category_stats
            ]
        }
    
    def get_student_progress_stats(self, student_id: int) -> Dict[str, Any]:
        """
        Get progress statistics for a student.
        
        Args:
            student_id: Student's user ID
        
        Returns:
            Dictionary with progress statistics
        """
        # Get all enrollments
        enrollments = self.db.query(Enrollment).filter(
            Enrollment.student_id == student_id
        ).all()
        
        total_courses = len(enrollments)
        completed_courses = sum(1 for e in enrollments if e.is_completed)
        in_progress = total_courses - completed_courses
        
        # Average progress
        avg_progress = sum(e.progress_percent for e in enrollments) / total_courses if total_courses > 0 else 0
        
        # Quiz statistics
        quiz_attempts = self.db.query(QuizAttempt).filter(
            QuizAttempt.student_id == student_id
        ).all()
        
        total_quizzes = len(quiz_attempts)
        passed_quizzes = sum(1 for q in quiz_attempts if q.passed)
        avg_quiz_score = sum(q.score for q in quiz_attempts) / total_quizzes if total_quizzes > 0 else 0
        
        # Detailed enrollment progress
        enrollment_details = []
        for e in enrollments:
            course = e.course
            enrollment_details.append({
                "course_id": course.id,
                "course_title": course.title,
                "progress_percent": e.progress_percent,
                "is_completed": e.is_completed,
                "enrolled_at": e.enrolled_at.isoformat(),
                "has_certificate": e.certificate is not None
            })
        
        return {
            "total_courses": total_courses,
            "completed_courses": completed_courses,
            "in_progress_courses": in_progress,
            "average_progress": round(avg_progress, 2),
            "total_quiz_attempts": total_quizzes,
            "passed_quizzes": passed_quizzes,
            "average_quiz_score": round(avg_quiz_score, 2),
            "enrollments": enrollment_details
        }
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """
        Get overall platform statistics (admin only).
        
        Returns:
            Dictionary with platform statistics
        """
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        total_students = self.db.query(func.count(User.id)).filter(
            User.role == UserRole.STUDENT
        ).scalar() or 0
        total_teachers = self.db.query(func.count(User.id)).filter(
            User.role == UserRole.TEACHER
        ).scalar() or 0
        
        total_courses = self.db.query(func.count(Course.id)).scalar() or 0
        published_courses = self.db.query(func.count(Course.id)).filter(
            Course.is_published == True
        ).scalar() or 0
        
        total_enrollments = self.db.query(func.count(Enrollment.id)).scalar() or 0
        completed_enrollments = self.db.query(func.count(Enrollment.id)).filter(
            Enrollment.is_completed == True
        ).scalar() or 0
        
        total_revenue = self.db.query(func.sum(Transaction.amount)).scalar() or 0.0
        
        return {
            "users": {
                "total": total_users,
                "students": total_students,
                "teachers": total_teachers
            },
            "courses": {
                "total": total_courses,
                "published": published_courses
            },
            "enrollments": {
                "total": total_enrollments,
                "completed": completed_enrollments,
                "completion_rate": round(
                    (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0, 2
                )
            },
            "revenue": {
                "total": total_revenue
            }
        }
