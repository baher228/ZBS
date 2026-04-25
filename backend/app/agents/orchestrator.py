from app.agents.models import (
    AgentCapability,
    AgentRequest,
    OrchestratorDecision,
    OrchestratorStatus,
    ReviewStatus,
    TaskResponse,
)
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent


class Orchestrator:
    _content_keywords = {
        "content",
        "marketing",
        "copy",
        "landing",
        "email",
        "social",
        "post",
        "launch",
        "positioning",
        "icp",
    }
    _demo_keywords = {"demo", "prototype", "presentation", "pitch walkthrough"}
    _legal_keywords = {
        "legal",
        "law",
        "lawyer",
        "compliance",
        "privacy",
        "terms",
        "contract",
        "liability",
        "entity",
        "formation",
        "llc",
        "corporation",
        "accessibility",
        "ada",
        "ftc",
        "regulation",
        "regulatory",
    }

    def __init__(self, registry: AgentRegistry, review_agent: ReviewAgent) -> None:
        self.registry = registry
        self.review_agent = review_agent

    def handle_task(self, request: AgentRequest) -> TaskResponse:
        selected_agent = self.choose_agent(request)

        if selected_agent == AgentCapability.DEMO:
            decision = OrchestratorDecision(
                status=OrchestratorStatus.UNAVAILABLE,
                selected_agent=selected_agent,
                message="Demo Agent is planned but not available in this MVP slice.",
            )
            return TaskResponse(selected_agent=selected_agent, decision=decision)

        if selected_agent == AgentCapability.UNSUPPORTED:
            decision = OrchestratorDecision(
                status=OrchestratorStatus.UNSUPPORTED,
                selected_agent=selected_agent,
                message="This task is not supported yet. Try a content, landing page, email, or social launch task.",
            )
            return TaskResponse(selected_agent=selected_agent, decision=decision)

        agent = self.registry.get(selected_agent)
        if agent is None:
            decision = OrchestratorDecision(
                status=OrchestratorStatus.UNAVAILABLE,
                selected_agent=selected_agent,
                message=f"{selected_agent.value} is not registered.",
            )
            return TaskResponse(selected_agent=selected_agent, decision=decision)

        agent_response = agent.run(request)
        review = self.review_agent.review(request, agent_response)
        decision = self._decide(selected_agent, review.status, review.revision_instruction)
        return TaskResponse(
            selected_agent=selected_agent,
            agent_response=agent_response,
            review=review,
            decision=decision,
        )

    def choose_agent(self, request: AgentRequest) -> AgentCapability:
        text = " ".join(
            [
                request.prompt,
                request.goal or "",
                request.channel or "",
                request.context.get("task_type", ""),
            ]
        ).lower()
        if any(keyword in text for keyword in self._demo_keywords):
            return AgentCapability.DEMO
        if any(keyword in text for keyword in self._legal_keywords):
            return AgentCapability.LEGAL
        if any(keyword in text for keyword in self._content_keywords):
            return AgentCapability.CONTENT_GENERATOR
        return AgentCapability.UNSUPPORTED

    def _decide(
        self,
        selected_agent: AgentCapability,
        review_status: ReviewStatus,
        revision_instruction: str | None,
    ) -> OrchestratorDecision:
        if review_status == ReviewStatus.APPROVED:
            return OrchestratorDecision(
                status=OrchestratorStatus.COMPLETED,
                selected_agent=selected_agent,
                message="Agent output passed review.",
            )
        if review_status == ReviewStatus.REVISE:
            return OrchestratorDecision(
                status=OrchestratorStatus.NEEDS_REVISION,
                selected_agent=selected_agent,
                message="Agent output needs one revision pass.",
                revision_instruction=revision_instruction,
            )
        return OrchestratorDecision(
            status=OrchestratorStatus.FAILED,
            selected_agent=selected_agent,
            message="Agent output failed review.",
            revision_instruction=revision_instruction,
        )
