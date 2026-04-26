from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks

from app.agents.llm import get_llm_provider
from app.agents.models import MarketingResearchRequest, MarketingResearchResponse
from app.company.chat_extractor import extract_insights_from_messages
from app.company.storage import get_company_context

router = APIRouter(prefix="/marketing-research", tags=["marketing-research"])


@router.post("/chat", response_model=MarketingResearchResponse)
def marketing_research_chat(
    request: MarketingResearchRequest,
    background_tasks: BackgroundTasks,
) -> MarketingResearchResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    background_tasks.add_task(
        extract_insights_from_messages,
        msg_dicts,
        "marketing_research",
        company_context,
    )

    return llm.chat_marketing_research(
        messages=request.messages,
        company_context=company_context,
        workflow=request.workflow,
    )
