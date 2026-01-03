"""Admin-specific endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_role
from app.models.enums import UserRole
from app.schemas.user import UserResponse, UserBalanceUpdate
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by role (student/teacher)"),
    db: Session = Depends(get_db),
    current_admin = Depends(require_role([UserRole.ADMIN])),
):
    """List platform users filtered by role."""
    service = AdminService(db)
    return service.list_users(role)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(require_role([UserRole.ADMIN])),
):
    """Delete a user (students/teachers only)."""
    service = AdminService(db)
    service.delete_user(user_id)
    return None


@router.put("/users/{user_id}/balance", response_model=UserResponse)
async def update_user_balance(
    user_id: int,
    payload: UserBalanceUpdate,
    db: Session = Depends(get_db),
    current_admin = Depends(require_role([UserRole.ADMIN])),
):
    """Update user balance."""
    service = AdminService(db)
    return service.update_user_balance(user_id, payload.balance)
