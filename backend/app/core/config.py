from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration settings."""
    
    APP_NAME: str = "Music Course Platform"
    DEBUG: bool = True
    CERTIFICATES_DIR: str = "generated/certificates"
    
    # Database
    DATABASE_URL: str = "sqlite:///./music_courses.db"
    
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Default admin credentials
    DEFAULT_ADMIN_EMAIL: str = "admin@punkschool.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin"
    DEFAULT_ADMIN_NAME: str = "Platform Admin"
    DEFAULT_ADMIN_LOGIN: str = "admin"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
