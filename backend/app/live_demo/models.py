from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


LiveDemoState = Literal[
    "greeting",
    "discovering",
    "demoing",
    "answering_question",
    "qualifying",
    "summarizing",
]

DemoEventType = Literal[
    "say",
    "navigate",
    "cursor.move",
    "cursor.click",
    "highlight.show",
    "highlight.hide",
    "wait",
    "lead.profile.updated",
]


class DemoElement(BaseModel):
    id: str
    label: str
    role: Literal["button", "link", "tab", "input", "card", "chart", "section", "panel"]
    description: str
    selector: str
    safe_to_click: bool = False
    requires_approval: bool = False
    destructive: bool = False


class PageAction(BaseModel):
    id: str
    type: Literal["highlight", "cursor.move", "click", "navigate"]
    label: str
    element_id: str | None = None
    target_page_id: str | None = None
    intent: str
    requires_approval: bool = False


class DemoPageManifest(BaseModel):
    page_id: str
    route: str
    title: str
    summary: str
    visible_concepts: list[str] = Field(default_factory=list)
    elements: list[DemoElement] = Field(default_factory=list)
    allowed_actions: list[PageAction] = Field(default_factory=list)


class KnowledgeRecord(BaseModel):
    id: str
    topic: str
    content: str
    tags: list[str] = Field(default_factory=list)
    approved: bool = True


class DemoFlowStep(BaseModel):
    id: str
    page_id: str
    objective: str
    talk_track: str
    recommended_action_ids: list[str] = Field(default_factory=list)


class DemoFlow(BaseModel):
    id: str
    name: str
    goal: str
    entry_page_id: str
    steps: list[DemoFlowStep] = Field(default_factory=list)


class DemoManifest(BaseModel):
    startup_id: str
    product_name: str
    product_description: str = ""
    target_persona: str
    cta: str
    pages: list[DemoPageManifest]
    flows: list[DemoFlow]
    knowledge: list[KnowledgeRecord]
    qualification_questions: list[str] = Field(default_factory=list)
    restricted_claims: list[str] = Field(default_factory=list)


class ApprovedQA(BaseModel):
    question: str
    answer: str


class FounderDemoInput(BaseModel):
    product_name: str = "Demeo"
    product_description: str = ""
    product_url: str = "http://127.0.0.1:5175"
    target_customer: str = ""
    prospect_description: str = ""
    demo_goals: list[str] = Field(default_factory=list)
    founder_walkthrough: str = ""
    approved_qa: list[ApprovedQA] = Field(default_factory=list)
    cta: str = "Book a setup call"
    qualification_questions: list[str] = Field(default_factory=list)


class DemoSetup(BaseModel):
    id: str = Field(default_factory=lambda: new_id("setup"))
    startup_id: str
    founder_input: FounderDemoInput
    manifest: DemoManifest
    status: Literal["draft", "approved"] = "draft"
    source: Literal["cached_extraction", "provided_manifest", "live_extraction"] = "cached_extraction"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DemoSetupCreateRequest(BaseModel):
    startup_id: str | None = None
    founder_input: FounderDemoInput
    source: Literal["cached_extraction", "provided_manifest"] = "cached_extraction"
    manifest: DemoManifest | None = None
    approve: bool = True


class DemoSetupApproveRequest(BaseModel):
    approved: bool = True


class LeadProfile(BaseModel):
    use_case: str | None = None
    urgency: str | None = None
    current_solution: str | None = None
    interested_features: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    score: int = Field(default=45, ge=0, le=100)


class ConversationTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=utc_now)


class DemoEvent(BaseModel):
    id: str = Field(default_factory=lambda: new_id("evt"))
    type: DemoEventType
    text: str | None = None
    page_id: str | None = None
    route: str | None = None
    element_id: str | None = None
    label: str | None = None
    duration_ms: int | None = None
    patch: dict[str, Any] | None = None


class LiveDemoSession(BaseModel):
    id: str = Field(default_factory=lambda: new_id("lds"))
    startup_id: str = "demeo"
    current_page_id: str = "setup"
    state: LiveDemoState = "greeting"
    transcript: list[ConversationTurn] = Field(default_factory=list)
    lead_profile: LeadProfile = Field(default_factory=LeadProfile)
    action_log: list[DemoEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class LiveDemoSessionCreateRequest(BaseModel):
    startup_id: str | None = None
    current_page_id: str | None = None


class LiveDemoMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    current_page_id: str | None = None
    visible_element_ids: list[str] = Field(default_factory=list)


class LiveDemoMessageResponse(BaseModel):
    session: LiveDemoSession
    reply: str
    events: list[DemoEvent]
    available_actions: list[PageAction]
