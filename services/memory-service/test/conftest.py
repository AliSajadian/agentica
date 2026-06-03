"""Pytest configuration and shared fixtures for memory-service tests."""
import pytest
# from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from uuid import uuid4
# from app.main import app


@pytest.fixture
def sample_user_id():
    """Generate a sample user UUID for tests."""
    return uuid4()


@pytest.fixture
def sample_session_id():
    """Generate a sample session UUID for tests."""
    return uuid4()


@pytest.fixture
def mock_db_fixture():
    """Mock database session."""
    with patch("app.api.v1.sessions.get_db") as mock:
        db = AsyncMock()
        mock.return_value = db
        yield db


@pytest.fixture
def mock_memory_fixture():
    """Mock memory service."""
    with patch("app.api.v1.sessions.memory_service") as mock:
        yield mock


@pytest.fixture
def mock_cache_fixture():
    """Mock Redis cache."""
    with patch("app.core.cache.redis_cache") as mock:
        mock.health = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        yield mock
