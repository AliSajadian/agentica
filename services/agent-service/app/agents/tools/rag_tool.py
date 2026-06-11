'''Rag tool'''
from app.models.schemas import AgentState
from app.clients.rag_client import RagClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client = RagClient()


async def retrieve_context(state: AgentState) -> AgentState:
    """LangGraph node: retrieve relevant chunks from rag-service."""
    chunks = await _client.search(state.message)
    logger.info("retrieve_context", chunks=len(chunks))
    return state.model_copy(
        update={
            "context_chunks": chunks, 
            "steps": state.steps + ["retrieve_context"]
        }
    )
