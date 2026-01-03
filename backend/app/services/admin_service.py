"""Administrative service layer for managing users and platform data."""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.enums import UserRole


class AdminService:
    """Service with admin-only operations."""

    def __init__(self, db: Session):
        self.db = db

    def list_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Return users filtered by role (students/teachers/all)."""
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        users = query.order_by(User.created_at.desc()).all()
        
        # Convert SQLAlchemy objects to dict with computed stats
        result = []
        for user in users:
            user_data = {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "bio": user.bio,
                "balance": user.balance,
                "rating": user.rating,
                "rating_count": user.rating_count,
            }
            
            if user.role == UserRole.TEACHER:
                courses = user.courses_teaching.all()
                courses_count = len(courses)
                students_count = sum(len(course.enrollments) for course in courses)
                user_data["courses_count"] = courses_count
                user_data["students_count"] = students_count
            result.append(user_data)
        
        return result

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (students/teachers only)."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete another admin user"
            )

        self.db.delete(user)
        self.db.commit()
        return True

    def update_user_balance(self, user_id: int, new_balance: float) -> User:
        """Update user's balance (admin operation)."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if new_balance < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Balance must be non-negative"
            )
        user.balance = new_balance
        self.db.commit()
        self.db.refresh(user)
        return user
