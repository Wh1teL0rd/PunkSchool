"""
Database module implementing Singleton pattern for database connection.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.core.config import settings


Base = declarative_base()


class Database:
    """
    Singleton class for database connection management.
    Ensures only one database connection exists throughout the application.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize database engine and session factory."""
        self.engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},  # SQLite specific
            echo=settings.DEBUG
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()
    
    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        # Add lesson_type column if it doesn't exist (migration)
        self._migrate_lesson_type()
        # Add points column to quiz_questions if it doesn't exist (migration)
        self._migrate_quiz_questions_points()
        # Add balance column to users table if it doesn't exist (migration)
        self._migrate_user_balance()
    
    def _migrate_lesson_type(self):
        """Add lesson_type column to lessons table if it doesn't exist."""
        from sqlalchemy import text
        try:
            with self.engine.connect() as conn:
                # Check if column exists
                result = conn.execute(text("PRAGMA table_info(lessons)"))
                columns = [row[1] for row in result]
                
                if 'lesson_type' not in columns:
                    # Add column with default value (using enum values, not names)
                    conn.execute(text("ALTER TABLE lessons ADD COLUMN lesson_type VARCHAR(50) DEFAULT 'text'"))
                    # Update existing rows to use enum values (lowercase)
                    conn.execute(text("UPDATE lessons SET lesson_type = 'text' WHERE lesson_type IS NULL"))
                    conn.commit()
                    print("✅ Migration: Added lesson_type column to lessons table")
                else:
                    # Update existing uppercase values to lowercase (enum values)
                    conn.execute(text("UPDATE lessons SET lesson_type = 'text' WHERE lesson_type = 'TEXT' OR lesson_type = 'text'"))
                    conn.execute(text("UPDATE lessons SET lesson_type = 'video' WHERE lesson_type = 'VIDEO' OR lesson_type = 'video'"))
                    conn.execute(text("UPDATE lessons SET lesson_type = 'quiz' WHERE lesson_type = 'QUIZ' OR lesson_type = 'quiz'"))
                    conn.commit()
                    print("✅ Migration: Updated lesson_type values to enum format")
        except Exception as e:
            print(f"⚠️ Migration warning: {e}")

    def _migrate_quiz_questions_points(self):
        """Add points column to quiz_questions table if it doesn't exist."""
        from sqlalchemy import text
        try:
            with self.engine.connect() as conn:
                # Check if quiz_questions table exists
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='quiz_questions'"))
                if not result.fetchone():
                    print("⚠️ Migration: quiz_questions table doesn't exist yet, skipping points migration")
                    return
                
                # Check if column exists
                result = conn.execute(text("PRAGMA table_info(quiz_questions)"))
                columns = [row[1] for row in result]
                
                if 'points' not in columns:
                    # Add column with default value
                    conn.execute(text("ALTER TABLE quiz_questions ADD COLUMN points INTEGER DEFAULT 1"))
                    # Update existing rows
                    conn.execute(text("UPDATE quiz_questions SET points = 1 WHERE points IS NULL"))
                    conn.commit()
                    print("✅ Migration: Added points column to quiz_questions table")
                else:
                    print("✅ Migration: points column already exists in quiz_questions table")
        except Exception as e:
            print(f"⚠️ Migration warning (quiz_questions.points): {e}")

    def _migrate_user_balance(self):
        """Add balance column to users table if it doesn't exist."""
        from sqlalchemy import text
        try:
            with self.engine.connect() as conn:
                # Check if users table exists
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
                if not result.fetchone():
                    print("⚠️ Migration: users table doesn't exist yet, skipping balance migration")
                    return
                
                # Check if column exists
                result = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result]
                
                if 'balance' not in columns:
                    # Add column with default value
                    conn.execute(text("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 1000.0"))
                    # Update existing rows
                    conn.execute(text("UPDATE users SET balance = 1000.0 WHERE balance IS NULL"))
                    conn.commit()
                    print("✅ Migration: Added balance column to users table")
                else:
                    print("✅ Migration: balance column already exists in users table")
        except Exception as e:
            print(f"⚠️ Migration warning (users.balance): {e}")


# Global database instance
db = Database()


def get_db():
    """
    Dependency for FastAPI to get database session.
    Yields session and ensures proper cleanup.
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
