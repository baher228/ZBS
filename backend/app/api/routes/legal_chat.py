from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.legal_knowledge import LegalKnowledgeBase
from app.agents.llm import get_llm_provider
from app.agents.models import LegalChatRequest, LegalChatResponse, LegalOverviewResponse
from app.company.chat_extractor import extract_insights_from_messages
from app.company.storage import get_company_context

router = APIRouter(prefix="/legal", tags=["legal"])


def _get_source_context(query: str, jurisdictions: list[str]) -> str:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=jurisdictions)
    documents = kb.retrieve(query)
    return "\n\n".join(
        f"[{doc.id}] {doc.title} ({doc.jurisdiction})\n"
        f"URL: {doc.source_url}\n"
        f"Summary: {doc.summary}"
        for doc in documents
    )


@router.post("/chat", response_model=LegalChatResponse)
def legal_chat(request: LegalChatRequest) -> LegalChatResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""

    last_user_msg = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    source_context = _get_source_context(last_user_msg, request.jurisdictions)

    # Extract useful context from user messages
    msg_dicts = [{"role": m.role, "content": m.content} for m in request.messages]
    extract_insights_from_messages(msg_dicts, source_agent="legal")

    try:
        return llm.chat_legal(
            messages=request.messages,
            mode=request.mode,
            source_context=source_context,
            company_context=company_context,
            document_type=request.document_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Legal chat generation failed: {exc.__class__.__name__}",
        ) from exc


@router.get("/overview", response_model=LegalOverviewResponse)
def legal_overview() -> LegalOverviewResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""
    source_context = _get_source_context("startup legal compliance overview", ["US"])
    try:
        return llm.generate_legal_overview(company_context, source_context)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Legal overview generation failed: {exc.__class__.__name__}",
        ) from exc
