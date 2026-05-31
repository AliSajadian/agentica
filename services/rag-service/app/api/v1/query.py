'''Query'''
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.core.embeddings import embedding_service
from app.services.qdrant import qdrant_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    '''Query'''
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

        # answer is None until llm-service is connected
        # llm-service will receive question + context and return answer
        logger.info("query_completed", context_chunks=len(results))
        return QueryResponse(
            question=request.question,
            context_chunks=results,
            total_context=len(results),
            answer=None
        )

    except Exception as e:
        logger.error("query_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
