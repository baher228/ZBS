from fastapi.testclient import TestClient

from app.main import create_app


client = TestClient(create_app())


def test_root_and_health_routes_still_work() -> None:
    root = client.get("/")
    health = client.get("/api/v1/health")

    assert root.status_code == 200
    assert root.json()["name"] == "ZBS API"
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}


def test_create_task_returns_agent_review_and_decision() -> None:
    response = client.post(
        "/api/v1/tasks",
        json={
            "prompt": "Create launch email and landing copy",
            "startup_idea": "GTM AI office for founders",
            "target_audience": "first-time founders",
            "goal": "book discovery calls",
            "tone": "practical",
            "channel": "email and landing page",
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["selected_agent"] == "content_generator"
    assert body["agent_response"]["output"]["launch_email"]
    assert body["review"]["status"] == "approved"
    assert body["decision"]["status"] == "completed"
