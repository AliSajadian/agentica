'''Base'''
from typing import Annotated
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, mapped_column
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


# Type annotation for UUID primary key
UuidPk= Annotated[
    uuid.UUID,
    mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
]


async def get_db():
    """FastAPI dependency — yields a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("db_session_error", error=str(e))
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup."""
    async with engine.begin() as conn:
        # from app.db import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    logger.info("db_tables_created")
