"""Extract reusable company context from chat conversations."""
from __future__ import annotations

import logging

from app.company.context_store import ChatInsight, add_chat_insight

logger = logging.getLogger(__name__)

# Keywords/phrases that suggest the user is sharing useful company info
_SIGNAL_PATTERNS = [
    "we use", "we have", "our team", "our product", "our company",
    "we offer", "we sell", "we provide", "our customers", "our users",
    "our budget", "our revenue", "we plan", "we are", "we're",
    "our goal", "our mission", "our vision", "we built", "we launched",
    "our stack", "we deploy", "our pricing", "we charge",
    "our competitors", "we target", "our market", "we operate",
    "our policy", "our terms", "we comply", "our jurisdiction",
    "employees", "headcount", "founded", "raised", "funding",
]


def _looks_like_company_info(text: str) -> bool:
    lower = text.lower()
    matches = sum(1 for p in _SIGNAL_PATTERNS if p in lower)
    return matches >= 1 and len(text) > 30


def extract_insights_from_messages(
    messages: list[dict[str, str]],
    source_agent: str,
) -> list[ChatInsight]:
    """Extract reusable company facts from the last user message only.

    Only processes the most recent user message to avoid duplicates, since
    the frontend sends the full conversation history on each request.
    """
    # Find the last user message
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            last_user_idx = i
            break

    if last_user_idx < 0:
        return []

    content = messages[last_user_idx].get("content", "")
    if not _looks_like_company_info(content):
        return []

    # Get the preceding assistant question if available
    raw_question = ""
    if last_user_idx > 0 and messages[last_user_idx - 1].get("role") == "assistant":
        raw_question = messages[last_user_idx - 1].get("content", "")[:300]

    fact = content[:500]

    insight = ChatInsight(
        source_agent=source_agent,
        fact=fact,
        raw_question=raw_question,
        raw_answer=content[:500],
    )
    add_chat_insight(insight)
    return [insight]
