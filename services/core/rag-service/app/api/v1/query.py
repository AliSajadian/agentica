'''Query'''
from fastapi import APIRouter, HTTPException
import httpx
from app.models.schemas import QueryRequest, QueryResponse
from app.core.embeddings import embedding_service
from app.services.qdrant import qdrant_service
from app.utils.logger import get_logger
from app.config import settings

router = APIRouter()
logger = get_logger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    RAG query endpoint — retrieves context from Qdrant then
    calls llm-service to generate a grounded answer.
    """
    try:
        logger.info("query_started", question=request.question)

        # embed question
        query_vector = embedding_service.embed_single(request.question)

        # retrieve context
        results = await qdrant_service.search(
            vector=query_vector,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            metadata_filter=request.metadata_filter
        )

        # call llm-service /chat/rag
        if results:
            answer = await _call_llm_service(
                question=request.question,
                context_chunks=results
            )
        else:
            answer = None

        # llm-service will receive question + context and return answer
        logger.info("query_completed", context_chunks=len(results))
        return QueryResponse(
            question=request.question,
            context_chunks=results,
            total_context=len(results),
            answer=answer
        )

    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _call_llm_service(question: str, context_chunks: list) -> str:
    """
    Calls llm-service /chat/rag endpoint with question and retrieved chunks.
    Returns generated answer string.
    """
    payload = {
        "question": question,
        "context_chunks": [
            {
                "text": chunk.text,
                "score": chunk.score,
                "metadata": chunk.metadata,
                "chunk_index": chunk.chunk_index
            }
            for chunk in context_chunks
        ],
        "stream": False,
        "system_prompt": None
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.LLM_SERVICE_URL}/api/v1/chat/rag",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data["answer"]
