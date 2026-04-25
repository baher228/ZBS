from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LegalDocument:
    id: str
    title: str
    jurisdiction: str
    source_url: str
    summary: str
    keywords: tuple[str, ...]


LEGAL_DOCUMENTS = [
    LegalDocument(
        id="ftc-advertising-faq",
        title="FTC Advertising FAQ's: A Guide for Small Business",
        jurisdiction="United States",
        source_url="https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business",
        summary=(
            "Advertising claims should be truthful, not misleading, and supported before publication. "
            "Claims about performance, endorsements, pricing, and product benefits need evidence."
        ),
        keywords=("advertising", "marketing", "claims", "copy", "endorsement", "pricing", "truth"),
    ),
    LegalDocument(
        id="ftc-privacy-security",
        title="FTC Privacy and Security Business Guidance",
        jurisdiction="United States",
        source_url="https://www.ftc.gov/business-guidance/privacy-security",
        summary=(
            "Businesses handling consumer data should consider privacy notices, data minimization, "
            "security safeguards, vendor practices, and promises made to customers."
        ),
        keywords=("privacy", "security", "data", "personal", "consumer", "saas", "app"),
    ),
    LegalDocument(
        id="sba-business-structure",
        title="SBA Choose a Business Structure",
        jurisdiction="United States",
        source_url="https://www.sba.gov/business-guide/launch-your-business/choose-business-structure",
        summary=(
            "Business structure affects liability, taxes, filings, and operations. Founders should compare "
            "structures and confirm state-specific requirements before forming."
        ),
        keywords=("formation", "company", "llc", "corporation", "liability", "tax", "structure"),
    ),
    LegalDocument(
        id="ada-web-guidance",
        title="ADA.gov Guidance on Web Accessibility and the ADA",
        jurisdiction="United States",
        source_url="https://www.ada.gov/resources/web-guidance/",
        summary=(
            "Web accessibility can affect access to goods, services, programs, and activities. Existing "
            "technical standards can help teams make websites more accessible."
        ),
        keywords=("accessibility", "ada", "website", "web", "disability", "compliance"),
    ),
    LegalDocument(
        id="ftc-endorsements-reviews",
        title="FTC Endorsements, Influencers, and Reviews",
        jurisdiction="United States",
        source_url="https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews",
        summary=(
            "Endorsements, reviews, testimonials, and influencer content can create legal risk when they "
            "misrepresent experience, hide material connections, or use deceptive review practices."
        ),
        keywords=("reviews", "testimonials", "influencer", "endorsement", "social", "affiliate"),
    ),
]


class LegalKnowledgeBase:
    def __init__(self, documents: list[LegalDocument] | None = None) -> None:
        self.documents = documents or LEGAL_DOCUMENTS

    def retrieve(self, query: str, limit: int = 3) -> list[LegalDocument]:
        query_terms = self._terms(query)
        scored = [
            (self._score(document, query_terms), document)
            for document in self.documents
        ]
        ranked = [document for score, document in sorted(scored, key=lambda item: item[0], reverse=True) if score > 0]
        return (ranked or self.documents[:limit])[:limit]

    def _score(self, document: LegalDocument, query_terms: set[str]) -> int:
        haystack = set(document.keywords) | self._terms(document.title) | self._terms(document.summary)
        return len(haystack & query_terms)

    def _terms(self, text: str) -> set[str]:
        return {
            term.strip(".,!?;:()[]{}\"'").lower()
            for term in text.split()
            if len(term.strip(".,!?;:()[]{}\"'")) > 3
        }
