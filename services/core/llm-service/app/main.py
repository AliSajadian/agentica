'''Main'''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.utils.logger import setup_logging, get_logger
from app.api.v1 import chat, complete
from app.core.ollama import ollama_client

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    ''''Life span'''
    # startup
    setup_logging()

    logger.info(f"Starting {fastapi_app.title}...")
    logger.info("llm_service_starting", env=settings.APP_ENV)

    # check ollama is running
    healthy = await ollama_client.health()
    if not healthy:
        logger.warning(
            "ollama_not_reachable", 
            url=f"http://{settings.OLLAMA_HOST}:{settings.OLLAMA_PORT}"
        )
    else:
        models = await ollama_client.list_models()
        logger.info("ollama_connected", available_models=models)

    yield
    logger.info("llm_service_stopping")


app = FastAPI(
    title="Agentica LLM Service",
    description="LLM inference and RAG answer generation service",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://agentica.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router,     prefix="/api/v1", tags=["chat"])
app.include_router(complete.router, prefix="/api/v1", tags=["complete"])


@app.get("/health", tags=["health"])
async def health():
    '''Health'''
    ollama_ok = await ollama_client.health()
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.APP_ENV,
        "ollama": "connected" if ollama_ok else "unreachable",
        "model": settings.OLLAMA_MODEL,
    }
