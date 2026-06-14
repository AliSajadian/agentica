'''Test chat'''
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


# ── /complete endpoint ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete(mock_ollama_complete_fixture):
    """
    Test complete endpoint with a valid prompt.
    Verifies response structure and that ollama generate was called with correct prompt.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/complete", json={
            "prompt": "What is FastAPI?",
            "stream": False
        })

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "model" in data
    assert len(data["answer"]) > 0
    assert data["model"] == "llama3.2:3b"
    assert data["prompt"] == "What is FastAPI?"

    # verify ollama was actually called with correct prompt
    mock_ollama_complete_fixture.generate.assert_awaited_once_with("What is FastAPI?")


@pytest.mark.asyncio
async def test_complete_short_prompt_fails(mock_ollama_complete_fixture):
    """
    Test complete endpoint rejects prompts shorter than min_length.
    Verifies pydantic validation works and ollama is never called for invalid input.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/complete", json={
            "prompt": "Hi",
            "stream": False
        })

    assert response.status_code == 422

    # ollama should never be called for invalid input
    mock_ollama_complete_fixture.generate.assert_not_awaited()


# ── /chat endpoint ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat(mock_ollama_fixture):
    """
    Test chat endpoint with a single user message.
    Verifies response structure and that ollama chat was called with correct message structure.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json={
            "messages": [
                {"role": "user", "content": "What is LangGraph?"}
            ],
            "stream": False
        })

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "model" in data
    assert data["model"] == "llama3.2:3b"
    assert len(data["answer"]) > 0

    # verify chat was called once with correct message structure
    mock_ollama_fixture.chat.assert_awaited_once()
    call_args = mock_ollama_fixture.chat.call_args[0][0]
    assert call_args[0]["role"] == "user"
    assert call_args[0]["content"] == "What is LangGraph?"


@pytest.mark.asyncio
async def test_chat_with_history(mock_ollama_fixture):
    """
    Test chat endpoint with multi-turn conversation history.
    Verifies all messages are passed to ollama in correct order.
    """
    messages = [
        {"role": "user",      "content": "What is LangGraph?"},
        {"role": "assistant", "content": "LangGraph is a library for building stateful LLM apps."},
        {"role": "user",      "content": "Can you give me an example?"}
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat", json={
            "messages": messages,
            "stream": False
        })

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data

    # verify all 3 messages were passed to ollama in correct order
    mock_ollama_fixture.chat.assert_awaited_once()
    call_args = mock_ollama_fixture.chat.call_args[0][0]
    assert len(call_args) == 3
    assert call_args[-1]["content"] == "Can you give me an example?"


# ── /chat/rag endpoint ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_rag(mock_ollama_fixture):
    """
    Test RAG chat endpoint with question and context chunks.
    Verifies context chunks are embedded in system message sent to ollama.
    """
    context_chunks = [
        {
            "text": "LangGraph is a library for building stateful \
                multi-actor applications with LLMs.",
            "score": 0.92,
            "metadata": {"source": "langgraph_docs.txt"},
            "chunk_index": 0
        },
        {
            "text": "LangGraph extends LangChain with cyclic computation and agent runtimes.",
            "score": 0.87,
            "metadata": {"source": "langgraph_docs.txt"},
            "chunk_index": 1
        }
    ]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat/rag", json={
            "question": "What is LangGraph used for?",
            "context_chunks": context_chunks,
            "stream": False,
            "system_prompt": None
        })

    assert response.status_code == 200
    data = response.json()
    assert data["question"] == "What is LangGraph used for?"
    assert "answer" in data
    assert data["context_used"] == 2
    assert data["model"] == "llama3.2:3b"
    assert len(data["answer"]) > 0

    # verify chat was called once and context was included in system message
    mock_ollama_fixture.chat.assert_awaited_once()
    call_args = mock_ollama_fixture.chat.call_args[0][0]
    system_message = call_args[0]
    assert system_message["role"] == "system"
    assert "LangGraph" in system_message["content"]
    assert "langgraph_docs.txt" in system_message["content"]


@pytest.mark.asyncio
async def test_chat_rag_empty_chunks(mock_ollama_fixture):
    """
    Test RAG chat endpoint with no context chunks.
    Verifies service handles empty context gracefully and still calls ollama.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat/rag", json={
            "question": "What is LangGraph?",
            "context_chunks": [],
            "stream": False
        })

    assert response.status_code == 200
    data = response.json()
    assert data["context_used"] == 0

    # verify ollama was still called even with no context
    mock_ollama_fixture.chat.assert_awaited_once()
    call_args = mock_ollama_fixture.chat.call_args[0][0]
    system_message = call_args[0]
    assert "No context available" in system_message["content"]


@pytest.mark.asyncio
async def test_chat_rag_custom_system_prompt(mock_ollama_fixture):
    """
    Test RAG chat endpoint with a custom system prompt.
    Verifies custom prompt overrides the default system prompt.
    """
    custom_prompt = "You are a specialized AI assistant for LangGraph documentation."

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/chat/rag", json={
            "question": "What is LangGraph?",
            "context_chunks": [
                {
                    "text": "LangGraph is a stateful LLM framework.",
                    "score": 0.95,
                    "metadata": {"source": "docs.txt"},
                    "chunk_index": 0
                }
            ],
            "stream": False,
            "system_prompt": custom_prompt
        })

    assert response.status_code == 200

    # verify custom system prompt was used instead of default
    mock_ollama_fixture.chat.assert_awaited_once()
    call_args = mock_ollama_fixture.chat.call_args[0][0]
    system_message = call_args[0]
    assert custom_prompt in system_message["content"]


# ── /health endpoint ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health():
    """
    Test health endpoint when ollama is reachable.
    Verifies service reports connected status and correct model name.
    """
    with patch("app.main.ollama_client.health", AsyncMock(return_value=True)):
        with patch("app.main.ollama_client.list_models", AsyncMock(return_value=["llama3.2:3b"])):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["ollama"] == "connected"
    assert data["model"] == "llama3.2:3b"


@pytest.mark.asyncio
async def test_health_ollama_unreachable():
    """
    Test health endpoint when ollama is not reachable.
    Verifies service still returns 200 but reports ollama as unreachable.
    """
    with patch("app.main.ollama_client.health", AsyncMock(return_value=False)):
        with patch("app.main.ollama_client.list_models", AsyncMock(return_value=[])):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["ollama"] == "unreachable"
