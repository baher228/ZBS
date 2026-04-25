from __future__ import annotations

from app.agents.legal_knowledge import LegalKnowledgeBase
from app.agents.llm import LLMProvider
from app.agents.models import AgentCapability, AgentRequest, AgentResponse, LegalIssueScan


class LegalAgent:
    capability = AgentCapability.LEGAL

    def __init__(
        self,
        knowledge_base: LegalKnowledgeBase | None = None,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base or LegalKnowledgeBase()
        self.llm_provider = llm_provider

    def run(self, request: AgentRequest) -> AgentResponse:
        kb = LegalKnowledgeBase.for_jurisdictions(
            jurisdictions=request.jurisdictions,
            industries=request.industries or None,
        )
        query = " ".join(
            [
                request.prompt,
                request.startup_idea or "",
                request.target_audience or "",
                request.goal or "",
                request.channel or "",
                " ".join(request.context.values()),
            ]
        )
        documents = kb.retrieve(query)
        source_context = "\n\n".join(
            f"[{doc.id}] {doc.title} ({doc.jurisdiction})\n"
            f"URL: {doc.source_url}\n"
            f"Summary: {doc.summary}"
            for doc in documents
        )

        if request.review_mode and request.uploaded_doc_text and self.llm_provider is not None:
            review = self.llm_provider.review_document(
                document_text=request.uploaded_doc_text,
                source_context=source_context,
                jurisdictions=request.jurisdictions,
            )
            return AgentResponse(
                agent=self.capability,
                title="Document Compliance Review",
                output=review.as_output_dict(),
                summary="Reviewed uploaded document against applicable regulations and flagged compliance gaps.",
            )

        extra_context = ""
        if request.uploaded_doc_text:
            extra_context += f"\n\nUploaded document excerpt:\n{request.uploaded_doc_text[:3000]}"
        if request.startup_url:
            extra_context += f"\n\nStartup URL: {request.startup_url}"

        full_source_context = source_context + extra_context

        if self.llm_provider is not None:
            scan = self.llm_provider.generate_legal_scan(request, full_source_context)
        else:
            scan = self._build_fallback_scan(request, query, source_context, documents)

        return AgentResponse(
            agent=self.capability,
            title="Founder Legal Issue Scan",
            output=scan.as_output_dict(),
            summary="Generated a source-grounded legal issue scan with citations and counsel handoff questions.",
        )

    def _build_fallback_scan(
        self,
        request: AgentRequest,
        query: str,
        source_context: str,
        documents: list,
    ) -> LegalIssueScan:
        source_lines = [
            f"{document.title} ({document.jurisdiction}): {document.source_url}"
            for document in documents
        ]
        risk_summary = " ".join(document.summary for document in documents)
        scope = ", ".join(request.jurisdictions) if request.jurisdictions else "US"
        return LegalIssueScan(
            important_notice=(
                "This is educational issue-spotting for founders, not legal advice. "
                "A qualified lawyer should review jurisdiction-specific decisions, filings, contracts, and regulated claims."
            ),
            jurisdiction_scope=(
                f"Jurisdictions in scope: {scope}. "
                "Treat regulated industries, employment, securities, health, finance, "
                "and tax questions as counsel-required."
            ),
            relevant_sources="\n".join(source_lines),
            risk_summary=risk_summary,
            founder_checklist=self._build_checklist(query),
            questions_for_counsel=(
                "1. Which entity structure and state filing path best fits the founders' risk, tax, and fundraising plans?\n"
                "2. Are the landing page, outreach, pricing, endorsements, and claims substantiated and non-deceptive?\n"
                "3. What privacy notice, data-processing, security, and customer-contract terms are needed before launch?\n"
                "4. Are accessibility, industry-specific, international, or employment obligations triggered?"
            ),
            next_steps=(
                "Collect product claims, data flows, customer promises, planned jurisdictions, and launch channels. "
                "Use this packet for a legal review before publishing high-risk claims or collecting customer data."
            ),
        )

    def _build_checklist(self, query: str) -> str:
        lowered = query.lower()
        items = [
            "Confirm the company formation path and founder ownership structure.",
            "List every public marketing claim and attach evidence before launch.",
            "Map what personal data is collected, why it is needed, where it is stored, and who receives it.",
            "Prepare customer-facing terms, privacy notice, and support/contact details before collecting users.",
        ]
        if any(term in lowered for term in ("review", "testimonial", "influencer", "affiliate")):
            items.append("Document review, testimonial, influencer, and affiliate disclosure practices.")
        if any(term in lowered for term in ("website", "web", "landing", "app")):
            items.append("Run an accessibility pass on core website and app flows.")
        if any(term in lowered for term in ("gdpr", "eu", "european")):
            items.append("Assess GDPR obligations: lawful basis, DPA, DPIA, and data subject rights workflows.")
        if any(term in lowered for term in ("ccpa", "california", "cpra")):
            items.append("Assess CCPA/CPRA obligations: privacy notice, opt-out, deletion, and data sale disclosures.")
        if any(term in lowered for term in ("email", "newsletter", "outreach")):
            items.append("Confirm CAN-SPAM compliance: opt-out, headers, physical address, ad identification.")
        if any(term in lowered for term in ("fintech", "payment", "money", "banking")):
            items.append("Evaluate money transmission, AML/KYC, and PCI DSS compliance requirements.")
        if any(term in lowered for term in ("health", "medical", "hipaa", "patient")):
            items.append("Evaluate HIPAA obligations and FDA digital health guidance if applicable.")
        if any(term in lowered for term in ("education", "student", "school", "children", "kids")):
            items.append("Evaluate FERPA/COPPA compliance for student/child data handling.")
        return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
