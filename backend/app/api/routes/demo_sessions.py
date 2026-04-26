from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException, Response, status

from app.agents.graphs.browser_demo import BrowserDemoGraphRunner
from app.demo_controller.actions import is_allowed_local_url
from app.demo_controller.models import (
    DemoSession,
    DemoSessionActionDecisionRequest,
    DemoSessionCreateRequest,
    DemoSessionMessageRequest,
)
from app.demo_controller.playwright_controller import BrowserControllerError, PlaywrightBrowserController
from app.demo_controller.store import demo_session_store

router = APIRouter(tags=["demo-sessions"])


@lru_cache
def get_browser_demo_graph_runner() -> BrowserDemoGraphRunner:
    return BrowserDemoGraphRunner(store=demo_session_store)


@lru_cache
def get_browser_controller() -> PlaywrightBrowserController:
    return PlaywrightBrowserController()


@router.post("/demo-sessions", response_model=DemoSession)
def create_demo_session(request: DemoSessionCreateRequest) -> DemoSession:
    if not is_allowed_local_url(request.app_base_url, request.app_base_url):
        raise HTTPException(status_code=400, detail="Only local app_base_url values are allowed")
    return demo_session_store.create_session(request)


@router.get("/demo-sessions/{session_id}", response_model=DemoSession)
def get_demo_session(session_id: str) -> DemoSession:
    session = demo_session_store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Demo session not found")
    return session


@router.post("/demo-sessions/{session_id}/message", response_model=DemoSession)
def send_demo_session_message(
    session_id: str, request: DemoSessionMessageRequest
) -> DemoSession:
    return get_browser_demo_graph_runner().run(session_id, request.message)


@router.post("/demo-sessions/{session_id}/actions/approve", response_model=DemoSession)
def approve_demo_session_actions(
    session_id: str, request: DemoSessionActionDecisionRequest
) -> DemoSession:
    session = get_demo_session(session_id)
    selected = (
        [action for action in session.pending_actions if action.id in request.action_ids]
        if request.action_ids
        else session.pending_actions
    )
    if not selected:
        return session

    approved = [
        action.model_copy(update={"status": "approved", "reason": request.reason})
        for action in selected
    ]
    try:
        executed, observations = get_browser_controller().execute(session, approved)
    except BrowserControllerError as exc:
        return demo_session_store.save_session(
            session.model_copy(update={"status": "failed", "last_error": str(exc)})
        )

    executed_count = len([action for action in executed if action.status == "executed"])
    current_step_id = session.current_step_id
    for action in executed:
        if action.status == "executed" and action.step_id:
            current_step_id = action.step_id
    remaining_pending = [action for action in session.pending_actions if action.id not in {a.id for a in selected}]
    updated = demo_session_store.save_session(
        session.model_copy(
            update={
                "status": "ready" if not remaining_pending else "waiting_for_approval",
                "pending_actions": remaining_pending,
                "action_log": [*session.action_log, *executed],
                "observations": [*session.observations, *observations],
                "action_budget": max(session.action_budget - executed_count, 0),
                "current_step_id": current_step_id,
                "last_error": None,
            }
        )
    )
    return updated


@router.post("/demo-sessions/{session_id}/actions/reject", response_model=DemoSession)
def reject_demo_session_actions(
    session_id: str, request: DemoSessionActionDecisionRequest
) -> DemoSession:
    session = get_demo_session(session_id)
    selected_ids = set(request.action_ids) if request.action_ids else {a.id for a in session.pending_actions}
    rejected = [
        action.model_copy(update={"status": "rejected", "reason": request.reason or "Rejected"})
        for action in session.pending_actions
        if action.id in selected_ids
    ]
    pending = [action for action in session.pending_actions if action.id not in selected_ids]
    return demo_session_store.save_session(
        session.model_copy(
            update={
                "status": "waiting_for_approval" if pending else "ready",
                "pending_actions": pending,
                "action_log": [*session.action_log, *rejected],
            }
        )
    )


@router.post("/demo-sessions/{session_id}/reset", response_model=DemoSession)
def reset_demo_session(session_id: str) -> DemoSession:
    return demo_session_store.reset_session(get_demo_session(session_id))


@router.post("/demo-sessions/{session_id}/verify", response_model=DemoSession)
def verify_demo_session(session_id: str) -> DemoSession:
    session = get_demo_session(session_id)
    result = get_browser_controller().verify(session)
    return demo_session_store.save_session(
        session.model_copy(
            update={
                "status": "ready" if result.passed else "failed",
                "verification_log": [*session.verification_log, result],
                "last_error": None if result.passed else result.message,
            }
        )
    )


@router.delete("/demo-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demo_session(session_id: str) -> Response:
    if not demo_session_store.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Demo session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
