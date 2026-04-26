"""Tests for the marketing research chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.agents.llm import _normalize_marketing_research_response
from app.agents.models import MarketingResearchResponse
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


def test_competitor_analysis_embedded_json_is_cleaned():
    response = _normalize_marketing_research_response(
        MarketingResearchResponse(
            reply=(
                "Below is a UK-focused competitor view.\n\n"
                "research_ready=true\n"
                '{"research_ready": true}\n'
                "research_data\n"
                '{"competitor_analysis":{"summary":"Apterro competes with prep providers.",'
                '"key_trends":["Role-specific prep","Recent-hire intel"]},'
                '"competitor_matrix":"| Competitor | Positioning | Opportunity |\\n'
                '|---|---|---|\\n| Leland | Coaching marketplace | UK finance focus |",'
                '"positioning_opportunities":{"recommended_positioning_statement":"Own recent-hire UK finance mentorship."}}\n'
                "competitor analysis\n"
                "/** see embedded JSON above for full competitor_analysis object **/"
            ),
            follow_up_questions=["What roles are in scope?"],
            research_ready=True,
            research_data={
                "competitor_analysis": "/** see embedded JSON above for full competitor_analysis object **/",
                "competitor_matrix": "/** see embedded JSON above for full markdown table **/",
            },
        )
    )

    assert response.reply == "Below is a UK-focused competitor view."
    assert response.research_data is not None
    assert "see embedded JSON" not in response.research_data["competitor_analysis"]
    assert "### Key Trends" in response.research_data["competitor_analysis"]
    assert response.research_data["competitor_matrix"].startswith("| Competitor |")
    assert "Own recent-hire" in response.research_data["positioning_opportunities"]
