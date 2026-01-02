"""
Course catalog service - handles course browsing and searching.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.course import Course, Module, Lesson
from app.models.enums import CourseCategory, DifficultyLevel
from app.services.sorting_strategy import ICourseSortStrategy, get_sort_strategy


class CourseCatalogService:
    """
    Service for course catalog operations.
    Uses Strategy pattern for sorting.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_courses(
        self,
        category: Optional[CourseCategory] = None,
        level: Optional[DifficultyLevel] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        teacher_search: Optional[str] = None,
        sort_strategy: Optional[ICourseSortStrategy] = None,
        published_only: bool = True
    ) -> List[Course]:
        """
        Get all courses with optional filters and sorting.
        Uses Strategy pattern for sorting.
        
        Args:
            category: Filter by category
            level: Filter by difficulty level
            min_price: Minimum price filter
            max_price: Maximum price filter
            teacher_search: Search by teacher name or email
            sort_strategy: Sorting strategy (Strategy pattern)
            published_only: Only return published courses
        
        Returns:
            List of filtered and sorted courses
        """
        from app.models.user import User
        
        query = self.db.query(Course)
        
        # Apply filters
        if published_only:
            query = query.filter(Course.is_published == True)
        
        if category:
            query = query.filter(Course.category == category)
        
        if level:
            query = query.filter(Course.level == level)
        
        if min_price is not None:
            query = query.filter(Course.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Course.price <= max_price)
        
        # Filter by teacher name or email
        if teacher_search and teacher_search.strip():
            search_term = f"%{teacher_search.strip()}%"
            query = query.join(User, Course.teacher_id == User.id).filter(
                or_(
                    User.full_name.ilike(search_term),
                    User.email.ilike(search_term)
                )
            )
        
        # Apply sorting strategy
        if sort_strategy:
            query = sort_strategy.sort(query)
        
        return query.all()
    
    def get_course_details(self, course_id: int) -> Optional[Course]:
        """
        Get detailed course information including modules and lessons.
        
        Args:
            course_id: Course ID
        
        Returns:
            Course with all related data or None
        """
        from sqlalchemy.orm import joinedload
        from app.models.course import Module, Lesson
        from app.models.enums import LessonType
        
        # Спочатку завантажуємо курс без eager loading, щоб уникнути проблем з ENUM
        course = self.db.query(Course).filter(Course.id == course_id).first()
        
        if not course:
            return None
        
        # Завантажуємо модулі та уроки окремо з обробкою помилок ENUM
        try:
            # Отримуємо модулі
            modules = self.db.query(Module).filter(Module.course_id == course_id).all()
            course.modules = modules
            
            # Отримуємо уроки для кожного модуля
            for module in modules:
                lessons = self.db.query(Lesson).filter(Lesson.module_id == module.id).all()
                # Обробляємо кожен урок окремо
                for lesson in lessons:
                    # Якщо lesson_type не встановлено або має неправильний формат, встановлюємо за замовчуванням
                    if not lesson.lesson_type or lesson.lesson_type not in [e.value for e in LessonType]:
                        lesson.lesson_type = LessonType.TEXT.value
                        self.db.commit()
                        self.db.refresh(lesson)
                module.lessons = lessons
        except Exception as e:
            print(f"Warning: Error loading lessons: {e}")
        
        return course
    
    def search_courses(self, keyword: str, published_only: bool = True) -> List[Course]:
        """
        Search courses by keyword in title and description.
        
        Args:
            keyword: Search keyword
            published_only: Only return published courses
        
        Returns:
            List of matching courses
        """
        query = self.db.query(Course)
        
        if published_only:
            query = query.filter(Course.is_published == True)
        
        search_filter = or_(
            Course.title.ilike(f"%{keyword}%"),
            Course.description.ilike(f"%{keyword}%")
        )
        
        return query.filter(search_filter).all()
    
    def get_courses_by_teacher(self, teacher_id: int) -> List[Course]:
        """Get all courses by a specific teacher."""
        return self.db.query(Course).filter(Course.teacher_id == teacher_id).all()
    
    def get_course_stats(self, course_id: int) -> dict:
        """
        Get course statistics (total modules, lessons, duration).
        
        Args:
            course_id: Course ID
        
        Returns:
            Dictionary with course statistics
        """
        course = self.get_course_details(course_id)
        if not course:
            return {}
        
        total_lessons = 0
        total_duration = 0
        
        for module in course.modules:
            total_lessons += len(module.lessons)
            total_duration += sum(lesson.duration_minutes for lesson in module.lessons)
        
        return {
            "total_modules": len(course.modules),
            "total_lessons": total_lessons,
            "total_duration_minutes": total_duration
        }


