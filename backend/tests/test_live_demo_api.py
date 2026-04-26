from fastapi.testclient import TestClient

from app.api.routes.live_demo import get_live_demo_runtime
from app.live_demo.store import live_demo_session_store
from app.main import create_app


client = TestClient(create_app())


def setup_function() -> None:
    live_demo_session_store.clear()
    get_live_demo_runtime.cache_clear()


def create_session() -> dict:
    response = client.post(
        "/api/v1/live-demo/sessions",
        json={"startup_id": "demeo", "current_page_id": "setup"},
    )
    assert response.status_code == 200
    return response.json()


def test_manifest_exposes_pages_and_actions() -> None:
    response = client.get("/api/v1/live-demo/manifest")

    body = response.json()
    assert response.status_code == 200
    assert body["product_name"] == "Demeo"
    assert {page["page_id"] for page in body["pages"]} >= {
        "setup",
        "knowledge",
        "flow",
        "live_room",
        "summary",
    }
    assert body["pages"][0]["elements"][0]["selector"].startswith("[data-demo-id=")


def test_live_demo_session_message_returns_reply_and_visual_events() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/live-demo/sessions/{session['id']}/message",
        json={
            "message": "Can you show me what the founder needs to provide?",
            "current_page_id": "setup",
            "visible_element_ids": ["product-url", "persona-card"],
        },
    )

    body = response.json()
    event_types = [event["type"] for event in body["events"]]
    assert response.status_code == 200
    assert body["reply"].startswith("The founder starts")
    assert body["session"]["current_page_id"] == "setup"
    assert "say" in event_types
    assert "cursor.move" in event_types
    assert "highlight.show" in event_types
    assert body["events"][1]["type"] == "navigate"
    assert body["session"]["lead_profile"]["use_case"] == "creating an agent-led product demo"


def test_agent_adapts_to_voice_question() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/live-demo/sessions/{session['id']}/message",
        json={"message": "Can this use Gemini realtime voice?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["session"]["current_page_id"] == "live_room"
    assert any(event["element_id"] == "voice-control" for event in body["events"])
    assert "Gemini Live" in body["reply"]


def test_agent_can_show_qualification_output() -> None:
    session = create_session()

    response = client.post(
        f"/api/v1/live-demo/sessions/{session['id']}/message",
        json={"message": "How does it qualify the lead and create CRM follow up?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["session"]["current_page_id"] == "summary"
    assert body["session"]["lead_profile"]["score"] == 82
    assert any(event["type"] == "lead.profile.updated" for event in body["events"])


def test_unknown_session_returns_404() -> None:
    response = client.post(
        "/api/v1/live-demo/sessions/lds_missing/message",
        json={"message": "Hello"},
    )

    assert response.status_code == 404
