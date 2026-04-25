from fastapi.testclient import TestClient

from app.api.routes.tasks import get_orchestrator
from app.main import create_app


client = TestClient(create_app())


def setup_function() -> None:
    get_orchestrator.cache_clear()


def test_root_and_health_routes_still_work() -> None:
    root = client.get("/")
    health = client.get("/api/v1/health")

    assert root.status_code == 200
    assert root.json()["name"] == "ZBS API"
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_create_content_task_returns_agent_review_and_decision() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "prompt": "Create launch email and landing copy",
            "startup_idea": "GTM AI office for founders",
            "target_audience": "first-time founders",
            "goal": "book discovery calls",
            "tone": "practical",
            "channel": "email and landing page",
            "context": {"task_type": "content"},
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["selected_agent"] == "content_generator"
    assert body["agent_response"]["output"]["launch_email"]
    assert body["review"]["status"] == "approved"
    assert body["decision"]["status"] == "completed"


def test_create_legal_task_returns_citations_and_counsel_questions() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "prompt": "Check legal risks for landing page claims, privacy, testimonials, and LLC formation.",
            "startup_idea": "GTM AI office for founders",
            "target_audience": "US startup founders",
            "goal": "launch a compliant MVP without overclaiming",
            "channel": "website and onboarding",
            "context": {"task_type": "legal"},
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["selected_agent"] == "legal"
    assert "https://www.ftc.gov" in body["agent_response"]["output"]["relevant_sources"]
    assert body["agent_response"]["output"]["questions_for_counsel"]
    assert body["review"]["status"] == "approved"
    assert body["decision"]["status"] == "completed"
