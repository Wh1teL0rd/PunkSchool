"""
Analytics API endpoints - Reports and statistics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User
from app.models.enums import UserRole
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/teacher/revenue")
async def get_teacher_revenue(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get revenue statistics for the teacher."""
    service = AnalyticsService(db)
    return service.get_teacher_revenue(current_user.id, days)


@router.get("/courses/popularity")
async def get_course_popularity(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get course popularity statistics."""
    service = AnalyticsService(db)
    return service.get_course_popularity_stats()


@router.get("/platform")
async def get_platform_stats(
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """Get overall platform statistics (Admin only)."""
    service = AnalyticsService(db)
    return service.get_platform_stats()


