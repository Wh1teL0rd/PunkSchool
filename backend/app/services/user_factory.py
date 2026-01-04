"""
Factory Method pattern for user creation.
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserRegisterDTO
from app.core.security import get_password_hash


class UserFactory(ABC):
    """
    Abstract base class for creating users.
    Implements the Factory Method pattern.
    """
    
    @abstractmethod
    def create_user(self, data: UserRegisterDTO, db: Session) -> User:
        """
        Create a new user with the appropriate role.
        
        Args:
            data: User registration data
            db: Database session
        
        Returns:
            Created User instance
        """
        pass
    
    def _build_user(self, data: UserRegisterDTO, role: UserRole) -> User:
        """
        Build a user object with common fields.
        
        Args:
            data: User registration data
            role: User role
        
        Returns:
            User instance (not persisted)
        """
        return User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            full_name=data.full_name,
            role=role,
            bio=data.bio
        )


class StudentFactory(UserFactory):
    """Factory for creating Student users."""
    
    def create_user(self, data: UserRegisterDTO, db: Session) -> User:
        """Create a student user."""
        user = self._build_user(data, UserRole.STUDENT)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class TeacherFactory(UserFactory):
    """Factory for creating Teacher users."""
    
    def create_user(self, data: UserRegisterDTO, db: Session) -> User:
        """Create a teacher user."""
        user = self._build_user(data, UserRole.TEACHER)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


class AdminFactory(UserFactory):
    """Factory for creating Admin users."""
    
    def create_user(self, data: UserRegisterDTO, db: Session) -> User:
        """Create an admin user."""
        user = self._build_user(data, UserRole.ADMIN)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def get_user_factory(role: str) -> UserFactory:
    """
    Get the appropriate factory based on role string.
    
    Args:
        role: Role string (student, teacher, admin)
    
    Returns:
        Appropriate UserFactory instance
    
    Raises:
        ValueError: If role is invalid
    """
    factories = {
        "student": StudentFactory(),
        "teacher": TeacherFactory(),
        "admin": AdminFactory(),
    }
    
    factory = factories.get(role.lower())
    if factory is None:
        raise ValueError(f"Invalid role: {role}. Must be one of: {list(factories.keys())}")
    
    return factory
