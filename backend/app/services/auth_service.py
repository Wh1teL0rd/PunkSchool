"""
Authentication service - handles user registration and authentication.
"""
from datetime import timedelta
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserRegisterDTO, Token
from app.services.user_factory import get_user_factory
from app.core.security import create_access_token, verify_password
from app.core.config import settings


class AuthService:
    """
    Service for authentication-related operations.
    Uses UserFactory for user creation (Factory Method pattern).
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_user(self, data: UserRegisterDTO, role: str = "student") -> User:
        """
        Register a new user using the Factory Method pattern.
        
        Args:
            data: User registration data
            role: User role (student, teacher, admin)
        
        Returns:
            Created User instance
        
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Use Factory to create user
        factory = get_user_factory(role)
        return factory.create_user(data, self.db)
    
    def authenticate_user(self, email: str, password: str) -> Token:
        """
        Authenticate user and return JWT token.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Token object with access_token
        
        Raises:
            HTTPException: If credentials are invalid
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user or not user.verify_password(password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},  # PyJWT requires sub to be a string
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user: User, full_name: Optional[str] = None, bio: Optional[str] = None) -> User:
        """Update user profile."""
        if full_name is not None:
            user.full_name = full_name
        if bio is not None:
            user.bio = bio
        
        self.db.commit()
        self.db.refresh(user)
        return user

