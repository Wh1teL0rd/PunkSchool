"""
Services package - Business logic layer.
"""
from app.services.user_factory import (
    UserFactory,
    StudentFactory,
    TeacherFactory,
    AdminFactory,
    get_user_factory,
)
from app.services.sorting_strategy import (
    ICourseSortStrategy,
    SortByPrice,
    SortByRating,
    SortByPopularity,
    SortByNewest,
    SortByTitle,
    get_sort_strategy,
)
from app.services.auth_service import AuthService
from app.services.course_catalog_service import CourseCatalogService
from app.services.course_management_service import CourseManagementService
from app.services.learning_service import LearningService
from app.services.analytics_service import AnalyticsService

__all__ = [
    # Factory pattern
    "UserFactory",
    "StudentFactory",
    "TeacherFactory",
    "AdminFactory",
    "get_user_factory",
    # Strategy pattern
    "ICourseSortStrategy",
    "SortByPrice",
    "SortByRating",
    "SortByPopularity",
    "SortByNewest",
    "SortByTitle",
    "get_sort_strategy",
    # Services
    "AuthService",
    "CourseCatalogService",
    "CourseManagementService",
    "LearningService",
    "AnalyticsService",
]
