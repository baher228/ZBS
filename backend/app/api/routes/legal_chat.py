from __future__ import annotations

from fastapi import APIRouter

from app.agents.legal_knowledge import LegalKnowledgeBase
from app.agents.llm import get_llm_provider
from app.agents.models import LegalChatRequest, LegalChatResponse
from app.company.storage import get_company_context

router = APIRouter(prefix="/legal", tags=["legal"])


@router.post("/chat", response_model=LegalChatResponse)
def legal_chat(request: LegalChatRequest) -> LegalChatResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""

    jurisdictions = request.jurisdictions
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=jurisdictions)

    last_user_msg = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            last_user_msg = msg.content
            break

    documents = kb.retrieve(last_user_msg)
    source_context = "\n\n".join(
        f"[{doc.id}] {doc.title} ({doc.jurisdiction})\n"
        f"URL: {doc.source_url}\n"
        f"Summary: {doc.summary}"
        for doc in documents
    )

    return llm.chat_legal(
        messages=request.messages,
        mode=request.mode,
        source_context=source_context,
        company_context=company_context,
        document_type=request.document_type,
    )
