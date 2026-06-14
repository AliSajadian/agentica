'''Base agent'''
from abc import ABC, abstractmethod
from app.models.schemas import AgentState


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    async def run(self, state: AgentState) -> AgentState:
        """Execute the agent logic and return updated state."""

    @abstractmethod
    async def stream(self, state: AgentState):
        """Stream agent output tokens as they are produced."""
