'''QDrant'''
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.config import settings
from app.models.schemas import SearchResult
from app.utils.logger import get_logger
from uuid import uuid4

logger = get_logger(__name__)


class QdrantService:
    '''Qdrant Service'''
    def __init__(self):
        self.client = None
        self.collection = settings.QDRANT_COLLECTION

    def _get_client(self):
        self.client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        return self.client

    async def init_collection(self, vector_size: int = 384):
        """Create collection if it doesn't exist."""
        existing = await self._get_client().get_collections()
        names = [c.name for c in existing.collections]

        if self.collection not in names:
            await self._get_client().create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info("qdrant_collection_created", collection=self.collection)
        else:
            logger.info("qdrant_collection_exists", collection=self.collection)

    async def upsert(self, chunks: list[dict], embeddings: list[list[float]]):
        """Store chunks with their embeddings."""
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    **chunk["metadata"]
                }
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        await self._get_client().upsert(
            collection_name=self.collection,
            points=points
        )
        logger.info("qdrant_upsert_done", count=len(points))

    async def search(
        self,
        vector: list[float],
        top_k: int = 5,
        score_threshold: float = 0.5,
        metadata_filter: dict = None
    ) -> list[SearchResult]:
        """Search similar vectors."""

        qdrant_filter = None
        if metadata_filter:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key=k,
                        match=MatchValue(value=v)
                    )
                    for k, v in metadata_filter.items()
                ]
            )

        results = await self._get_client().query_points( # search
            collection_name=self.collection,
            query=vector,
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
            with_payload=True
        )

        return [
            SearchResult(
                text=r.payload.get("text", ""),
                score=r.score,
                metadata={k: v for k, v in r.payload.items() if k != "text"},
                chunk_index=r.payload.get("chunk_index", 0)
            )
            for r in results.points
        ]

    async def delete_by_source(self, source: str):
        """Delete all chunks from a specific source."""
        await self._get_client().delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source)
                    )
                ]
            )
        )
        logger.info("qdrant_deleted_by_source", source=source)


# ── Alternative: sync client (for non-async contexts) ────────────────────────
# from qdrant_client import QdrantClient
# client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
# ─────────────────────────────────────────────────────────────────────────────

qdrant_service = QdrantService()
