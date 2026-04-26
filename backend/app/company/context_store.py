"""Persistent storage for enriched company context (website data + chat insights)."""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import BACKEND_ROOT

logger = logging.getLogger(__name__)

DATA_DIR = BACKEND_ROOT / "data"
WEBSITE_CONTEXT_JSON = DATA_DIR / "website_context.json"
CHAT_CONTEXT_JSON = DATA_DIR / "chat_context.json"

_chat_lock = threading.Lock()


# ── Models ──────────────────────────────────────────────────


class WebsitePageData(BaseModel):
    url: str
    title: str = ""
    page_type: str = ""  # e.g. "homepage", "about", "pricing", "legal"
    content_summary: str = ""
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WebsiteContext(BaseModel):
    source_url: str
    pages: list[WebsitePageData] = Field(default_factory=list)
    company_summary: str = ""
    products_and_services: str = ""
    pricing_info: str = ""
    team_info: str = ""
    legal_info: str = ""
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatInsight(BaseModel):
    source_agent: str  # "legal", "content", "marketing_research"
    fact: str
    raw_question: str = ""
    raw_answer: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatContext(BaseModel):
    insights: list[ChatInsight] = Field(default_factory=list)


# ── Website Context Storage ─────────────────────────────────


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_website_context(ctx: WebsiteContext) -> Path:
    _ensure_data_dir()
    WEBSITE_CONTEXT_JSON.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")
    logger.info("Website context saved for %s (%d pages)", ctx.source_url, len(ctx.pages))
    return WEBSITE_CONTEXT_JSON


def load_website_context() -> WebsiteContext | None:
    if not WEBSITE_CONTEXT_JSON.exists():
        return None
    try:
        raw = WEBSITE_CONTEXT_JSON.read_text(encoding="utf-8")
        return WebsiteContext.model_validate(json.loads(raw))
    except Exception:
        logger.exception("Failed to load website context")
        return None


def delete_website_context() -> bool:
    if WEBSITE_CONTEXT_JSON.exists():
        WEBSITE_CONTEXT_JSON.unlink()
        return True
    return False


# ── Chat Context Storage ────────────────────────────────────


def load_chat_context() -> ChatContext:
    if not CHAT_CONTEXT_JSON.exists():
        return ChatContext()
    try:
        raw = CHAT_CONTEXT_JSON.read_text(encoding="utf-8")
        return ChatContext.model_validate(json.loads(raw))
    except Exception:
        logger.exception("Failed to load chat context")
        return ChatContext()


def save_chat_context(ctx: ChatContext) -> Path:
    _ensure_data_dir()
    CHAT_CONTEXT_JSON.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")
    return CHAT_CONTEXT_JSON


def add_chat_insight(insight: ChatInsight) -> ChatContext:
    with _chat_lock:
        ctx = load_chat_context()
        ctx.insights.append(insight)
        # Keep last 200 insights to avoid unbounded growth
        if len(ctx.insights) > 200:
            ctx.insights = ctx.insights[-200:]
        save_chat_context(ctx)
    logger.info("Chat insight added from %s", insight.source_agent)
    return ctx


def delete_chat_context() -> bool:
    if CHAT_CONTEXT_JSON.exists():
        CHAT_CONTEXT_JSON.unlink()
        return True
    return False


# ── Enriched Context Builder ────────────────────────────────


def get_enriched_context() -> str:
    """Build a combined context string from website data + chat insights.

    Returns empty string if no enriched data exists.
    """
    parts: list[str] = []

    website = load_website_context()
    if website:
        lines = ["--- Website Context ---"]
        if website.company_summary:
            lines.append(f"Summary: {website.company_summary}")
        if website.products_and_services:
            lines.append(f"Products/Services: {website.products_and_services}")
        if website.pricing_info:
            lines.append(f"Pricing: {website.pricing_info}")
        if website.team_info:
            lines.append(f"Team: {website.team_info}")
        if website.legal_info:
            lines.append(f"Legal pages: {website.legal_info}")
        for page in website.pages:
            if page.content_summary:
                lines.append(f"[{page.page_type or 'page'}] {page.url}: {page.content_summary}")
        parts.append("\n".join(lines))

    chat = load_chat_context()
    if chat.insights:
        lines = ["--- Stored Context from Previous Conversations ---"]
        for ins in chat.insights[-50:]:  # last 50 for prompt budget
            lines.append(f"• [{ins.source_agent}] {ins.fact}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)
