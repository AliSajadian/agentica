'''Menory service'''
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models import Session, Message
from app.core.cache import redis_cache
from app.models.schemas import (
    SessionResponse,
    MessageResponse,
    HistoryResponse
)
from app.config import settings
from app.utils.logger import get_logger
import uuid
# import json

logger = get_logger(__name__)

CACHE_PREFIX = "session:"


class MemoryService:
    """Service for managing conversation sessions and message history."""

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        title: str = None
    ) -> SessionResponse:
        """Create a new conversation session for a user."""
        session = Session(user_id=user_id, title=title)
        db.add(session)
        await db.flush()
        await db.refresh(session)
        logger.info("session_created", session_id=str(session.id), user_id=user_id)
        return SessionResponse.model_validate(session)

    async def get_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> SessionResponse | None:
        """Retrieve a session by ID."""
        result = await db.execute(
            select(Session).where(Session.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            return None
        return SessionResponse.model_validate(session)

    async def get_user_sessions(
        self,
        db: AsyncSession,
        user_id: str
    ) -> list[SessionResponse]:
        """Retrieve all sessions for a user."""
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.updated_at.desc())
        )
        sessions = result.scalars().all()
        return [SessionResponse.model_validate(s) for s in sessions]

    async def save_message(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        role: str,
        content: str,
        token_count: int = None
    ) -> MessageResponse:
        """Save a message to a session and invalidate cache."""
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            token_count=token_count
        )
        db.add(message)
        await db.flush()
        await db.refresh(message)

        # invalidate cache so next get_history fetches fresh data
        await redis_cache.delete(f"{CACHE_PREFIX}{session_id}")
        logger.info("message_saved", session_id=str(session_id), role=role)
        return MessageResponse.model_validate(message)

    async def get_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = None
    ) -> HistoryResponse:
        """
        Retrieve conversation history for a session.
        Checks Redis cache first, falls back to PostgreSQL.
        """
        cache_key = f"{CACHE_PREFIX}{session_id}"
        limit = limit or settings.MAX_HISTORY_MESSAGES

        # check cache first
        cached = await redis_cache.get(cache_key)
        if cached:
            messages = cached.get("messages", [])[-limit:]
            return HistoryResponse(
                session_id=session_id,
                messages=[MessageResponse(**m) for m in messages],
                total=len(messages)
            )

        # fetch from PostgreSQL
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))

        # cache the result
        messages_data = [MessageResponse.model_validate(m).model_dump(mode="json")
                         for m in messages]
        await redis_cache.set(cache_key, {"messages": messages_data})

        logger.info("history_fetched", session_id=str(session_id), count=len(messages))
        return HistoryResponse(
            session_id=session_id,
            messages=[MessageResponse.model_validate(m) for m in messages],
            total=len(messages)
        )

    async def delete_session(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Delete a session and all its messages."""
        await db.execute(
            delete(Session).where(Session.id == session_id)
        )
        await redis_cache.delete(f"{CACHE_PREFIX}{session_id}")
        logger.info("session_deleted", session_id=str(session_id))
        return True

    async def clear_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID
    ) -> bool:
        """Clear all messages in a session without deleting the session."""
        await db.execute(
            delete(Message).where(Message.session_id == session_id)
        )
        await redis_cache.delete(f"{CACHE_PREFIX}{session_id}")
        logger.info("history_cleared", session_id=str(session_id))
        return True


memory_service = MemoryService()
