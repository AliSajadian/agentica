'''Complete'''
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import CompleteRequest, CompleteResponse
from app.core.ollama import ollama_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/complete", response_model=CompleteResponse)
async def complete(request: CompleteRequest):
    """Single prompt completion — no context, direct LLM call."""
    try:
        logger.info("complete_started", stream=request.stream)

        if request.stream:
            async def stream_generator():
                async for token in ollama_client.generate_stream(request.prompt):
                    yield token

            return StreamingResponse(
                stream_generator(),
                media_type="text/plain"
            )

        answer = await ollama_client.generate(request.prompt)
        logger.info("complete_done")
        return CompleteResponse(
            prompt=request.prompt,
            answer=answer,
            model=ollama_client.model
        )

    except Exception as e:
        logger.error("complete_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
