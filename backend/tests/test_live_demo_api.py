from fastapi.testclient import TestClient

from app.live_demo.setup_store import live_demo_setup_store
from app.live_demo.store import live_demo_session_store
from app.main import create_app


client = TestClient(create_app())


def setup_function() -> None:
    live_demo_session_store.clear()
    live_demo_setup_store.clear()


def get_manifest() -> dict:
    response = client.get("/api/v1/live-demo/manifest")
    assert response.status_code == 200
    return response.json()


def create_session() -> dict:
    response = client.post("/api/v1/live-demo/sessions", json={})
    assert response.status_code == 200
    return response.json()


def test_manifest_exposes_extracted_pages_and_actions() -> None:
    body = get_manifest()

    page_ids = {page["page_id"] for page in body["pages"]}
    assert body["startup_id"] == "demeo_current_app"
    assert body["product_name"] == "Demeo"
    assert page_ids >= {"home", "onboarding", "demo", "crm"}
    assert all(page["route"].startswith("/") for page in body["pages"])
    assert any(
        action["type"] == "navigate"
        for page in body["pages"]
        for action in page["allowed_actions"]
    )
    assert any(
        action["type"] == "highlight"
        for page in body["pages"]
        for action in page["allowed_actions"]
    )


def test_live_demo_session_defaults_to_first_extracted_page() -> None:
    manifest = get_manifest()
    session = create_session()

    assert session["startup_id"] == manifest["startup_id"]
    assert session["current_page_id"] == manifest["pages"][0]["page_id"]


def test_founder_setup_creates_approved_manifest() -> None:
    response = client.post(
        "/api/v1/live-demo/setups",
        json={
            "startup_id": "local_founder_demo",
            "source": "cached_extraction",
            "approve": True,
            "founder_input": {
                "product_name": "Demeo",
                "product_description": "AI demo rooms for founders",
                "product_url": "http://127.0.0.1:5175",
                "target_customer": "B2B founders",
                "prospect_description": "founder evaluating Demeo",
                "demo_goals": ["show setup", "show demo room", "show follow-up"],
                "founder_walkthrough": "Show setup, demo room, then CRM follow-up.",
                "approved_qa": [
                    {
                        "question": "Can this support voice?",
                        "answer": "Yes, voice calls the same safe demo tools.",
                    }
                ],
                "cta": "book onboarding",
                "qualification_questions": ["Who is your buyer?"],
            },
        },
    )

    assert response.status_code == 200
    setup = response.json()
    assert setup["startup_id"] == "local_founder_demo"
    assert setup["status"] == "approved"
    assert setup["manifest"]["startup_id"] == "local_founder_demo"

    manifest = client.get("/api/v1/live-demo/manifest?startup_id=local_founder_demo")
    assert manifest.status_code == 200
    assert manifest.json()["startup_id"] == "local_founder_demo"


def test_live_demo_session_message_returns_valid_visual_events() -> None:
    manifest = get_manifest()
    known_pages = {page["page_id"] for page in manifest["pages"]}
    known_elements = {
        element["id"] for page in manifest["pages"] for element in page["elements"]
    }
    session = create_session()

    response = client.post(
        f"/api/v1/live-demo/sessions/{session['id']}/message",
        json={
            "message": "Can you show me what the founder needs to provide?",
            "current_page_id": session["current_page_id"],
            "visible_element_ids": [],
        },
    )

    body = response.json()
    assert response.status_code == 200
    assert body["reply"]
    assert body["session"]["current_page_id"] in known_pages
    assert any(event["type"] == "say" for event in body["events"])
    assert any(event["type"] == "navigate" for event in body["events"])
    assert all(
        event.get("page_id") in known_pages
        for event in body["events"]
        if event.get("page_id") is not None
    )
    assert all(
        event.get("element_id") in known_elements
        for event in body["events"]
        if event.get("element_id") is not None
    )


def test_rejects_unknown_startup_or_page() -> None:
    bad_startup = client.post(
        "/api/v1/live-demo/sessions",
        json={"startup_id": "missing"},
    )
    bad_page = client.post(
        "/api/v1/live-demo/sessions",
        json={"current_page_id": "missing"},
    )

    assert bad_startup.status_code == 404
    assert bad_page.status_code == 400


def test_unknown_session_returns_404() -> None:
    response = client.post(
        "/api/v1/live-demo/sessions/lds_missing/message",
        json={"message": "Hello"},
    )

    assert response.status_code == 404
