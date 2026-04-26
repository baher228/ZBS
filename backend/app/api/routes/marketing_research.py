from __future__ import annotations

from fastapi import APIRouter

from app.agents.llm import get_llm_provider
from app.agents.models import MarketingResearchRequest, MarketingResearchResponse
from app.company.storage import get_company_context

router = APIRouter(prefix="/marketing-research", tags=["marketing-research"])


@router.post("/chat", response_model=MarketingResearchResponse)
def marketing_research_chat(request: MarketingResearchRequest) -> MarketingResearchResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    return llm.chat_marketing_research(
        messages=request.messages,
        company_context=company_context,
        workflow=request.workflow,
    )
