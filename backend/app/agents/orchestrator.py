from __future__ import annotations

from app.agents.llm import LLMProvider
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
    _legal_keywords = {
        "legal",
        "privacy",
        "compliance",
        "terms",
        "gdpr",
        "llc",
        "soc2",
        "dpa",
        "claim",
        "claims",
        "testimonial",
        "accessibility",
        "counsel",
    }
    _demo_keywords = {"demo", "prototype", "presentation", "pitch walkthrough"}

    def __init__(
        self,
        registry: AgentRegistry,
        review_agent: ReviewAgent,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.registry = registry
        self.review_agent = review_agent
        self.llm_provider = llm_provider

    def handle_task(self, request: AgentRequest) -> TaskResponse:
        selected_agent = self.choose_agent(request)

        if selected_agent == AgentCapability.DEMO:
            decision = OrchestratorDecision(
                status=OrchestratorStatus.UNAVAILABLE,
                selected_agent=selected_agent,
                message="Demo Agent is handled by the campaign demo-room workflow, not the generic tasks route.",
            )
            return TaskResponse(selected_agent=selected_agent, decision=decision)

        if selected_agent == AgentCapability.UNSUPPORTED:
            decision = OrchestratorDecision(
                status=OrchestratorStatus.UNSUPPORTED,
                selected_agent=selected_agent,
                message="This task is not supported yet. Try a content or legal task.",
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
        task_type = request.context.get("task_type", "").lower()
        if task_type == "legal":
            return AgentCapability.LEGAL
        if task_type == "content":
            return AgentCapability.CONTENT_GENERATOR

        if self.llm_provider is not None:
            return self._llm_classify(request)

        return self._keyword_classify(request)

    def _llm_classify(self, request: AgentRequest) -> AgentCapability:
        classification = self.llm_provider.classify_task(request)
        return classification.agent

    def _keyword_classify(self, request: AgentRequest) -> AgentCapability:
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
