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
