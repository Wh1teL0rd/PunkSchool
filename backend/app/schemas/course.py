"""
Pydantic schemas (DTOs) for Course and related entities.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, conint

from app.models.enums import CourseCategory, DifficultyLevel, LessonType
from app.schemas.user import UserBriefResponse


# ============== Module Schemas ==============

class ModuleBase(BaseModel):
    """Base module schema."""
    title: str = Field(..., min_length=1, max_length=255)
    order: int = 0


class ModuleCreateDTO(ModuleBase):
    """Schema for creating a module."""
    pass


class ModuleResponse(ModuleBase):
    """Schema for module response."""
    id: int
    course_id: int
    lessons: List["LessonBriefResponse"] = []
    
    class Config:
        from_attributes = True


class CourseReviewResponse(BaseModel):
    """Schema representing student's course review."""
    rating: int
    comment: Optional[str] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TeacherReviewResponse(BaseModel):
    """Schema representing student's teacher review."""
    rating: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CourseRatingRequest(BaseModel):
    """Request payload for submitting a course rating."""
    rating: conint(ge=1, le=5)
    comment: Optional[str] = None


class CourseRatingResponse(BaseModel):
    """Response payload for a course rating submission."""
    course_id: int
    rating: float
    rating_count: int
    student_rating: int


class TeacherRatingRequest(BaseModel):
    """Request payload for submitting a teacher rating."""
    rating: conint(ge=1, le=5)


class TeacherRatingResponse(BaseModel):
    """Response payload for a teacher rating submission."""
    teacher_id: int
    rating: float
    rating_count: int
    student_rating: int


# ============== Lesson Schemas ==============

class LessonBase(BaseModel):
    """Base lesson schema."""
    title: str = Field(..., min_length=1, max_length=255)
    lesson_type: Optional["LessonType"] = None
    video_url: Optional[str] = None
    content_text: Optional[str] = None
    duration_minutes: int = 0
    order: int = 0


class LessonCreateDTO(LessonBase):
    """Schema for creating a lesson."""
    pass


class LessonResponse(LessonBase):
    """Schema for lesson response."""
    id: int
    module_id: int
    has_quiz: bool = False
    quiz: Optional["QuizResponse"] = None
    
    class Config:
        from_attributes = True


class LessonBriefResponse(BaseModel):
    """Brief lesson info."""
    id: int
    title: str
    lesson_type: Optional["LessonType"] = None
    duration_minutes: int
    order: int
    
    class Config:
        from_attributes = True


# ============== Quiz Schemas ==============

class QuizQuestionBase(BaseModel):
    """Base quiz question schema."""
    question_text: str
    options: List[str]
    correct_option_index: int
    points: int = Field(default=1, ge=1, description="Points for correct answer")


class QuizQuestionCreateDTO(QuizQuestionBase):
    """Schema for creating quiz question."""
    pass


class QuizQuestionResponse(BaseModel):
    """Schema for quiz question response (without correct answer for students)."""
    id: int
    question_text: str
    options: List[str]
    
    class Config:
        from_attributes = True


class QuizQuestionTeacherResponse(BaseModel):
    """Schema for quiz question response for teachers (includes correct answer and points)."""
    id: int
    question_text: str
    options: List[str]
    correct_option_index: int
    points: int
    
    class Config:
        from_attributes = True


class QuizBase(BaseModel):
    """Base quiz schema."""
    title: str = Field(..., min_length=1, max_length=255)
    passing_score: int = 70


class QuizCreateDTO(QuizBase):
    """Schema for creating a quiz."""
    questions: List[QuizQuestionCreateDTO] = []


class QuizResponse(QuizBase):
    """Schema for quiz response."""
    id: int
    lesson_id: int
    questions: List[QuizQuestionResponse] = []
    
    class Config:
        from_attributes = True


class QuizTeacherResponse(QuizBase):
    """Schema for quiz response for teachers (includes correct answers and points)."""
    id: int
    lesson_id: int
    questions: List[QuizQuestionTeacherResponse] = []
    
    class Config:
        from_attributes = True


class QuizSubmitDTO(BaseModel):
    """Schema for submitting quiz answers."""
    answers: dict  # {question_id: selected_option_index}


class QuizAttemptResponse(BaseModel):
    """Schema for quiz attempt response."""
    id: int
    quiz_id: int
    score: int  # Score in points
    total_score: int  # Total possible score in points
    passed: bool
    attempted_at: datetime
    
    class Config:
        from_attributes = True


# ============== Course Schemas ==============

class CourseBase(BaseModel):
    """Base course schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(default=0.0, ge=0)
    category: CourseCategory
    level: DifficultyLevel = DifficultyLevel.BEGINNER


class CourseCreateDTO(CourseBase):
    """Schema for creating a course."""
    teacher_id: Optional[int] = None


class CourseUpdateDTO(BaseModel):
    """Schema for updating a course."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[CourseCategory] = None
    level: Optional[DifficultyLevel] = None
    teacher_id: Optional[int] = None


class CourseResponse(CourseBase):
    """Schema for course response."""
    id: int
    teacher_id: int
    rating: float
    rating_count: int = 0
    is_published: bool
    created_at: datetime
    teacher: Optional[UserBriefResponse] = None
    
    class Config:
        from_attributes = True


class CourseDetailResponse(CourseResponse):
    """Schema for detailed course response with modules."""
    modules: List[ModuleResponse] = []
    total_lessons: int = 0
    total_duration: int = 0
    
    class Config:
        from_attributes = True


class CourseBriefResponse(BaseModel):
    """Brief course info for lists."""
    id: int
    title: str
    price: float
    rating: float
    rating_count: int = 0
    category: CourseCategory
    level: DifficultyLevel
    teacher: Optional[UserBriefResponse] = None
    
    class Config:
        from_attributes = True


# ============== Enrollment Schemas ==============

class EnrollmentBase(BaseModel):
    """Base enrollment schema."""
    course_id: int


class EnrollmentCreateDTO(EnrollmentBase):
    """Schema for creating enrollment."""
    pass


class EnrollmentResponse(BaseModel):
    """Schema for enrollment response."""
    id: int
    student_id: int
    course_id: int
    enrolled_at: datetime
    progress_percent: float
    is_completed: bool
    completed_lessons: List[int] = Field(default_factory=list)
    course: Optional[CourseBriefResponse] = None
    certificate: Optional["CertificateResponse"] = None
    course_review: Optional["CourseReviewResponse"] = None
    teacher_review: Optional["TeacherReviewResponse"] = None
    
    class Config:
        from_attributes = True


class EnrollmentProgressDTO(BaseModel):
    """Schema for updating enrollment progress."""
    lesson_id: int


# ============== Certificate Schemas ==============

class CertificateResponse(BaseModel):
    """Schema for certificate response."""
    id: str
    enrollment_id: int
    issued_at: datetime
    pdf_url: Optional[str] = None
    download_url: Optional[str] = None
    student_name: Optional[str] = None
    course_title: Optional[str] = None
    total_hours: Optional[float] = None
    
    class Config:
        from_attributes = True


# ============== Transaction Schemas ==============

class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    user_id: int
    course_id: int
    amount: float
    date: datetime
    
    class Config:
        from_attributes = True


# Update forward references
ModuleResponse.model_rebuild()
EnrollmentResponse.model_rebuild()
CertificateResponse.model_rebuild()
