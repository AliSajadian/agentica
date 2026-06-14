'''Retrieve'''
from app.services.qdrant import qdrant_service
from app.core.embeddings import embedding_service
from app.models.schemas import SearchResult
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RetrieverService:
    """
    Higher level retrieval logic on top of qdrant_service.
    Handles reranking, deduplication and context building.
    Will be extended when llm-service is connected.
    """

    async def retrieve(
        self,
        question: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        metadata_filter: dict = None
    ) -> list[SearchResult]:
        '''Retrieve'''
        # embed question
        vector = embedding_service.embed_single(question)

        # search
        results = await qdrant_service.search(
            vector=vector,
            top_k=top_k,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter
        )

        # deduplicate by text
        results = self._deduplicate(results)

        # rerank by score
        results = self._rerank(results)

        logger.info("retriever_done", results=len(results))
        return results

    def _deduplicate(self, results: list[SearchResult]) -> list[SearchResult]:
        seen = set()
        unique = []
        for r in results:
            if r.text not in seen:
                seen.add(r.text)
                unique.append(r)
        return unique

    def _rerank(self, results: list[SearchResult]) -> list[SearchResult]:
        return sorted(results, key=lambda r: r.score, reverse=True)

    def build_context(self, results: list[SearchResult]) -> str:
        """
        Builds a single context string from results.
        Used when passing context to llm-service.
        """
        return "\n\n---\n\n".join(
            f"[Source: {r.metadata.get('source', 'unknown')}]\n{r.text}"
            for r in results
        )

    # ── Future: cross-encoder reranking ──────────────────────────────────────
    # from sentence_transformers import CrossEncoder
    # reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    #
    # def _rerank(self, results, query):
    #     pairs = [[query, r.text] for r in results]
    #     scores = reranker.predict(pairs)
    #     for r, s in zip(results, scores):
    #         r.score = float(s)
    #     return sorted(results, key=lambda r: r.score, reverse=True)
    # ─────────────────────────────────────────────────────────────────────────


retriever_service = RetrieverService()
