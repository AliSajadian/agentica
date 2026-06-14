"""Pytest configuration and shared fixtures for llm-service tests."""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def mock_ollama_fixture():
    """Mock fixture for ollama_client used in chat endpoints."""
    with patch("app.api.v1.chat.ollama_client") as mock:
        mock.chat = AsyncMock(
            return_value=
            "LangGraph is a library for building stateful multi-actor LLM applications."
        )
        mock.model = "llama3.2:3b"
        yield mock


@pytest.fixture
def mock_ollama_complete_fixture():
    """Mock fixture for ollama_client used in complete endpoint."""
    with patch("app.api.v1.complete.ollama_client") as mock:
        mock.generate = AsyncMock(return_value="FastAPI is a modern Python web framework.")
        mock.model = "llama3.2:3b"
        yield mock
