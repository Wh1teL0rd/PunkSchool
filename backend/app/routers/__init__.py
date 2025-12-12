"""
Routers package - API endpoints.
"""
from app.routers.auth import router as auth_router
from app.routers.courses import router as courses_router
from app.routers.students import router as students_router
from app.routers.analytics import router as analytics_router

__all__ = [
    "auth_router",
    "courses_router",
    "students_router",
    "analytics_router",
]
