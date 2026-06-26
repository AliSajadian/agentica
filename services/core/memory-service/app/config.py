'''Config'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, computed_field
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App
    APP_NAME: str = "memory-service"
    APP_ENV: str = "development"
    APP_PORT: int = 8003
    DEBUG: bool = True

    # PostgreSQL
    POSTGRES_HOST: str = "postgres-memory"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_DB: str = "agentica_memory"

    # Redis
    # REDIS_URL: str = "redis://redis-memory:6379/0"
    # REDIS_HOST: str = "redis-memory"
    REDIS_HOST: str = "redis-memory-svc.agentica-app.svc.cluster.local"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_TTL: int = 3600
    REDIS_PASSWORD: str = ""

    # Memory
    MAX_HISTORY_MESSAGES: int = 20
    SESSION_TTL_HOURS: int = 24

    # Logging
    LOG_LEVEL: str = "INFO"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?ssl=disable"
        )

    model_config = ConfigDict(env_file=".env.docker", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
