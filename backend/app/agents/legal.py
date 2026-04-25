from __future__ import annotations

from app.agents.legal_knowledge import LegalKnowledgeBase
from app.agents.models import AgentCapability, AgentRequest, AgentResponse, LegalIssueScan


class LegalAgent:
    capability = AgentCapability.LEGAL

    def __init__(self, knowledge_base: LegalKnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or LegalKnowledgeBase()

    def run(self, request: AgentRequest) -> AgentResponse:
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
        documents = self.knowledge_base.retrieve(query)
        source_lines = [
            f"{document.title} ({document.jurisdiction}): {document.source_url}"
            for document in documents
        ]
        risk_summary = " ".join(document.summary for document in documents)
        scan = LegalIssueScan(
            important_notice=(
                "This is educational issue-spotting for founders, not legal advice. "
                "A qualified lawyer should review jurisdiction-specific decisions, filings, contracts, and regulated claims."
            ),
            jurisdiction_scope=(
                "Seed sources are currently United States-focused. Treat non-US launches, regulated industries, "
                "employment, securities, health, finance, and tax questions as counsel-required."
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
        return AgentResponse(
            agent=self.capability,
            title="Founder Legal Issue Scan",
            output=scan.as_output_dict(),
            summary="Generated a source-grounded legal issue scan with citations and counsel handoff questions.",
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
        return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))
