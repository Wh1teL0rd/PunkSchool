"""
Music Course Platform - FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import db
from app.routers import auth_router, courses_router, students_router, analytics_router, admin_router


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Music Course Platform API - Learn guitar, drums, vocals, keyboards and music theory.
    
    ## Features
    
    * **Authentication** - Register, login, JWT tokens
    * **Courses** - Browse, search, filter courses with various sorting strategies
    * **Learning** - Enroll in courses, complete lessons, take quizzes
    * **Certificates** - Generate completion certificates
    * **Analytics** - Track progress and revenue statistics
    
    ## Design Patterns Used
    
    * **Singleton** - Database connection management
    * **Factory Method** - User creation (Student/Teacher/Admin)
    * **Strategy** - Course sorting (by price, rating, popularity, etc.)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(courses_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    # Import all models to ensure they are registered
    from app.models import (
        User, Course, Module, Lesson, Enrollment,
        Quiz, QuizQuestion, QuizAttempt, Certificate, Transaction
    )
    
    # Create all tables
    db.create_tables()
    print(f"🎵 {settings.APP_NAME} started successfully!")
    print(f"📚 Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print(f"👋 {settings.APP_NAME} shutting down...")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["Root"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Run with: uvicorn app.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
