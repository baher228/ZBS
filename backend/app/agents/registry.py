from typing import Protocol

from app.agents.models import AgentCapability, AgentRequest, AgentResponse


class RunnableAgent(Protocol):
    capability: AgentCapability

    def run(self, request: AgentRequest) -> AgentResponse:
        ...


class AgentRegistry:
    def __init__(self, agents: list[RunnableAgent] | None = None) -> None:
        self._agents: dict[AgentCapability, RunnableAgent] = {}
        for agent in agents or []:
            self.register(agent)

    def register(self, agent: RunnableAgent) -> None:
        self._agents[agent.capability] = agent

    def get(self, capability: AgentCapability) -> RunnableAgent | None:
        return self._agents.get(capability)
