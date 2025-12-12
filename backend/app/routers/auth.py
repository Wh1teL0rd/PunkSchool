"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserRegisterDTO,
    UserResponse,
    UserUpdateDTO,
    Token,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegisterDTO,
    role: str = "student",
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **role**: User role (student, teacher)
    """
    if role not in ["student", "teacher"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'student' or 'teacher'"
        )
    
    service = AuthService(db)
    user = service.register_user(data, role)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get JWT token.
    
    - **username**: User email
    - **password**: User password
    """
    service = AuthService(db)
    token = service.authenticate_user(form_data.username, form_data.password)
    return token


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user's information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    data: UserUpdateDTO,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    service = AuthService(db)
    updated_user = service.update_user(
        current_user,
        full_name=data.full_name,
        bio=data.bio
    )
    return updated_user
