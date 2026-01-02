"""
User model for database.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.security import verify_password as verify_pwd
from app.models.enums import UserRole


class User(Base):
    """
    User entity representing students, teachers, and admins.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    bio = Column(Text, nullable=True)  # For teachers
    balance = Column(Float, default=1000.0, nullable=False)  # User balance for purchasing courses
    
    # Relationships
    courses_teaching = relationship("Course", back_populates="teacher", lazy="dynamic")
    enrollments = relationship("Enrollment", back_populates="student", lazy="dynamic")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", lazy="dynamic")
    transactions = relationship("Transaction", back_populates="user", lazy="dynamic")
    
    def verify_password(self, password: str) -> bool:
        """Verify the user's password."""
        return verify_pwd(password, self.password_hash)
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"
