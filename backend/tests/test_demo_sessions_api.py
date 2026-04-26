from fastapi.testclient import TestClient

from app.api.routes.campaigns import (
    get_campaign_graph_runner,
    get_demo_chat_graph_runner,
    get_qualification_graph_runner,
)
from app.api.routes.demo_sessions import (
    get_browser_controller,
    get_browser_demo_graph_runner,
)
from app.agents.store import campaign_store
from app.demo_controller.actions import validate_action
from app.demo_controller.models import BrowserAction, DemoSessionCreateRequest
from app.demo_controller.store import demo_session_store
from app.main import create_app


client = TestClient(create_app())


def setup_function() -> None:
    campaign_store.clear()
    demo_session_store.clear()
    get_campaign_graph_runner.cache_clear()
    get_demo_chat_graph_runner.cache_clear()
    get_qualification_graph_runner.cache_clear()
    get_browser_demo_graph_runner.cache_clear()
    get_browser_controller.cache_clear()


def create_session(mode: str = "bounded_auto") -> dict:
    response = client.post(
        "/api/v1/demo-sessions",
        json={
            "demo_room_id": "room_tracepilot",
            "scenario": "tracepilot_render",
            "mode": mode,
            "app_base_url": "http://localhost:5173",
            "objective": "Show Render how TracePilot debugs a failed AI-agent run",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_session_creation_initializes_manifest_and_local_url() -> None:
    body = create_session()

    assert body["id"].startswith("ds_")
    assert body["status"] == "ready"
    assert body["manifest"]["allowed_routes"]["tool_call"] == "/sandbox/tracepilot/render/tool-call"
    assert "[data-demo-id='tool-call-detail']" in body["manifest"]["allowed_selectors"]


def test_external_app_base_url_is_rejected() -> None:
    response = client.post(
        "/api/v1/demo-sessions",
        json={
            "demo_room_id": "room_tracepilot",
            "app_base_url": "https://render.com",
            "objective": "Show Render how TracePilot debugs a failed AI-agent run",
        },
    )

    assert response.status_code == 400
    assert "local" in response.json()["detail"].lower()


def test_missing_session_returns_404() -> None:
    response = client.get("/api/v1/demo-sessions/ds_missing")

    assert response.status_code == 404


def test_tracepilot_walkthrough_prompt_executes_bounded_actions() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/demo-sessions/{session['id']}/message",
        json={"message": "Can you walk me through the failure?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["current_step_id"] == "tool_call"
    assert body["observations"][-1]["screenshot_path"].endswith("/tool_call.png")
    assert "tool-call-detail" in body["observations"][-1]["visible_demo_ids"]
    assert [message["role"] for message in body["transcript"]] == ["user", "assistant"]
    assert any(action["type"] == "assert_visible" for action in body["action_log"])


def test_why_did_it_fail_opens_state_diff() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/demo-sessions/{session['id']}/message",
        json={"message": "Why did it fail?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["current_step_id"] == "state_diff"
    assert body["observations"][-1]["route_id"] == "state_diff"
    assert "stale service version" in body["transcript"][-1]["content"]


def test_alert_prompt_opens_alert_setup() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/demo-sessions/{session['id']}/message",
        json={"message": "Can this alert our team?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["current_step_id"] == "alerts"
    assert "alert-setup" in body["observations"][-1]["visible_demo_ids"]


def test_privacy_prompt_answers_without_browser_action() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/demo-sessions/{session['id']}/message",
        json={"message": "What about privacy and redaction?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["action_log"] == []
    assert "redacts" in body["transcript"][-1]["content"]


def test_unknown_selector_is_rejected_by_safety_gate() -> None:
    session = demo_session_store.create_session(
        DemoSessionCreateRequest(
            demo_room_id="room_tracepilot",
            objective="Show Render how TracePilot debugs a failed AI-agent run",
        )
    )
    action = BrowserAction(
        type="click",
        label="Click unknown control",
        selector="[data-demo-id='unknown']",
        risk="low",
    )

    result = validate_action(session, action)

    assert not result.allowed
    assert "selector" in (result.reason or "")


def test_medium_risk_action_requires_approval_in_manual_mode() -> None:
    session = demo_session_store.create_session(
        DemoSessionCreateRequest(
            demo_room_id="room_tracepilot",
            mode="manual_approval",
            objective="Show Render how TracePilot debugs a failed AI-agent run",
        )
    )
    action = BrowserAction(
        type="click",
        label="Open alerts",
        selector="[data-demo-id='open-alerts']",
        risk="medium",
    )

    result = validate_action(session, action)

    assert result.allowed
    assert result.needs_approval


def test_rejected_pending_action_is_logged_and_not_executed() -> None:
    session = demo_session_store.create_session(
        DemoSessionCreateRequest(
            demo_room_id="room_tracepilot",
            objective="Show Render how TracePilot debugs a failed AI-agent run",
        )
    )
    pending = BrowserAction(
        type="click",
        label="Open alerts",
        selector="[data-demo-id='open-alerts']",
        risk="medium",
        status="pending",
    )
    demo_session_store.save_session(
        session.model_copy(update={"status": "waiting_for_approval", "pending_actions": [pending]})
    )

    response = client.post(
        f"/api/v1/demo-sessions/{session.id}/actions/reject",
        json={"action_ids": [pending.id], "reason": "Prospect asked to pause"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "ready"
    assert body["pending_actions"] == []
    assert body["action_log"][-1]["status"] == "rejected"
    assert body["observations"] == []


def test_action_budget_exhaustion_stops_execution() -> None:
    session = demo_session_store.create_session(
        DemoSessionCreateRequest(
            demo_room_id="room_tracepilot",
            objective="Show Render how TracePilot debugs a failed AI-agent run",
        )
    )
    demo_session_store.save_session(session.model_copy(update={"action_budget": 0}))

    response = client.post(
        f"/api/v1/demo-sessions/{session.id}/message",
        json={"message": "Can you walk me through the failure?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "failed"
    assert body["last_error"] == "action budget exhausted"
    assert body["observations"] == []


def test_verification_failure_leaves_session_recoverable() -> None:
    session = demo_session_store.create_session(
        DemoSessionCreateRequest(
            demo_room_id="room_tracepilot",
            objective="Show Render how TracePilot debugs a failed AI-agent run",
        )
    )
    demo_session_store.save_session(session.model_copy(update={"current_step_id": "tool_call"}))

    response = client.post(f"/api/v1/demo-sessions/{session.id}/verify")

    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "failed"
    assert body["last_error"] == "tool-call-detail is not visible."
    assert body["action_budget"] == 20


def test_acceptance_path_reaches_alerts_within_budget() -> None:
    session = create_session()

    for message in [
        "Can you walk me through the failure?",
        "Why did it fail?",
        "Can this alert our team?",
    ]:
        response = client.post(
            f"/api/v1/demo-sessions/{session['id']}/message",
            json={"message": message},
        )
        assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ready"
    assert body["current_step_id"] == "alerts"
    assert "alert-setup" in body["observations"][-1]["visible_demo_ids"]

    lookup = client.get(f"/api/v1/demo-sessions/{session['id']}")
    assert lookup.status_code == 200


def test_browser_guided_chat_keeps_demo_room_qualification_working() -> None:
    campaign_response = client.post(
        "/api/v1/campaigns",
        json={
            "product_name": "TracePilot",
            "product_description": (
                "Agent observability platform that helps engineering teams inspect "
                "tool calls, state diffs, and failed AI-agent runs."
            ),
            "target_audience": "AI platform engineering teams",
            "prospect_company": "Render",
            "prospect_description": "Cloud application platform running AI worker services.",
        },
    )
    assert campaign_response.status_code == 200
    demo_room_id = campaign_response.json()["demo_room"]["id"]
    session_response = client.post(
        "/api/v1/demo-sessions",
        json={
            "demo_room_id": demo_room_id,
            "scenario": "tracepilot_render",
            "mode": "bounded_auto",
            "app_base_url": "http://localhost:5173",
            "objective": "Show Render how TracePilot debugs a failed AI-agent run",
        },
    )
    session_id = session_response.json()["id"]

    chat_response = client.post(
        f"/api/v1/demo-sessions/{session_id}/message",
        json={"message": "Can you walk me through the failure?"},
    )
    qualify_response = client.post(f"/api/v1/demo-rooms/{demo_room_id}/qualify")

    assert chat_response.status_code == 200
    assert qualify_response.status_code == 200
    assert qualify_response.json()["qualification_status"] == "qualified"
