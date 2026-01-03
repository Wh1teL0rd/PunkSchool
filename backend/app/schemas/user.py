"""
Pydantic schemas (DTOs) for User.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)


# Request schemas
class UserRegisterDTO(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6, max_length=100)
    bio: Optional[str] = None


class UserLoginDTO(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdateDTO(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    bio: Optional[str] = None

class UserBalanceUpdate(BaseModel):
    """Schema for admin balance updates."""
    balance: float = Field(..., ge=0)


# Response schemas
class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    role: UserRole
    created_at: datetime
    bio: Optional[str] = None
    balance: float = 1000.0
    rating: float = 0.0
    rating_count: int = 0
    
    class Config:
        from_attributes = True


class UserBriefResponse(BaseModel):
    """Brief user info for nested responses."""
    id: int
    full_name: str
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Token schemas
class Token(BaseModel):
    """JWT Token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[int] = None
