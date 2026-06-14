'''Routes'''
from fastapi import APIRouter, HTTPException
from app.models.schemas import AgentRunRequest, AgentRunResponse, AgentState
from app.agents.orchestrator import OrchestratorAgent
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
_agent = OrchestratorAgent()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """Run the agent for a single turn and return the full response."""
    state = AgentState(
        session_id=request.session_id,
        user_id=request.user_id,
        message=request.message,
    )
    try:
        result = await _agent.run(state)
    except Exception as exc:
        logger.error("agent_run_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Agent run failed") from exc

    return AgentRunResponse(
        session_id=result.session_id,
        answer=result.answer,
        steps=result.steps,
    )
