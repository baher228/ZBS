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
    existing_context: str = "",
) -> list[ChatInsight]:
    """Extract reusable company facts from the latest user reply in context.

    Uses recent assistant and user turns to understand short replies, while
    only saving facts from the latest user turn to avoid reprocessing the whole
    chat each time the frontend resends history.

    This is a non-critical side effect — errors are logged but never
    propagated so the primary chat response is not interrupted.
    """
    try:
        return _do_extract(messages, source_agent, existing_context)
    except Exception:
        logger.warning("Failed to extract chat insights", exc_info=True)
        return []


def _do_extract(
    messages: list[dict[str, str]],
    source_agent: str,
    existing_context: str = "",
) -> list[ChatInsight]:
    # Find the last user message
    last_user_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if messages[i].get("role") == "user":
            last_user_idx = i
            break

    if last_user_idx < 0:
        return []

    content = messages[last_user_idx].get("content", "")
    recent_messages = messages[max(0, last_user_idx - 6) : last_user_idx + 1]
    conversation_context = _format_conversation_context(recent_messages)
    extraction_text = f"{conversation_context}\n\nLatest user reply: {content}".strip()

    if not _looks_like_company_info(content) and not _looks_like_company_info(extraction_text):
        return []
    if _already_in_context(content, existing_context) or _already_in_context(extraction_text, existing_context):
        return []

    # Get the preceding assistant question if available
    raw_question = ""
    if last_user_idx > 0 and messages[last_user_idx - 1].get("role") == "assistant":
        raw_question = messages[last_user_idx - 1].get("content", "")[:300]

    fact = _summarize_company_fact(content, raw_question, conversation_context)
    if not fact or _already_in_context(fact, existing_context):
        return []

    insight = ChatInsight(
        source_agent=source_agent,
        fact=fact,
        raw_question=raw_question,
        raw_answer=content[:500],
    )
    add_chat_insight(insight)
    return [insight]


def _already_in_context(text: str, existing_context: str) -> bool:
    if not text.strip() or not existing_context.strip():
        return False

    normalized_text = _normalize_for_compare(text)
    normalized_context = _normalize_for_compare(existing_context)
    if normalized_text in normalized_context:
        return True

    words = [word for word in normalized_text.split() if len(word) > 3]
    if len(words) < 5:
        return False
    overlap = sum(1 for word in set(words) if word in normalized_context)
    return overlap / len(set(words)) >= 0.8


def _normalize_for_compare(text: str) -> str:
    return " ".join(text.lower().split())


def _format_conversation_context(messages: list[dict[str, str]]) -> str:
    lines: list[str] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = " ".join(msg.get("content", "").strip().split())
        if content:
            lines.append(f"{role}: {content[:500]}")
    return "\n".join(lines)


def _summarize_company_fact(content: str, raw_question: str, conversation_context: str = "") -> str:
    cleaned = " ".join(content.strip().split())
    if not cleaned:
        return ""

    llm_summary = _summarize_company_fact_with_llm(cleaned, raw_question, conversation_context)
    if llm_summary:
        return llm_summary

    prefix = ""
    lower_question = raw_question.lower()
    if "jurisdiction" in lower_question or "where" in lower_question:
        prefix = "Company jurisdictions/locations: "
    elif "customer" in lower_question or "audience" in lower_question or "target" in lower_question:
        prefix = "Target customers: "
    elif "pricing" in lower_question or "charge" in lower_question:
        prefix = "Pricing: "
    elif "product" in lower_question or "what does" in lower_question:
        prefix = "Product/company description: "

    if not prefix:
        lowered = cleaned.lower()
        if "pricing" in lowered or "we charge" in lowered:
            prefix = "Pricing: "
        elif "we target" in lowered or "our customers" in lowered or "our users" in lowered:
            prefix = "Target customers: "
        elif "we operate" in lowered or "jurisdiction" in lowered:
            prefix = "Company jurisdictions/locations: "
        elif "our product" in lowered or "we sell" in lowered or "we provide" in lowered:
            prefix = "Product/company description: "
        else:
            prefix = "Company fact: "

    context_hint = _fallback_context_hint(raw_question)
    return f"{prefix}{context_hint}{cleaned[:450]}"


def _fallback_context_hint(raw_question: str) -> str:
    question = raw_question.lower()
    if "where" in question and "operate" in question:
        return "Company operates in "
    if "jurisdiction" in question:
        return "Company jurisdictions include "
    if ("customer" in question or "audience" in question or "target" in question) and "who" in question:
        return "Company targets "
    if "pricing" in question or "charge" in question:
        return "Company pricing is "
    return ""


def _summarize_company_fact_with_llm(content: str, raw_question: str, conversation_context: str = "") -> str:
    try:
        from langchain_openai import ChatOpenAI

        from app.core.config import settings

        api_key = settings.resolved_gateway_api_key or settings.resolved_llm_api_key
        if not api_key:
            return ""

        model = ChatOpenAI(
            model=settings.resolved_llm_model,
            api_key=api_key,
            base_url=settings.resolved_gateway_base_url,
            max_tokens=120,
            temperature=0,
        )
        result = model.invoke(
            [
                (
                    "system",
                    "You extract durable company knowledge from chat replies. "
                    "Return one concise sentence that can be saved to a company knowledge base. "
                    "Keep concrete facts such as product, audience, pricing, jurisdiction, users, team, stack, policy, or compliance posture. "
                    "If the reply contains no durable company fact, return an empty string. "
                    "Do not include advice, legal analysis, or conversational filler.",
                ),
                (
                    "human",
                    f"Recent conversation:\n{conversation_context}\n\nLatest user reply:\n{content}",
                ),
            ]
        )
        summary = result.content if hasattr(result, "content") else str(result)
        return " ".join(str(summary).strip().split())[:500]
    except Exception:
        logger.info("LLM company insight summarization unavailable; using fallback", exc_info=True)
        return ""
