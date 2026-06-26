'''Configuration'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, computed_field
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
    POSTGRES_HOST: str = "postgres-gateway"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "admin"
    POSTGRES_DB: str = "agentica_gateway"

    # Redis
    # REDIS_HOST: str = "redis-gateway"
    REDIS_HOST: str = "redis-gateway-svc.agentica-app.svc.cluster.local"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Upstream Services
    RAG_SERVICE_URL: str = "http://rag-service:8001"
    LLM_SERVICE_URL: str = "http://llm-service:8002"
    MEMORY_SERVICE_URL: str = "http://memory-service:8003"
    AGENT_SERVICE_URL: str = "http://agent-service:8004"

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
print(f'[CONFIG] POSTGRES_HOST={settings.POSTGRES_HOST}', flush=True)
print(f'[CONFIG] DATABASE_URL={settings.DATABASE_URL}', flush=True)

print(f'[CONFIG] REDIS_HOST={settings.REDIS_HOST}', flush=True)
