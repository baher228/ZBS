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
    """Scan a conversation for messages that contain reusable company facts.

    Returns a list of ChatInsight objects that were stored.
    """
    stored: list[ChatInsight] = []

    for i, msg in enumerate(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if not _looks_like_company_info(content):
            continue

        # Get the preceding assistant question if available
        raw_question = ""
        if i > 0 and messages[i - 1].get("role") == "assistant":
            raw_question = messages[i - 1].get("content", "")[:300]

        # Build a concise fact from the user message
        fact = content[:500]

        insight = ChatInsight(
            source_agent=source_agent,
            fact=fact,
            raw_question=raw_question,
            raw_answer=content[:500],
        )
        add_chat_insight(insight)
        stored.append(insight)

    return stored
