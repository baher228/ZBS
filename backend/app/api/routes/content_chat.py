from __future__ import annotations

from fastapi import APIRouter

from app.agents.llm import get_llm_provider
from app.agents.models import ContentChatRequest, ContentChatResponse
from app.company.storage import get_company_context

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/chat", response_model=ContentChatResponse)
def content_chat(request: ContentChatRequest) -> ContentChatResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    return llm.chat_content(
        messages=request.messages,
        company_context=company_context,
    )
