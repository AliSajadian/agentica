'''Memory tool'''
from app.models.schemas import AgentState, Message
from app.clients.memory_client import MemoryClient
from app.utils.logger import get_logger

logger = get_logger(__name__)

_client = MemoryClient()


async def fetch_history(state: AgentState) -> AgentState:
    """LangGraph node: load conversation history from memory-service."""
    raw = await _client.get_history(state.session_id)
    history = [Message(role=m["role"], content=m["content"]) for m in raw]
    logger.info("fetch_history", session_id=state.session_id, messages=len(history))
    return state.model_copy(update={"history": history, "steps": state.steps + ["fetch_history"]})


async def save_message(state: AgentState) -> AgentState:
    """LangGraph node: persist user message and assistant answer to memory-service."""
    await _client.save_message(state.session_id, "user", state.message)
    await _client.save_message(state.session_id, "assistant", state.answer)
    logger.info("save_message", session_id=state.session_id)
    return state.model_copy(update={"steps": state.steps + ["save_message"]})
