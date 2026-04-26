"""API routes for company context enrichment (website parsing + chat insights)."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.company.context_store import (
    ChatContext,
    ChatInsight,
    WebsiteContext,
    add_chat_insight,
    delete_chat_context,
    delete_website_context,
    get_enriched_context,
    load_chat_context,
    load_website_context,
    save_website_context,
)
from app.company.storage import load_profile
from app.company.website_parser import parse_website

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company/context", tags=["context"])


# ── Request/Response models ─────────────────────────────────


class ParseWebsiteRequest(BaseModel):
    url: str | None = None  # if None, uses the profile's website field


class ParseWebsiteResponse(BaseModel):
    status: str
    pages_parsed: int
    source_url: str
    company_summary: str = ""


class EnrichedContextResponse(BaseModel):
    website_context: WebsiteContext | None = None
    chat_context: ChatContext = Field(default_factory=ChatContext)
    combined_text: str = ""


class AddInsightRequest(BaseModel):
    source_agent: str
    fact: str
    raw_question: str = ""
    raw_answer: str = ""


# ── Endpoints ───────────────────────────────────────────────


@router.post("/parse-website", response_model=ParseWebsiteResponse)
async def parse_company_website(request: ParseWebsiteRequest) -> ParseWebsiteResponse:
    url = request.url
    if not url:
        profile = load_profile()
        if profile is None or not profile.website:
            raise HTTPException(
                status_code=400,
                detail="No URL provided and no website in company profile.",
            )
        url = profile.website

    try:
        ctx = await parse_website(url)
    except Exception as exc:
        logger.exception("Website parsing failed for %s", url)
        raise HTTPException(status_code=502, detail=f"Failed to parse website: {exc}") from exc

    save_website_context(ctx)

    return ParseWebsiteResponse(
        status="ok",
        pages_parsed=len(ctx.pages),
        source_url=ctx.source_url,
        company_summary=ctx.company_summary[:500],
    )


@router.get("", response_model=EnrichedContextResponse)
def get_context() -> EnrichedContextResponse:
    return EnrichedContextResponse(
        website_context=load_website_context(),
        chat_context=load_chat_context(),
        combined_text=get_enriched_context(),
    )


@router.post("/insight", response_model=ChatContext)
def add_insight(request: AddInsightRequest) -> ChatContext:
    insight = ChatInsight(
        source_agent=request.source_agent,
        fact=request.fact,
        raw_question=request.raw_question,
        raw_answer=request.raw_answer,
    )
    return add_chat_insight(insight)


@router.delete("")
def clear_context() -> dict[str, bool]:
    w = delete_website_context()
    c = delete_chat_context()
    return {"website_deleted": w, "chat_deleted": c}
