'''Test ingest'''
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from app.main import app


@pytest.fixture
def mock_qdrant():
    '''Mock qdrant'''
    with patch("app.api.v1.ingest.qdrant_service") as mock:
        mock.upsert = AsyncMock(return_value=None)
        yield mock


@pytest.fixture
def mock_embedding():
    '''Mock enbedding'''
    with patch("app.api.v1.ingest.embedding_service") as mock:
        mock.embed = AsyncMock(return_value=[[0.1] * 384])
        yield mock


@pytest.mark.asyncio
async def test_ingest_text(mock_qdrant, mock_embedding):
    '''Test ingest'''
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/ingest", json={
            "text": "FastAPI is a modern web framework for building APIs with Python.",
            "source": "test_doc.txt",
            "metadata": {"author": "test"}
        })
    assert response.status_code == 200
    data = response.json()
    assert data["chunks_created"] >= 1
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_ingest_short_text_fails(mock_qdrant, mock_embedding):
    '''Test ingest'''
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post("/api/v1/ingest", json={
            "text": "too short",
        })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health():
    '''Test health'''
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
