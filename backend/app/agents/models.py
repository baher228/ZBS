from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentCapability(StrEnum):
    CONTENT_GENERATOR = "content_generator"
    LEGAL = "legal"
    DEMO = "demo"
    UNSUPPORTED = "unsupported"


class ReviewStatus(StrEnum):
    APPROVED = "approved"
    REVISE = "revise"
    FAILED = "failed"


class OrchestratorStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_REVISION = "needs_revision"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"
    UNAVAILABLE = "unavailable"


class AgentRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    startup_idea: str | None = None
    target_audience: str | None = None
    goal: str | None = None
    tone: str | None = None
    channel: str | None = None
    context: dict[str, str] = Field(default_factory=dict)


class ContentPackage(BaseModel):
    positioning: str
    landing_copy: str
    icp_notes: str
    launch_email: str
    social_post: str

    def as_output_dict(self) -> dict[str, str]:
        return self.model_dump()


class LegalIssueScan(BaseModel):
    important_notice: str
    jurisdiction_scope: str
    relevant_sources: str
    risk_summary: str
    founder_checklist: str
    questions_for_counsel: str
    next_steps: str

    def as_output_dict(self) -> dict[str, str]:
        return self.model_dump()


class AgentResponse(BaseModel):
    agent: AgentCapability
    title: str
    output: dict[str, str]
    summary: str


class ReviewResult(BaseModel):
    status: ReviewStatus
    score: float = Field(..., ge=0, le=1)
    relevance: float = Field(..., ge=0, le=1)
    completeness: float = Field(..., ge=0, le=1)
    clarity: float = Field(..., ge=0, le=1)
    actionability: float = Field(..., ge=0, le=1)
    feedback: str
    revision_instruction: str | None = None


class OrchestratorDecision(BaseModel):
    status: OrchestratorStatus
    selected_agent: AgentCapability
    message: str
    revision_instruction: str | None = None


class TaskClassification(BaseModel):
    agent: AgentCapability
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str


class LLMReviewEvaluation(BaseModel):
    relevance: float = Field(..., ge=0, le=1)
    completeness: float = Field(..., ge=0, le=1)
    clarity: float = Field(..., ge=0, le=1)
    actionability: float = Field(..., ge=0, le=1)
    feedback: str
    revision_instruction: str | None = None


class TaskRequest(AgentRequest):
    pass


class TaskResponse(BaseModel):
    selected_agent: AgentCapability
    agent_response: AgentResponse | None = None
    review: ReviewResult | None = None
    decision: OrchestratorDecision
