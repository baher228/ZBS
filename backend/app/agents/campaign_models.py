from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    name: str
    agent: str
    status: Literal["completed", "failed"] = "completed"
    summary: str


class CampaignCreateRequest(BaseModel):
    product_name: str = Field(..., min_length=1)
    product_description: str = Field(..., min_length=20)
    product_url: str | None = None
    target_audience: str | None = None
    prospect_company: str = Field(..., min_length=1)
    prospect_description: str | None = None
    prospect_url: str | None = None


class ProductProfile(BaseModel):
    name: str
    category: str
    one_liner: str
    core_problem: str
    key_value_props: list[str] = Field(default_factory=list)
    proof_points: list[str] = Field(default_factory=list)
    likely_objections: list[str] = Field(default_factory=list)


class ICPProfile(BaseModel):
    primary_buyer: str
    ideal_company: str
    trigger_events: list[str] = Field(default_factory=list)
    qualification_criteria: list[str] = Field(default_factory=list)
    disqualifiers: list[str] = Field(default_factory=list)


class ProspectProfile(BaseModel):
    company_name: str
    description: str
    likely_pain_points: list[str] = Field(default_factory=list)
    relevance_angle: str
    personalization_assumptions: list[str] = Field(default_factory=list)


class DemoBrief(BaseModel):
    title: str
    narrative: str
    talking_points: list[str] = Field(default_factory=list)
    qualifying_questions: list[str] = Field(default_factory=list)
    objection_handlers: list[str] = Field(default_factory=list)


class OutreachMessage(BaseModel):
    subject: str
    body: str
    channel: Literal["email", "linkedin"] = "email"
    demo_room_url: str


class OutreachDraft(BaseModel):
    subject: str
    body: str
    channel: Literal["email", "linkedin"] = "email"


class ReadinessScore(BaseModel):
    score: int = Field(..., ge=0, le=100)
    verdict: Literal["ready", "needs_more_context", "weak_fit"]
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class DemoRoom(BaseModel):
    id: str
    campaign_id: str
    prospect_company: str
    headline: str
    relevance_summary: str
    suggested_questions: list[str] = Field(default_factory=list)
    cta_label: str = "Send me the summary"
    transcript: list[ChatMessage] = Field(default_factory=list)


class CampaignResponse(BaseModel):
    campaign_id: str
    product_profile: ProductProfile
    icp: ICPProfile
    prospect_profile: ProspectProfile
    demo_brief: DemoBrief
    outreach_message: OutreachMessage
    demo_room: DemoRoom
    readiness_score: ReadinessScore
    workflow_steps: list[WorkflowStep]


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    demo_room_id: str
    reply: str
    transcript: list[ChatMessage]


class FollowUpEmail(BaseModel):
    subject: str
    body: str


class QualificationReport(BaseModel):
    demo_room_id: str
    lead_score: int = Field(..., ge=0, le=100)
    qualification_status: Literal["qualified", "nurture", "unqualified"]
    pain_points: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    urgency: str
    recommended_next_step: str
    crm_note: str
    follow_up_email: FollowUpEmail


class ProductStrategy(BaseModel):
    product_profile: ProductProfile
    icp: ICPProfile


class CampaignGraphState(TypedDict, total=False):
    request: CampaignCreateRequest
    campaign_id: str
    demo_room_id: str
    product_profile: ProductProfile
    icp: ICPProfile
    prospect_profile: ProspectProfile
    demo_brief: DemoBrief
    outreach_message: OutreachMessage
    readiness_score: ReadinessScore
    demo_room: DemoRoom
    workflow_steps: list[WorkflowStep]


class DemoChatGraphState(TypedDict, total=False):
    demo_room_id: str
    message: str
    demo_room: DemoRoom
    reply: str
    transcript: list[ChatMessage]


class QualificationGraphState(TypedDict, total=False):
    demo_room_id: str
    demo_room: DemoRoom
    qualification_report: QualificationReport
