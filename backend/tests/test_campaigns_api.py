from fastapi.testclient import TestClient

from app.api.routes.campaigns import (
    get_campaign_graph_runner,
    get_demo_chat_graph_runner,
    get_qualification_graph_runner,
)
from app.agents.store import campaign_store
from app.main import create_app


client = TestClient(create_app())


def setup_function() -> None:
    campaign_store.clear()
    get_campaign_graph_runner.cache_clear()
    get_demo_chat_graph_runner.cache_clear()
    get_qualification_graph_runner.cache_clear()


def create_campaign() -> dict:
    response = client.post(
        "/api/v1/campaigns",
        json={
            "product_name": "DemoRoom AI",
            "product_description": (
                "AI demo rooms for technical B2B founders that turn cold outreach "
                "into qualified sales conversations."
            ),
            "target_audience": "technical B2B founders",
            "prospect_company": "Pydantic",
            "prospect_description": "Python data validation and agent reliability tooling company.",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_create_campaign_returns_demo_room_package() -> None:
    body = create_campaign()

    assert body["campaign_id"].startswith("camp_")
    assert body["product_profile"]["name"] == "DemoRoom AI"
    assert body["prospect_profile"]["company_name"] == "Pydantic"
    assert body["demo_room"]["id"].startswith("room_")
    assert body["readiness_score"]["verdict"] == "ready"
    assert len(body["workflow_steps"]) == 7


def test_get_demo_room_by_id() -> None:
    campaign = create_campaign()
    demo_room_id = campaign["demo_room"]["id"]

    response = client.get(f"/api/v1/demo-rooms/{demo_room_id}")

    assert response.status_code == 200
    assert response.json()["id"] == demo_room_id
    assert response.json()["prospect_company"] == "Pydantic"


def test_demo_room_chat_appends_transcript() -> None:
    campaign = create_campaign()
    demo_room_id = campaign["demo_room"]["id"]

    response = client.post(
        f"/api/v1/demo-rooms/{demo_room_id}/chat",
        json={"message": "How would this work for our developer tooling workflow?"},
    )

    body = response.json()
    assert response.status_code == 200
    assert body["demo_room_id"] == demo_room_id
    assert "demo room" in body["reply"].lower() or "context" in body["reply"].lower()
    assert [message["role"] for message in body["transcript"]] == ["user", "assistant"]


def test_qualification_rejects_empty_transcript() -> None:
    campaign = create_campaign()
    demo_room_id = campaign["demo_room"]["id"]

    response = client.post(f"/api/v1/demo-rooms/{demo_room_id}/qualify")

    assert response.status_code == 400
    assert "before the prospect has chatted" in response.json()["detail"]


def test_qualification_uses_transcript_and_returns_sales_ops_output() -> None:
    campaign = create_campaign()
    demo_room_id = campaign["demo_room"]["id"]
    client.post(
        f"/api/v1/demo-rooms/{demo_room_id}/chat",
        json={"message": "How does it work, and what does pricing look like?"},
    )

    response = client.post(f"/api/v1/demo-rooms/{demo_room_id}/qualify")

    body = response.json()
    assert response.status_code == 200
    assert body["demo_room_id"] == demo_room_id
    assert body["lead_score"] >= 80
    assert body["qualification_status"] == "qualified"
    assert body["crm_note"]
    assert body["follow_up_email"]["subject"]


def test_campaign_validation_rejects_short_product_description() -> None:
    response = client.post(
        "/api/v1/campaigns",
        json={
            "product_name": "DemoRoom AI",
            "product_description": "Too short",
            "prospect_company": "Pydantic",
        },
    )

    assert response.status_code == 422


def test_missing_demo_room_returns_404() -> None:
    response = client.get("/api/v1/demo-rooms/room_missing")

    assert response.status_code == 404

