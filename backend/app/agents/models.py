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
    jurisdictions: list[str] = Field(default_factory=lambda: ["US"])
    industries: list[str] = Field(default_factory=list)
    uploaded_doc_text: str | None = None
    startup_url: str | None = None
    review_mode: bool = False
    additional_context: str | None = None
    document_type: str | None = None


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
    follow_up_needed: str = ""

    def as_output_dict(self) -> dict[str, str]:
        return {k: v for k, v in self.model_dump().items() if v}


class LegalDocumentDraft(BaseModel):
    important_notice: str
    document_title: str
    document_body: str
    key_provisions: str
    customization_notes: str
    jurisdiction_notes: str
    next_steps: str
    follow_up_needed: str = ""

    def as_output_dict(self) -> dict[str, str]:
        return {k: v for k, v in self.model_dump().items() if v}


class DocumentReviewResult(BaseModel):
    important_notice: str
    document_summary: str
    compliance_gaps: str
    risk_areas: str
    recommendations: str
    applicable_regulations: str
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


class SocialPost(BaseModel):
    caption: str
    hashtags: str = ""
    call_to_action: str = ""
    follow_up_needed: str = ""

    def as_output_dict(self) -> dict[str, str]:
        return {k: v for k, v in self.model_dump().items() if v}


class SocialPostRequest(BaseModel):
    platform: str = Field(default="linkedin", pattern=r"^(linkedin|twitter|instagram|facebook)$")
    topic: str = Field(..., min_length=1)
    extra_context: str = ""
    tone: str = "professional"
    num_images: int = Field(default=1, ge=0, le=3)


class SocialPostResponse(BaseModel):
    post: dict[str, str]
    images: list[str] = Field(default_factory=list)
    platform: str


class TaskRequest(AgentRequest):
    pass


class TaskResponse(BaseModel):
    selected_agent: AgentCapability
    agent_response: AgentResponse | None = None
    review: ReviewResult | None = None
    decision: OrchestratorDecision


# ── Legal Chat Models ──────────────────────────────────────


class LegalChatMode(StrEnum):
    OVERVIEW = "overview"
    LEGAL_ADVICE = "legal_advice"
    TAX = "tax"
    DOCUMENT_DRAFTING = "document_drafting"


class LegalChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)


class LegalChatRequest(BaseModel):
    messages: list[LegalChatMessage] = Field(..., min_length=1)
    mode: LegalChatMode = LegalChatMode.LEGAL_ADVICE
    document_type: str | None = None
    jurisdictions: list[str] = Field(default_factory=lambda: ["US"])


class LegalChatResponse(BaseModel):
    reply: str
    document: LegalDocumentDraft | None = None
    follow_up_questions: list[str] = Field(default_factory=list)
    mode: LegalChatMode
    sources_used: list[str] = Field(default_factory=list)


class LegalOverviewIssue(BaseModel):
    title: str
    severity: str = Field(..., pattern=r"^(high|medium|low)$")
    description: str
    recommendation: str


class LegalOverviewResponse(BaseModel):
    summary: str
    potential_issues: list[LegalOverviewIssue] = Field(default_factory=list)
    recommended_documents: list[str] = Field(default_factory=list)
    missing_info: list[str] = Field(default_factory=list)
    compliance_areas: list[str] = Field(default_factory=list)


# ── Content Chat Models ──────────────────────────────────────


class ContentChatMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ContentChatRequest(BaseModel):
    messages: list[ContentChatMessage] = Field(..., min_length=1)
    workflow: str | None = None
    image_mode: str = Field(default="ask", pattern=r"^(ask|generate|reference|none)$")
    reference_image_urls: list[str] = Field(default_factory=list)
    existing_image_note: str = ""
    existing_generated_content: dict[str, str] | None = None


class ContentChatResponse(BaseModel):
    reply: str
    follow_up_questions: list[str] = Field(default_factory=list)
    content_ready: bool = False
    generated_content: dict[str, str] | None = None


# ── Marketing Research Chat Models ──────────────────────────────────────


class MarketingResearchMessage(BaseModel):
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)


class MarketingResearchRequest(BaseModel):
    messages: list[MarketingResearchMessage] = Field(..., min_length=1)
    workflow: str | None = None


class MarketingResearchResponse(BaseModel):
    reply: str
    follow_up_questions: list[str] = Field(default_factory=list)
    research_ready: bool = False
    research_data: dict[str, str] | None = None
