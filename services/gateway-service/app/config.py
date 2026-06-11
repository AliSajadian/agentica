'''Configuration'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "gateway-service"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "agentica"
    POSTGRES_PASSWORD: str = "agentica"
    POSTGRES_DB: str = "agentica_gateway"
    DATABASE_URL: str = "postgresql+asyncpg://agentica:agentica@localhost:5432/agentica_gateway"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Upstream Services
    RAG_SERVICE_URL: str = "http://localhost:8001"
    LLM_SERVICE_URL: str = "http://localhost:8002"
    MEMORY_SERVICE_URL: str = "http://localhost:8003"
    AGENT_SERVICE_URL: str = "http://localhost:8004"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()