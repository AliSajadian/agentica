'''Configuration'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = ConfigDict(env_file=".env.docker", extra="ignore")

    APP_ENV: str = "development"
    APP_PORT: int = 8004
    LOG_LEVEL: str = "INFO"

    RAG_SERVICE_URL: str = "http://rag-service-svc:8001"
    LLM_SERVICE_URL: str = "http://llm-service-svc:8002"
    MEMORY_SERVICE_URL: str = "http://memory-service-svc:8003"

    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3


settings = Settings()
