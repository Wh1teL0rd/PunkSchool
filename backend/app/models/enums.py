"""
Enumerations for the application.
"""
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration."""
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class CourseCategory(str, Enum):
    """Course category enumeration."""
    GUITAR = "guitar"
    DRUMS = "drums"
    VOCALS = "vocals"
    KEYBOARDS = "keyboards"
    THEORY = "theory"


class DifficultyLevel(str, Enum):
    """Course difficulty level enumeration."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    MASTER = "master"


class LessonType(str, Enum):
    """Lesson type enumeration."""
    VIDEO = "video"
    TEXT = "text"
    QUIZ = "quiz"

