'''Configuration'''
from typing import Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    '''Setting'''
    # App
    APP_NAME: str = "rag-service"
    APP_ENV: str = "development"
    APP_PORT: int = 8001
    DEBUG: bool = True

    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "agentica"
    QDRANT__TELEMETRY_DISABLED: Optional[bool] = True

    # Embedding
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DEVICE: str = "cpu"

    # Chunking
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # RabbitMQ
    # RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Logging
    LOG_LEVEL: str = "INFO"

    LLM_SERVICE_URL: str = "http://llm-service:8002"

    model_config = ConfigDict(env_file=".env.docker", case_sensitive=True, env_nested_delimiter = "__"
)

    # class Config:
    #     '''Config'''
    #     env_file = ".env"
    #     case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    '''Get setting'''
    return Settings()


settings = get_settings()
