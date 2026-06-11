'''Orchestrator'''
from typing import AsyncIterator
from langgraph.graph import StateGraph, END
from app.agents.base import BaseAgent
from app.agents.tools.memory_tool import fetch_history, save_message
from app.agents.tools.rag_tool import retrieve_context
from app.agents.tools.llm_tool import generate_answer
from app.models.schemas import AgentState
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _build_graph() -> StateGraph:
    """Build and compile the LangGraph agent graph."""
    graph = StateGraph(AgentState)

    graph.add_node("fetch_history", fetch_history)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("save_message", save_message)

    graph.set_entry_point("fetch_history")
    graph.add_edge("fetch_history", "retrieve_context")
    graph.add_edge("retrieve_context", "generate_answer")
    graph.add_edge("generate_answer", "save_message")
    graph.add_edge("save_message", END)

    return graph.compile()


class OrchestratorAgent(BaseAgent):
    """General-purpose agent backed by the LangGraph graph."""

    def __init__(self):
        """Compile the agent graph on instantiation."""
        self._graph = _build_graph()

    async def run(self, state: AgentState) -> AgentState:
        """Invoke the compiled graph and return final state."""
        logger.info("agent_run_start", session_id=state.session_id)
        result: AgentState = await self._graph.ainvoke(state)
        if isinstance(result, dict):
            result = AgentState(**result)
        logger.info("agent_run_complete", session_id=state.session_id, steps=result.steps)
        return result

    async def stream(self, state: AgentState) -> AsyncIterator[str]:
        """Stream node outputs from the graph."""
        async for chunk in self._graph.astream(state):
            for node_name, node_state in chunk.items():
                if node_name == "generate_answer" and node_state.answer:
                    yield node_state.answer
