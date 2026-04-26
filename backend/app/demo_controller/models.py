from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, TypedDict
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agents.campaign_models import ChatMessage


DemoSessionStatus = Literal[
    "initializing",
    "ready",
    "planning",
    "acting",
    "waiting_for_approval",
    "verifying",
    "completed",
    "failed",
]
DemoSessionMode = Literal["manual_approval", "bounded_auto"]
BrowserActionType = Literal[
    "navigate",
    "click",
    "fill",
    "select",
    "hover",
    "wait_for",
    "assert_visible",
    "snapshot",
    "screenshot",
]
ActionRisk = Literal["low", "medium", "high"]
ActionStatus = Literal["pending", "approved", "rejected", "executed", "failed"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class DemoActionManifest(BaseModel):
    scenario: str
    app_base_url: str
    allowed_routes: dict[str, str] = Field(default_factory=dict)
    allowed_selectors: list[str] = Field(default_factory=list)
    demo_targets: dict[str, str] = Field(default_factory=dict)
    workflow_steps: list[str] = Field(default_factory=list)


class BrowserAction(BaseModel):
    id: str = Field(default_factory=lambda: new_id("act"))
    type: BrowserActionType
    label: str
    risk: ActionRisk = "low"
    step_id: str | None = None
    route_id: str | None = None
    url: str | None = None
    selector: str | None = None
    value: str | None = None
    expected_demo_id: str | None = None
    status: ActionStatus = "pending"
    reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    executed_at: datetime | None = None


class BrowserObservation(BaseModel):
    url: str
    route_id: str | None = None
    visible_demo_ids: list[str] = Field(default_factory=list)
    title: str | None = None
    screenshot_path: str | None = None
    captured_at: datetime = Field(default_factory=utc_now)


class VerificationResult(BaseModel):
    action_id: str | None = None
    step_id: str | None = None
    passed: bool
    message: str
    expected_demo_id: str | None = None
    observed_demo_ids: list[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=utc_now)


class DemoSession(BaseModel):
    id: str = Field(default_factory=lambda: new_id("ds"))
    demo_room_id: str
    scenario: Literal["tracepilot_render"] = "tracepilot_render"
    mode: DemoSessionMode = "bounded_auto"
    app_base_url: str = "http://localhost:5173"
    objective: str
    status: DemoSessionStatus = "initializing"
    current_step_id: str | None = None
    action_budget: int = Field(default=20, ge=0)
    transcript: list[ChatMessage] = Field(default_factory=list)
    action_log: list[BrowserAction] = Field(default_factory=list)
    pending_actions: list[BrowserAction] = Field(default_factory=list)
    verification_log: list[VerificationResult] = Field(default_factory=list)
    observations: list[BrowserObservation] = Field(default_factory=list)
    manifest: DemoActionManifest
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class DemoSessionCreateRequest(BaseModel):
    demo_room_id: str = Field(..., min_length=1)
    scenario: Literal["tracepilot_render"] = "tracepilot_render"
    mode: DemoSessionMode = "bounded_auto"
    app_base_url: str = "http://localhost:5173"
    objective: str = "Show Render how TracePilot debugs a failed AI-agent run"


class DemoSessionMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)


class DemoSessionActionDecisionRequest(BaseModel):
    action_ids: list[str] = Field(default_factory=list)
    reason: str | None = None


class BrowserDemoGraphState(TypedDict, total=False):
    session_id: str
    message: str | None
    session: DemoSession
    observation: BrowserObservation
    planned_actions: list[BrowserAction]
    executable_actions: list[BrowserAction]
    rejected_actions: list[BrowserAction]
    verification_results: list[VerificationResult]
    reply: str
    error: str
    metadata: dict[str, Any]
