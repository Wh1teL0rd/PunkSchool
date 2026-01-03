"""
Courses API endpoints.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.enums import UserRole, CourseCategory, DifficultyLevel
from app.schemas.course import (
    CourseCreateDTO,
    CourseUpdateDTO,
    CourseResponse,
    CourseDetailResponse,
    CourseBriefResponse,
    ModuleCreateDTO,
    ModuleResponse,
    LessonCreateDTO,
    LessonResponse,
    QuizCreateDTO,
    QuizResponse,
    QuizTeacherResponse,
)
from app.services.course_catalog_service import CourseCatalogService
from app.services.course_management_service import CourseManagementService
from app.services.sorting_strategy import get_sort_strategy


router = APIRouter(prefix="/courses", tags=["Courses"])


# ============== Public endpoints (Course Catalog) ==============

@router.get("/", response_model=List[CourseBriefResponse])
async def get_courses(
    category: Optional[CourseCategory] = None,
    level: Optional[DifficultyLevel] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    teacher_search: Optional[str] = Query(None, description="Search by teacher name or email"),
    sort_by: str = Query("newest", description="Sort by: price_asc, price_desc, rating, popularity, newest, title"),
    db: Session = Depends(get_db)
):
    """
    Get all published courses with optional filters and sorting.
    Uses Strategy pattern for sorting.
    """
    service = CourseCatalogService(db)
    sort_strategy = get_sort_strategy(sort_by)
    
    courses = service.get_all_courses(
        category=category,
        level=level,
        min_price=min_price,
        max_price=max_price,
        teacher_search=teacher_search,
        sort_strategy=sort_strategy
    )
    
    return courses


@router.get("/search", response_model=List[CourseBriefResponse])
async def search_courses(
    q: str = Query(..., min_length=1, description="Search keyword"),
    db: Session = Depends(get_db)
):
    """Search courses by keyword."""
    service = CourseCatalogService(db)
    return service.search_courses(q)


@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course_details(
    course_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed course information."""
    service = CourseCatalogService(db)
    course = service.get_course_details(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Calculate statistics
    stats = service.get_course_stats(course_id)
    
    # Build response with stats
    response = CourseDetailResponse.model_validate(course)
    response.total_lessons = stats.get("total_lessons", 0)
    response.total_duration = stats.get("total_duration_minutes", 0)
    
    return response


# ============== Teacher endpoints (Course Management) ==============

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    data: CourseCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Create a new course (Teacher only)."""
    service = CourseManagementService(db)
    course = service.create_course(current_user, data)
    return course


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    data: CourseUpdateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a course (Owner only)."""
    service = CourseManagementService(db)
    course = service.update_course(course_id, current_user, data)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a course (Owner only)."""
    service = CourseManagementService(db)
    service.delete_course(course_id, current_user)


@router.post("/{course_id}/publish", response_model=dict)
async def publish_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Publish a course (Owner only)."""
    service = CourseManagementService(db)
    service.publish_course(course_id, current_user)
    return {"message": "Course published successfully"}


@router.post("/{course_id}/unpublish", response_model=dict)
async def unpublish_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Unpublish a course (Owner only)."""
    service = CourseManagementService(db)
    service.unpublish_course(course_id, current_user)
    return {"message": "Course unpublished successfully"}


# ============== Module endpoints ==============

@router.post("/{course_id}/modules", response_model=ModuleResponse, status_code=status.HTTP_201_CREATED)
async def add_module(
    course_id: int,
    data: ModuleCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a module to a course (Owner only)."""
    service = CourseManagementService(db)
    module = service.add_module(course_id, current_user, data)
    return module


@router.put("/modules/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: int,
    title: str,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a module (Owner only)."""
    service = CourseManagementService(db)
    module = service.update_module(module_id, current_user, title)
    return module


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a module (Owner only)."""
    service = CourseManagementService(db)
    service.delete_module(module_id, current_user)


# ============== Lesson endpoints ==============

@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
async def get_lesson(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get lesson details (Owner only)."""
    from sqlalchemy.orm import joinedload
    from app.models.course import Lesson
    from app.models.enums import LessonType
    
    service = CourseManagementService(db)
    # Завантажуємо урок з quiz relationship
    lesson = db.query(Lesson).options(joinedload(Lesson.quiz)).filter(Lesson.id == lesson_id).first()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Перевіряємо права доступу
    service._get_module_with_access(lesson.module_id, current_user)
    
    # Встановлюємо lesson_type за замовчуванням, якщо його немає або неправильний формат
    if not lesson.lesson_type or lesson.lesson_type not in [e.value for e in LessonType]:
        lesson.lesson_type = LessonType.TEXT.value
        db.commit()
        db.refresh(lesson)
    
    # Створюємо response з правильно встановленим has_quiz
    response = LessonResponse.model_validate(lesson)
    response.has_quiz = lesson.quiz is not None
    return response


@router.post("/modules/{module_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def add_lesson(
    module_id: int,
    data: LessonCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a lesson to a module (Owner only)."""
    service = CourseManagementService(db)
    lesson = service.add_lesson(module_id, current_user, data)
    return lesson


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    data: LessonCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update a lesson (Owner only)."""
    service = CourseManagementService(db)
    lesson = service.update_lesson(lesson_id, current_user, data)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a lesson (Owner only)."""
    service = CourseManagementService(db)
    service.delete_lesson(lesson_id, current_user)


# ============== Quiz endpoints ==============

@router.get("/lessons/{lesson_id}/quiz", response_model=QuizTeacherResponse)
async def get_lesson_quiz(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get quiz for a lesson (Owner only)."""
    from sqlalchemy.orm import joinedload
    from app.models.course import Lesson, Quiz
    from app.schemas.course import QuizTeacherResponse
    
    service = CourseManagementService(db)
    # Перевіряємо права доступу
    lesson = service._get_lesson_with_access(lesson_id, current_user)
    
    # Завантажуємо quiz з питаннями
    quiz = db.query(Quiz).options(joinedload(Quiz.questions)).filter(Quiz.lesson_id == lesson_id).first()
    
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found for this lesson"
        )
    
    # Створюємо response з повною інформацією для викладача
    response = QuizTeacherResponse.model_validate(quiz)
    return response


@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def add_quiz(
    lesson_id: int,
    data: QuizCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a quiz to a lesson (Owner only)."""
    service = CourseManagementService(db)
    quiz = service.add_quiz(lesson_id, current_user, data)
    return quiz


@router.put("/lessons/{lesson_id}/quiz", response_model=QuizTeacherResponse)
async def update_quiz(
    lesson_id: int,
    data: QuizCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Update quiz for a lesson (Owner only)."""
    from sqlalchemy.orm import joinedload
    from app.models.course import Quiz
    from app.schemas.course import QuizTeacherResponse
    
    import logging
    logger = logging.getLogger(__name__)
    
    service = CourseManagementService(db)
    questions_count = len(data.questions) if data.questions else 0
    logger.info(f"Update quiz request for lesson {lesson_id}: title='{data.title}', passing_score={data.passing_score}, questions_count={questions_count}")
    
    if data.questions:
        for idx, q in enumerate(data.questions):
            logger.info(f"  Question {idx + 1} in request: text='{q.question_text[:50]}...', options={len(q.options) if q.options else 0}, correct={q.correct_option_index}, points={q.points if hasattr(q, 'points') else 'N/A'}")
    
    quiz = service.update_quiz(lesson_id, current_user, data)
    
    # Завантажуємо quiz з питаннями для повного response
    quiz_with_questions = db.query(Quiz).options(joinedload(Quiz.questions)).filter(Quiz.id == quiz.id).first()
    
    questions_in_db = len(quiz_with_questions.questions) if quiz_with_questions and quiz_with_questions.questions else 0
    logger.info(f"Quiz {quiz.id} loaded with {questions_in_db} questions from DB")
    
    # Створюємо response з повною інформацією для викладача
    response = QuizTeacherResponse.model_validate(quiz_with_questions)
    logger.info(f"Response prepared with {len(response.questions)} questions")
    
    if response.questions:
        for idx, q in enumerate(response.questions):
            logger.info(f"  Response question {idx + 1}: text='{q.question_text[:50]}...', options={len(q.options)}, correct={q.correct_option_index}, points={q.points}")
    
    return response


# ============== Teacher's courses ==============

@router.get("/my/teaching", response_model=List[CourseResponse])
async def get_my_courses(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get courses created by the current teacher."""
    service = CourseCatalogService(db)
    return service.get_courses_by_teacher(current_user.id)


@router.get("/admin/all", response_model=List[CourseResponse])
async def get_all_courses_admin(
    category: Optional[CourseCategory] = None,
    level: Optional[DifficultyLevel] = None,
    sort_by: str = Query("newest", description="Sort strategy"),
    teacher_id: Optional[int] = Query(None, description="Filter by teacher ID"),
    include_unpublished: bool = Query(True, description="Include unpublished courses"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    """Get all courses for admin management."""
    service = CourseCatalogService(db)
    sort_strategy = get_sort_strategy(sort_by)
    courses = service.get_all_courses(
        category=category,
        level=level,
        sort_strategy=sort_strategy,
        published_only=not include_unpublished,
        teacher_id=teacher_id,
    )
    return courses
