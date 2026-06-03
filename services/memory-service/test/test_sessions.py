"""Tests for session and message history endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime
from app.main import app
from app.models.schemas import (
    SessionResponse,
    MessageResponse,
    HistoryResponse,
    MessageRole
)


def make_session_response(user_id=None, session_id=None):
    """Helper to create a mock SessionResponse."""
    return SessionResponse(
        id=session_id or uuid4(),
        user_id=user_id or uuid4(),
        title="Test Session",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def make_message_response(session_id=None, role=MessageRole.user):
    """Helper to create a mock MessageResponse."""
    return MessageResponse(
        id=uuid4(),
        session_id=session_id or uuid4(),
        role=role,
        content="Test message content",
        token_count=10,
        created_at=datetime.now()
    )


# ── /sessions ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_session(mock_memory_fixture, mock_db_fixture):
    """
    Test session creation with valid user_id.
    Verifies response structure and memory service was called correctly.
    """
    user_id = uuid4()
    session_response = make_session_response(user_id=user_id)
    mock_memory_fixture.create_session = AsyncMock(return_value=session_response)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/sessions", json={
            "user_id": str(user_id),
            "title": "Test Session"
        })

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    mock_memory_fixture.create_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session(mock_memory_fixture, mock_db_fixture):
    """
    Test retrieving an existing session by ID.
    Verifies correct session data is returned.
    """
    session_id = uuid4()
    session_response = make_session_response(session_id=session_id)
    mock_memory_fixture.get_session = AsyncMock(return_value=session_response)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(session_id)
    mock_memory_fixture.get_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_session_not_found(mock_memory_fixture, mock_db_fixture):
    """
    Test retrieving a non-existent session returns 404.
    Verifies proper error handling for missing sessions.
    """
    mock_memory_fixture.get_session = AsyncMock(return_value=None)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/sessions/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_user_sessions(mock_memory_fixture, mock_db_fixture):
    """
    Test retrieving all sessions for a user.
    Verifies list of sessions is returned correctly.
    """
    user_id = uuid4()
    sessions = [make_session_response(user_id=user_id) for _ in range(3)]
    mock_memory_fixture.get_user_sessions = AsyncMock(return_value=sessions)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/sessions/user/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    mock_memory_fixture.get_user_sessions.assert_awaited_once()


# ── /sessions/messages ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_message(mock_memory_fixture, mock_db_fixture):
    """
    Test saving a user message to a session.
    Verifies message is stored with correct role and content.
    """
    session_id = uuid4()
    message_response = make_message_response(session_id=session_id, role=MessageRole.user)
    mock_memory_fixture.save_message = AsyncMock(return_value=message_response)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/sessions/messages", json={
            "session_id": str(session_id),
            "role": "user",
            "content": "What is the weather in Paris?",
            "token_count": 8
        })

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "user"
    assert "id" in data
    mock_memory_fixture.save_message.assert_awaited_once()
    call_kwargs = mock_memory_fixture.save_message.call_args.kwargs
    assert call_kwargs["role"] == "user"
    assert call_kwargs["content"] == "What is the weather in Paris?"


@pytest.mark.asyncio
async def test_save_assistant_message(mock_memory_fixture, mock_db_fixture):
    """
    Test saving an assistant message to a session.
    Verifies assistant role is stored correctly.
    """
    session_id = uuid4()
    message_response = make_message_response(
        session_id=session_id,
        role=MessageRole.assistant
    )
    mock_memory_fixture.save_message = AsyncMock(return_value=message_response)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/sessions/messages", json={
            "session_id": str(session_id),
            "role": "assistant",
            "content": "The weather in Paris is 18°C and sunny.",
            "token_count": 12
        })

    assert response.status_code == 200
    mock_memory_fixture.save_message.assert_awaited_once()
    call_kwargs = mock_memory_fixture.save_message.call_args.kwargs
    assert call_kwargs["role"] == "assistant"


# ── /sessions/history ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_history(mock_memory_fixture, mock_db_fixture):
    """
    Test retrieving conversation history for a session.
    Verifies history contains correct number of messages.
    """
    session_id = uuid4()
    messages = [
        make_message_response(session_id=session_id, role=MessageRole.user),
        make_message_response(session_id=session_id, role=MessageRole.assistant),
    ]
    history = HistoryResponse(
        session_id=session_id,
        messages=messages,
        total=2
    )
    mock_memory_fixture.get_history = AsyncMock(return_value=history)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/sessions/history", json={
            "session_id": str(session_id),
            "limit": 20
        })

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["messages"]) == 2
    mock_memory_fixture.get_history.assert_awaited_once()
    call_kwargs = mock_memory_fixture.get_history.call_args.kwargs
    assert call_kwargs["limit"] == 20


# ── DELETE endpoints ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_session(mock_memory_fixture, mock_db_fixture):
    """
    Test deleting a session and all its messages.
    Verifies delete was called and success message returned.
    """
    session_id = uuid4()
    mock_memory_fixture.delete_session = AsyncMock(return_value=True)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/sessions/{session_id}")

    assert response.status_code == 200
    assert "deleted" in response.json()["message"]
    mock_memory_fixture.delete_session.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_history(mock_memory_fixture, mock_db_fixture):
    """
    Test clearing all messages in a session without deleting the session.
    Verifies clear was called and success message returned.
    """
    session_id = uuid4()
    mock_memory_fixture.clear_history = AsyncMock(return_value=True)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.delete(f"/api/v1/sessions/{session_id}/history")

    assert response.status_code == 200
    assert "cleared" in response.json()["message"]
    mock_memory_fixture.clear_history.assert_awaited_once()


# ── /health ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health():
    """
    Test health endpoint when all dependencies are reachable.
    Verifies redis status is reported correctly.
    """
    with patch("app.main.redis_cache.health", AsyncMock(return_value=True)):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["redis"] == "connected"


@pytest.mark.asyncio
async def test_health_redis_unreachable():
    """
    Test health endpoint when Redis is not reachable.
    Verifies service still returns 200 but reports redis as unreachable.
    """
    with patch("app.main.redis_cache.health", AsyncMock(return_value=False)):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["redis"] == "unreachable"
