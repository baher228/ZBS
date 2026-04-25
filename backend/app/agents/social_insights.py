"""Extract tone, themes, and audience insights from company social media profiles."""

from __future__ import annotations

import logging
import re

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0


class SocialInsights(BaseModel):
    tone: str = Field(default="", description="Dominant tone/voice")
    themes: list[str] = Field(default_factory=list, description="Recurring content themes")
    audience_signals: str = Field(default="", description="Who the content speaks to")
    content_style: str = Field(default="", description="Style patterns (long-form, punchy, etc.)")
    raw_snippets: list[str] = Field(default_factory=list, description="Sample text from profiles")

    def to_context_block(self) -> str:
        if not self.tone and not self.themes:
            return ""
        lines = ["Social media analysis of the company's existing presence:"]
        if self.tone:
            lines.append(f"- Voice/tone: {self.tone}")
        if self.themes:
            lines.append(f"- Key themes: {', '.join(self.themes)}")
        if self.audience_signals:
            lines.append(f"- Audience: {self.audience_signals}")
        if self.content_style:
            lines.append(f"- Style: {self.content_style}")
        return "\n".join(lines)


def _clean_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]


def _fetch_page_text(url: str) -> str:
    try:
        with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
            resp = client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; ZBS-GTM-Bot/1.0)",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
            resp.raise_for_status()
            return _clean_html(resp.text)
    except Exception:
        logger.warning("Failed to fetch %s", url, exc_info=True)
        return ""


def _extract_snippets(text: str, max_snippets: int = 10) -> list[str]:
    sentences = re.split(r"[.!?]+", text)
    snippets: list[str] = []
    for s in sentences:
        s = s.strip()
        if len(s) > 30 and len(s) < 500:
            snippets.append(s)
        if len(snippets) >= max_snippets:
            break
    return snippets


def extract_social_insights(
    social_links: dict[str, str],
    company_context: str = "",
) -> SocialInsights:
    """Fetch social media pages and use LLM to extract insights."""
    all_snippets: list[str] = []
    fetched_platforms: list[str] = []

    for platform, url in social_links.items():
        if not url or not url.startswith("http"):
            continue
        text = _fetch_page_text(url)
        if text:
            snippets = _extract_snippets(text)
            all_snippets.extend(snippets)
            fetched_platforms.append(platform)

    if not all_snippets:
        return SocialInsights()

    try:
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.pydantic_ai_api_key,
            base_url="https://ai.pydantic.dev/openai/v1",
            max_tokens=800,
            temperature=0.3,
        )

        snippet_text = "\n".join(f"- {s}" for s in all_snippets[:15])
        prompt = (
            "Analyze these snippets from a company's social media profiles "
            f"(platforms: {', '.join(fetched_platforms)}).\n\n"
            f"Snippets:\n{snippet_text}\n\n"
            f"Company context: {company_context[:500]}\n\n"
            "Return a JSON object with these fields:\n"
            '- "tone": dominant voice/tone in 2-4 words (e.g., "professional and authoritative")\n'
            '- "themes": list of 3-5 recurring content themes\n'
            '- "audience_signals": who the content speaks to (1-2 sentences)\n'
            '- "content_style": style patterns in 1-2 sentences\n'
            "Return ONLY the JSON object, no markdown fences."
        )

        result = model.invoke([("human", prompt)])
        content = result.content if hasattr(result, "content") else str(result)

        import json
        data = json.loads(content)

        return SocialInsights(
            tone=data.get("tone", ""),
            themes=data.get("themes", []),
            audience_signals=data.get("audience_signals", ""),
            content_style=data.get("content_style", ""),
            raw_snippets=all_snippets[:10],
        )

    except Exception:
        logger.exception("LLM social insight extraction failed")
        return SocialInsights(raw_snippets=all_snippets[:10])
