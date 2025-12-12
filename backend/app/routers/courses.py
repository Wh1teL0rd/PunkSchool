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
    course = service.create_course(current_user.id, data)
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
    course = service.update_course(course_id, current_user.id, data)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a course (Owner only)."""
    service = CourseManagementService(db)
    service.delete_course(course_id, current_user.id)


@router.post("/{course_id}/publish", response_model=dict)
async def publish_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Publish a course (Owner only)."""
    service = CourseManagementService(db)
    service.publish_course(course_id, current_user.id)
    return {"message": "Course published successfully"}


@router.post("/{course_id}/unpublish", response_model=dict)
async def unpublish_course(
    course_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Unpublish a course (Owner only)."""
    service = CourseManagementService(db)
    service.unpublish_course(course_id, current_user.id)
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
    module = service.add_module(course_id, current_user.id, data)
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
    module = service.update_module(module_id, current_user.id, title)
    return module


@router.delete("/modules/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_module(
    module_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a module (Owner only)."""
    service = CourseManagementService(db)
    service.delete_module(module_id, current_user.id)


# ============== Lesson endpoints ==============

@router.post("/modules/{module_id}/lessons", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def add_lesson(
    module_id: int,
    data: LessonCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a lesson to a module (Owner only)."""
    service = CourseManagementService(db)
    lesson = service.add_lesson(module_id, current_user.id, data)
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
    lesson = service.update_lesson(lesson_id, current_user.id, data)
    return lesson


@router.delete("/lessons/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson(
    lesson_id: int,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Delete a lesson (Owner only)."""
    service = CourseManagementService(db)
    service.delete_lesson(lesson_id, current_user.id)


# ============== Quiz endpoints ==============

@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResponse, status_code=status.HTTP_201_CREATED)
async def add_quiz(
    lesson_id: int,
    data: QuizCreateDTO,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Add a quiz to a lesson (Owner only)."""
    service = CourseManagementService(db)
    quiz = service.add_quiz(lesson_id, current_user.id, data)
    return quiz


# ============== Teacher's courses ==============

@router.get("/my/teaching", response_model=List[CourseResponse])
async def get_my_courses(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get courses created by the current teacher."""
    service = CourseCatalogService(db)
    return service.get_courses_by_teacher(current_user.id)
