'''Config'''
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    '''Setting'''
    # App
    APP_NAME: str = "llm-service"
    APP_ENV: str = "development"
    APP_PORT: int = 8002
    DEBUG: bool = True

    # Ollama
    OLLAMA_HOST: str = "ollama"
    OLLAMA_PORT: int = 11434
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT: int = 120

    # Generation
    MAX_TOKENS: int = 1024
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    STREAM: bool = True

    # RAG Service
    RAG_SERVICE_URL: str = "http://rag-service:8001"

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env.docker", case_sensitive=True)


@lru_cache()
def get_settings() -> Settings:
    '''Get config'''
    return Settings()


settings = get_settings()
