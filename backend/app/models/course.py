"""
Course and related models for database.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, Text, Enum as SQLEnum, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import CourseCategory, DifficultyLevel


class Course(Base):
    """
    Course entity representing a music course.
    """
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, default=0.0, nullable=False)
    category = Column(SQLEnum(CourseCategory), nullable=False)
    level = Column(SQLEnum(DifficultyLevel), default=DifficultyLevel.BEGINNER, nullable=False)
    rating = Column(Float, default=0.0)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    teacher = relationship("User", back_populates="courses_teaching")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan", order_by="Module.order")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="course", lazy="dynamic")
    
    def update_rating(self, new_rating: float) -> None:
        """Update course rating."""
        self.rating = new_rating
    
    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}')>"


class Module(Base):
    """
    Module entity - a section of a course.
    """
    __tablename__ = "modules"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan", order_by="Lesson.order")
    
    def __repr__(self):
        return f"<Module(id={self.id}, title='{self.title}')>"


class Lesson(Base):
    """
    Lesson entity - individual lesson within a module.
    """
    __tablename__ = "lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(255), nullable=False)
    video_url = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)
    duration_minutes = Column(Integer, default=0)
    order = Column(Integer, default=0, nullable=False)
    
    # Relationships
    module = relationship("Module", back_populates="lessons")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title='{self.title}')>"


class Enrollment(Base):
    """
    Enrollment entity - student enrollment in a course (Many-to-Many).
    """
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    progress_percent = Column(Float, default=0.0)
    is_completed = Column(Boolean, default=False)
    completed_lessons = Column(JSON, default=list)  # List of completed lesson IDs
    
    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    certificate = relationship("Certificate", back_populates="enrollment", uselist=False)
    
    def update_progress(self, completed_lessons: int, total_lessons: int) -> None:
        """Update enrollment progress based on completed lessons."""
        if total_lessons > 0:
            self.progress_percent = (completed_lessons / total_lessons) * 100
        if self.progress_percent >= 100:
            self.is_completed = True
    
    def __repr__(self):
        return f"<Enrollment(student_id={self.student_id}, course_id={self.course_id})>"


class Quiz(Base):
    """
    Quiz entity - test for a lesson.
    """
    __tablename__ = "quizzes"
    
    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    title = Column(String(255), nullable=False)
    passing_score = Column(Integer, default=70)  # Percentage
    
    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", lazy="dynamic")
    
    def __repr__(self):
        return f"<Quiz(id={self.id}, title='{self.title}')>"


class QuizQuestion(Base):
    """
    QuizQuestion entity - individual question in a quiz.
    """
    __tablename__ = "quiz_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)  # List of answer options
    correct_option_index = Column(Integer, nullable=False)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    
    def __repr__(self):
        return f"<QuizQuestion(id={self.id})>"


class QuizAttempt(Base):
    """
    QuizAttempt entity - student's quiz attempt result.
    """
    __tablename__ = "quiz_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    answers = Column(JSON, nullable=True)  # Student's answers
    
    # Relationships
    student = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")
    
    def __repr__(self):
        return f"<QuizAttempt(student_id={self.student_id}, quiz_id={self.quiz_id}, score={self.score})>"


class Certificate(Base):
    """
    Certificate entity - course completion certificate.
    """
    __tablename__ = "certificates"
    
    id = Column(String(36), primary_key=True)  # UUID
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False, unique=True)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    pdf_url = Column(String(500), nullable=True)
    
    # Relationships
    enrollment = relationship("Enrollment", back_populates="certificate")
    
    def __repr__(self):
        return f"<Certificate(id='{self.id}')>"


class Transaction(Base):
    """
    Transaction entity - financial transaction for course purchase.
    """
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    course = relationship("Course", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount})>"
