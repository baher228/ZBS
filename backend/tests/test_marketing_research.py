"""Tests for the marketing research chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_marketing_research_basic():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [{"role": "user", "content": "Analyze our top competitors in the AI sales space"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert isinstance(data["follow_up_questions"], list)
    assert isinstance(data["research_ready"], bool)
    assert "research_data" in data


def test_marketing_research_multi_turn():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [
                {"role": "user", "content": "What's our TAM?"},
                {"role": "assistant", "content": "I can estimate that. What industry are you in?"},
                {"role": "user", "content": "B2B SaaS for sales teams"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["reply"]) > 0


def test_marketing_research_empty_messages_rejected():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={"messages": []},
    )
    assert response.status_code == 422


def test_marketing_research_response_structure():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [{"role": "user", "content": "Map our customer segments"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"reply", "follow_up_questions", "research_ready", "research_data"}


def test_marketing_research_invalid_role_rejected():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [{"role": "system", "content": "You are helpful"}],
        },
    )
    assert response.status_code == 422


def test_marketing_research_with_workflow():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [{"role": "user", "content": "Analyze our competitors"}],
            "workflow": "competitor_analysis",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["research_ready"] is True
    assert data["research_data"] is not None


def test_marketing_research_with_unknown_workflow():
    response = client.post(
        "/api/v1/marketing-research/chat",
        json={
            "messages": [{"role": "user", "content": "Help me research my market"}],
            "workflow": "unknown_workflow",
        },
    )
    assert response.status_code == 200
    assert "reply" in response.json()
