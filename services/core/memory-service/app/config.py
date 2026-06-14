'''Config'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "memory-service"
    APP_ENV: str = "development"
    APP_PORT: int = 8003
    DEBUG: bool = True

    # PostgreSQL
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "agentica"
    POSTGRES_PASSWORD: str = "agentica"
    POSTGRES_DB: str = "agentica_memory"
    DATABASE_URL: str = "postgresql+asyncpg://agentica:agentica@postgres:5432/agentica_memory"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600

    # Memory
    MAX_HISTORY_MESSAGES: int = 20
    SESSION_TTL_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
