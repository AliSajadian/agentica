'''LLM tool'''
from app.models.schemas import AgentState
from app.clients.llm_client import LlmClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client = LlmClient()


async def generate_answer(state: AgentState) -> AgentState:
    """LangGraph node: generate answer via llm-service using retrieved context."""
    answer = await _client.rag_answer(
        question=state.message,
        context_chunks=state.context_chunks,
    )
    logger.info("generate_answer", answer_len=len(answer))
    return state.model_copy(
        update={
            "answer": answer, 
            "steps": state.steps + ["generate_answer"]
        }
    )
