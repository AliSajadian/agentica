'''Search'''
from fastapi import APIRouter, HTTPException
from app.models.schemas import SearchRequest, SearchResponse
from app.core.embeddings import embedding_service
from app.services.qdrant import qdrant_service
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    '''Search'''
    try:
        logger.info("search_started", query=request.query, top_k=request.top_k)

        # embed the query
        query_vector = embedding_service.embed_single(request.query)

        # search qdrant
        results = await qdrant_service.search(
            vector=query_vector,
            top_k=request.top_k,
            score_threshold=request.score_threshold,
            metadata_filter=request.metadata_filter
        )

        logger.info("search_completed", results=len(results))
        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results)
        )

    except Exception as e:
        logger.error("search_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
    