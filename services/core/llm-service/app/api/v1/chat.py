'''Chat'''
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse, RAGRequest, RAGResponse
from app.core.ollama import ollama_client
from app.services.prompt_builder import prompt_builder
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with message history.
    Accepts list of messages with roles (system/user/assistant).
    """
    try:
        logger.info("chat_started", messages=len(request.messages), stream=request.stream)

        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        if request.stream:
            async def stream_generator():
                async for token in ollama_client.chat_stream(messages):
                    yield token

            return StreamingResponse(
                stream_generator(),
                media_type="text/plain"
            )

        answer = await ollama_client.chat(messages)
        logger.info("chat_done")
        return ChatResponse(
            answer=answer,
            model=ollama_client.model
        )

    except Exception as e:
        logger.error("chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))from e


@router.post("/chat/rag", response_model=RAGResponse)
async def chat_rag(request: RAGRequest):
    """
    RAG-powered chat.
    Receives question + context chunks from rag-service.
    Builds prompt and returns grounded answer.
    """
    try:
        logger.info(
            "rag_chat_started",
            question=request.question,
            chunks=len(request.context_chunks),
            stream=request.stream
        )

        # build messages with context
        messages = prompt_builder.build_rag_messages(
            question=request.question,
            context_chunks=request.context_chunks,
            system_prompt=request.system_prompt
        )

        if request.stream:
            async def stream_generator():
                async for token in ollama_client.chat_stream(messages):
                    yield token

            return StreamingResponse(
                stream_generator(),
                media_type="text/plain"
            )

        answer = await ollama_client.chat(messages)
        logger.info("rag_chat_done", answer_length=len(answer))

        return RAGResponse(
            question=request.question,
            answer=answer,
            model=ollama_client.model,
            context_used=len(request.context_chunks)
        )

    except Exception as e:
        logger.error("rag_chat_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
