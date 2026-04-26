"""Tests for the legal chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

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
