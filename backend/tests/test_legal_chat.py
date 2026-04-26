"""Tests for the legal chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.agents.llm import MockLLMProvider, ResilientLLMProvider, _normalize_legal_chat_response
from app.agents.models import LegalChatMode, LegalChatResponse
from app.main import app

client = TestClient(app)


def test_legal_chat_basic():
    """Basic legal advice chat."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "What are the legal risks for a SaaS startup?"}],
            "mode": "legal_advice",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["mode"] == "legal_advice"
    assert isinstance(data["follow_up_questions"], list)
    assert isinstance(data["sources_used"], list)


def test_legal_chat_tax_mode():
    """Tax mode chat."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "What tax obligations does a Delaware LLC have?"}],
            "mode": "tax",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "tax"
    assert len(data["reply"]) > 0


def test_legal_chat_document_drafting():
    """Document drafting mode returns a document."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "Draft a Terms of Service for my startup"}],
            "mode": "document_drafting",
            "document_type": "Terms of Service",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "document_drafting"
    assert data["document"] is not None
    assert "document_body" in data["document"]
    assert "important_notice" in data["document"]


def test_legal_chat_multi_turn():
    """Multi-turn conversation sends history."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [
                {"role": "user", "content": "Tell me about GDPR compliance"},
                {"role": "assistant", "content": "GDPR requires..."},
                {"role": "user", "content": "How does this apply to SaaS companies?"},
            ],
            "mode": "legal_advice",
            "jurisdictions": ["EU"],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["reply"]) > 0


def test_legal_chat_custom_jurisdictions():
    """Custom jurisdictions are passed through."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "Privacy requirements?"}],
            "mode": "legal_advice",
            "jurisdictions": ["EU", "UK"],
        },
    )
    assert response.status_code == 200


def test_legal_chat_empty_messages_rejected():
    """Empty messages list should be rejected."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [],
            "mode": "legal_advice",
        },
    )
    assert response.status_code == 422


def test_legal_chat_invalid_mode():
    """Invalid mode should be rejected."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "mode": "invalid_mode",
        },
    )
    assert response.status_code == 422


def test_legal_chat_document_without_type():
    """Document drafting without document_type still works (agent should ask)."""
    response = client.post(
        "/api/v1/legal/chat",
        json={
            "messages": [{"role": "user", "content": "I need a legal document"}],
            "mode": "document_drafting",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "document_drafting"


def test_legal_followups_are_asked_in_reply_not_suggestions():
    """Legal follow-ups should be folded into one assistant message and cleared from chips."""
    response = _normalize_legal_chat_response(
        LegalChatResponse(
            reply="Need more info — before drafting.",
            document=None,
            follow_up_questions=[
                "Role title and responsibilities — include department.",
                "Paid or unpaid internship — include rate and expenses.",
                "Working hours and location.",
                "Start date and end date.",
                "Supervisor name.",
            ],
            mode=LegalChatMode.DOCUMENT_DRAFTING,
            sources_used=["GOV.UK — Employment status"],
        )
    )

    assert response.follow_up_questions == []
    assert response.document is None
    assert "I need these exact details" in response.reply
    assert "- Role title and responsibilities" in response.reply
    assert "5." not in response.reply
    assert "—" not in response.reply
    assert response.sources_used == ["GOV.UK - Employment status"]


def test_legal_chat_does_not_fall_back_to_mock():
    """Legal chat should surface provider failures instead of returning mock legal advice."""

    class FailingLegalProvider(MockLLMProvider):
        def chat_legal(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise TimeoutError("slow legal draft")

    provider = ResilientLLMProvider(FailingLegalProvider(), MockLLMProvider())

    try:
        provider.chat_legal(
            messages=[],
            mode=LegalChatMode.DOCUMENT_DRAFTING,
            source_context="",
            company_context="",
            document_type="Intern Agreement",
        )
    except TimeoutError:
        pass
    else:
        raise AssertionError("Expected legal chat provider failure to be raised")


def test_legal_overview_basic():
    """Legal overview endpoint returns 200 with expected structure."""
    response = client.get("/api/v1/legal/overview")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert len(data["summary"]) > 0
    assert isinstance(data["potential_issues"], list)
    assert isinstance(data["recommended_documents"], list)
    assert isinstance(data["missing_info"], list)
    assert isinstance(data["compliance_areas"], list)


def test_legal_overview_response_structure():
    """Verify the full response structure of legal overview."""
    response = client.get("/api/v1/legal/overview")
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {
        "summary",
        "potential_issues",
        "recommended_documents",
        "missing_info",
        "compliance_areas",
    }


def test_legal_overview_issues_have_severity():
    """Each potential issue should have a severity field."""
    response = client.get("/api/v1/legal/overview")
    assert response.status_code == 200
    data = response.json()
    for issue in data["potential_issues"]:
        assert issue["severity"] in ("high", "medium", "low")
        assert "title" in issue
        assert "description" in issue
        assert "recommendation" in issue
