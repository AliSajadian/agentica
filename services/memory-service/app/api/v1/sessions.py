'''Session endpoints'''
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.services.memory import memory_service
from app.models.schemas import (
    SessionCreate, SessionResponse,
    SaveMessageRequest, MessageResponse,
    GetHistoryRequest, HistoryResponse
)
from app.utils.logger import get_logger
import uuid

router = APIRouter()
logger = get_logger(__name__)


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation session for a user."""
    try:
        logger.info("create_session_started", user_id=str(request.user_id))
        return await memory_service.create_session(
            db=db,
            user_id=str(request.user_id),
            title=request.title
        )
    except Exception as e:
        logger.error("create_session_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a session by ID."""
    try:
        session = await memory_service.get_session(db=db, session_id=session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_session_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/sessions/user/{user_id}", response_model=list[SessionResponse])
async def get_user_sessions(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all sessions for a specific user."""
    try:
        return await memory_service.get_user_sessions(
            db=db,
            user_id=str(user_id)
        )
    except Exception as e:
        logger.error("get_user_sessions_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sessions/messages", response_model=MessageResponse)
async def save_message(
    request: SaveMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """Save a message to an existing session."""
    try:
        logger.info("save_message_started", session_id=str(request.session_id))
        return await memory_service.save_message(
            db=db,
            session_id=request.session_id,
            role=request.role,
            content=request.content,
            token_count=request.token_count
        )
    except Exception as e:
        logger.error("save_message_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/sessions/history", response_model=HistoryResponse)
async def get_history(
    request: GetHistoryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve conversation history for a session."""
    try:
        return await memory_service.get_history(
            db=db,
            session_id=request.session_id,
            limit=request.limit
        )
    except Exception as e:
        logger.error("get_history_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a session and all its messages."""
    try:
        await memory_service.delete_session(db=db, session_id=session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error("delete_session_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/sessions/{session_id}/history")
async def clear_history(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Clear all messages in a session without deleting the session."""
    try:
        await memory_service.clear_history(db=db, session_id=session_id)
        return {"message": "History cleared successfully"}
    except Exception as e:
        logger.error("clear_history_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
