"""Tests for the content chat endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.agents.llm import _normalize_content_chat_response
from app.agents.models import ContentChatResponse
from app.api.routes.content_chat import _add_content_visuals
from app.main import app

client = TestClient(app)


def test_content_chat_basic():
    """Basic content chat request."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "user", "content": "I need landing page copy for my SaaS product"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert isinstance(data["follow_up_questions"], list)
    assert isinstance(data["content_ready"], bool)
    assert "generated_content" in data


def test_content_chat_multi_turn():
    """Multi-turn content conversation."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [
                {"role": "user", "content": "I need a launch email"},
                {"role": "assistant", "content": "I can help with that. What's your product about?"},
                {"role": "user", "content": "It's a project management tool for remote teams"},
            ],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["reply"]) > 0
    assert isinstance(data["follow_up_questions"], list)


def test_content_chat_empty_messages_rejected():
    """Empty messages list should be rejected."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [],
        },
    )
    assert response.status_code == 422


def test_content_chat_response_structure():
    """Verify the full response structure."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "user", "content": "Create a social media post about our beta launch"}],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"reply", "follow_up_questions", "content_ready", "generated_content"}


def test_content_chat_invalid_role_rejected():
    """Invalid message role should be rejected."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "system", "content": "You are helpful"}],
        },
    )
    assert response.status_code == 422


def test_content_chat_empty_content_rejected():
    """Empty message content should be rejected."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "user", "content": ""}],
        },
    )
    assert response.status_code == 422


def test_content_chat_with_workflow():
    """Content chat with workflow parameter."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "user", "content": "Write a LinkedIn post about our launch"}],
            "workflow": "social_post",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "content_ready" in data
    assert "generated_content" in data


def test_content_chat_followups_are_single_structured_ask():
    """Follow-up responses should be capped and rendered in one assistant message."""
    response = _normalize_content_chat_response(
        ContentChatResponse(
            reply="I have several questions.",
            follow_up_questions=[
                "Product name and one-line description.",
                "Target audience and main pain point.",
                "Primary call to action and link.",
                "Launch date or timing.",
                "Brand voice.",
            ],
            content_ready=True,
            generated_content={"draft": "placeholder"},
        )
    )

    assert response.content_ready is False
    assert response.generated_content is None
    assert len(response.follow_up_questions) == 4
    assert response.reply.startswith("I need these exact details before I write it:")
    assert "- Product name and one-line description." in response.reply
    assert "5." not in response.reply


def test_content_chat_embedded_json_reply_is_unpacked():
    response = _normalize_content_chat_response(
        ContentChatResponse(
            reply=(
                '{"content_ready":true,"generated_content":{"linkedin_post_launch":"Launch post"},'
                '"follow_up_questions":[]}'
            ),
            follow_up_questions=[],
            content_ready=False,
            generated_content=None,
        )
    )

    assert response.reply == "I drafted the content below."
    assert response.content_ready is True
    assert response.generated_content == {"linkedin_post_launch": "Launch post"}


def test_content_chat_adds_image_directions_when_images_unavailable(monkeypatch):
    monkeypatch.setattr("app.api.routes.content_chat.generate_content_images", lambda *args, **kwargs: {})
    response = _add_content_visuals(
        ContentChatResponse(
            reply="Done",
            follow_up_questions=[],
            content_ready=True,
            generated_content={"linkedin_post_launch": "Apterro launches tomorrow."},
        ),
        company_context="",
        workflow="social_post",
    )

    assert response.generated_content is not None
    assert "image_directions" in response.generated_content
    assert "Linkedin Post Launch" in response.generated_content["image_directions"]


def test_content_chat_with_unknown_workflow():
    """Content chat with unknown workflow still works."""
    response = client.post(
        "/api/v1/content/chat",
        json={
            "messages": [{"role": "user", "content": "Help me create content"}],
            "workflow": "unknown_workflow",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
