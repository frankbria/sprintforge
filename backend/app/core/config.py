"""Application configuration management."""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    
    # Application
    app_name: str = "SprintForge API"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost/sprintforge",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Security
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"],
        env="CORS_ORIGINS"
    )
    
    # Trusted hosts (security)
    allowed_hosts: Optional[List[str]] = Field(default=None, env="ALLOWED_HOSTS")
    
    # File storage
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=50_000_000, env="MAX_FILE_SIZE")  # 50MB
    
    # Celery (background tasks)
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")

    # Email/SMTP (notifications)
    smtp_host: str = Field(default="localhost", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@sprintforge.local", env="SMTP_FROM_EMAIL")
    smtp_from_name: str = Field(default="SprintForge", env="SMTP_FROM_NAME")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")

    # External services
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # Monitoring
    log_level: str = Field(default="INFO", env="LOG_LEVEL")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()