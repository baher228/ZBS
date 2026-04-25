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
    industry: str = "general"


# --- US General ---

_FTC_ADVERTISING = LegalDocument(
    id="ftc-advertising-faq",
    title="FTC Advertising FAQ's: A Guide for Small Business",
    jurisdiction="United States",
    source_url="https://www.ftc.gov/business-guidance/resources/advertising-faqs-guide-small-business",
    summary=(
        "Advertising claims should be truthful, not misleading, and supported before publication. "
        "Claims about performance, endorsements, pricing, and product benefits need evidence."
    ),
    keywords=("advertising", "marketing", "claims", "copy", "endorsement", "pricing", "truth"),
)

_FTC_PRIVACY = LegalDocument(
    id="ftc-privacy-security",
    title="FTC Privacy and Security Business Guidance",
    jurisdiction="United States",
    source_url="https://www.ftc.gov/business-guidance/privacy-security",
    summary=(
        "Businesses handling consumer data should consider privacy notices, data minimization, "
        "security safeguards, vendor practices, and promises made to customers."
    ),
    keywords=("privacy", "security", "data", "personal", "consumer", "saas", "app"),
)

_SBA_STRUCTURE = LegalDocument(
    id="sba-business-structure",
    title="SBA Choose a Business Structure",
    jurisdiction="United States",
    source_url="https://www.sba.gov/business-guide/launch-your-business/choose-business-structure",
    summary=(
        "Business structure affects liability, taxes, filings, and operations. Founders should compare "
        "structures and confirm state-specific requirements before forming."
    ),
    keywords=("formation", "company", "llc", "corporation", "liability", "tax", "structure"),
)

_ADA_WEB = LegalDocument(
    id="ada-web-guidance",
    title="ADA.gov Guidance on Web Accessibility and the ADA",
    jurisdiction="United States",
    source_url="https://www.ada.gov/resources/web-guidance/",
    summary=(
        "Web accessibility can affect access to goods, services, programs, and activities. Existing "
        "technical standards can help teams make websites more accessible."
    ),
    keywords=("accessibility", "ada", "website", "web", "disability", "compliance"),
)

_FTC_ENDORSEMENTS = LegalDocument(
    id="ftc-endorsements-reviews",
    title="FTC Endorsements, Influencers, and Reviews",
    jurisdiction="United States",
    source_url="https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews",
    summary=(
        "Endorsements, reviews, testimonials, and influencer content can create legal risk when they "
        "misrepresent experience, hide material connections, or use deceptive review practices."
    ),
    keywords=("reviews", "testimonials", "influencer", "endorsement", "social", "affiliate"),
)

_CAN_SPAM = LegalDocument(
    id="ftc-can-spam",
    title="FTC CAN-SPAM Act: A Compliance Guide for Business",
    jurisdiction="United States",
    source_url="https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business",
    summary=(
        "Commercial email must include honest headers, non-deceptive subject lines, an opt-out mechanism "
        "honored within 10 business days, the sender's physical postal address, and identification as an ad "
        "when applicable. Violations can result in penalties per email."
    ),
    keywords=("email", "spam", "opt-out", "unsubscribe", "marketing", "outreach", "newsletter"),
)

_CCPA = LegalDocument(
    id="ccpa-overview",
    title="California Consumer Privacy Act (CCPA) / CPRA Overview",
    jurisdiction="United States — California",
    source_url="https://oag.ca.gov/privacy/ccpa",
    summary=(
        "The CCPA gives California consumers the right to know what personal information is collected, "
        "request deletion, opt out of sale or sharing, and non-discrimination. Businesses meeting revenue, "
        "data-volume, or data-sale thresholds must provide notices and honor requests."
    ),
    keywords=("ccpa", "cpra", "california", "privacy", "consumer", "opt-out", "data", "sale"),
)

_SEC_CROWDFUNDING = LegalDocument(
    id="sec-regulation-crowdfunding",
    title="SEC Regulation Crowdfunding Overview",
    jurisdiction="United States",
    source_url="https://www.sec.gov/education/smallbusiness/exemptofferings/regcrowdfunding",
    summary=(
        "Regulation Crowdfunding allows eligible companies to raise up to $5 million per year through "
        "SEC-registered funding portals. Issuers must file Form C, provide financial statements, and "
        "comply with investment limits and ongoing reporting requirements."
    ),
    keywords=("securities", "crowdfunding", "fundraising", "investment", "sec", "equity", "shares"),
)

_SOC2_OVERVIEW = LegalDocument(
    id="aicpa-soc2-overview",
    title="AICPA SOC 2 Trust Services Criteria Overview",
    jurisdiction="International",
    source_url="https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2",
    summary=(
        "SOC 2 reports evaluate an organization's controls related to security, availability, processing "
        "integrity, confidentiality, and privacy. Enterprise buyers often require a SOC 2 Type II report "
        "before signing contracts with SaaS vendors."
    ),
    keywords=("soc2", "soc", "audit", "security", "compliance", "enterprise", "vendor", "trust"),
)

# --- EU / UK ---

_GDPR = LegalDocument(
    id="gdpr-overview",
    title="GDPR Official Text and Key Provisions",
    jurisdiction="European Union",
    source_url="https://gdpr-info.eu/",
    summary=(
        "The GDPR requires a lawful basis for processing personal data, mandates data protection by "
        "design and by default, requires Data Protection Impact Assessments for high-risk processing, "
        "and gives data subjects rights to access, rectify, erase, and port their data. Non-compliance "
        "can result in fines up to 4% of global annual turnover."
    ),
    keywords=("gdpr", "privacy", "data", "eu", "european", "consent", "dpa", "controller", "processor"),
)

_UK_GDPR = LegalDocument(
    id="uk-gdpr-ico",
    title="UK GDPR and Data Protection Act 2018 — ICO Guide",
    jurisdiction="United Kingdom",
    source_url="https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/",
    summary=(
        "The UK GDPR mirrors EU GDPR requirements post-Brexit. Organisations processing data of UK "
        "residents must register with the ICO, maintain lawful bases, and follow UK-specific adequacy "
        "and transfer rules."
    ),
    keywords=("uk", "gdpr", "ico", "data", "privacy", "brexit", "british"),
)

_ECOMMERCE_DIRECTIVE = LegalDocument(
    id="eu-ecommerce-directive",
    title="EU E-Commerce Directive — Key Requirements",
    jurisdiction="European Union",
    source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:32000L0031",
    summary=(
        "Online service providers in the EU must display clear information about the business, provide "
        "transparent pricing, and follow rules for electronic contracts, commercial communications, "
        "and intermediary liability."
    ),
    keywords=("ecommerce", "eu", "online", "terms", "contracts", "commercial", "business"),
)

# --- Industry-Specific ---

_FINTECH_MONEY_TRANSMISSION = LegalDocument(
    id="fintech-money-transmission",
    title="FinCEN Money Transmission Regulations Overview",
    jurisdiction="United States",
    source_url="https://www.fincen.gov/money-services-business-definition",
    summary=(
        "Businesses that transmit money, issue payment instruments, or exchange currency may be "
        "classified as Money Services Businesses (MSBs) and must register with FinCEN, implement "
        "AML programs, file SARs, and comply with state money transmitter licensing requirements."
    ),
    keywords=("fintech", "payments", "money", "transmission", "aml", "kyc", "banking", "finance"),
    industry="fintech",
)

_PCI_DSS = LegalDocument(
    id="pci-dss-overview",
    title="PCI DSS — Payment Card Industry Data Security Standard",
    jurisdiction="International",
    source_url="https://www.pcisecuritystandards.org/document_library/",
    summary=(
        "Any business that stores, processes, or transmits cardholder data must comply with PCI DSS. "
        "Requirements include network segmentation, encryption, access controls, vulnerability management, "
        "and regular security testing."
    ),
    keywords=("pci", "payment", "card", "credit", "debit", "fintech", "merchant", "stripe"),
    industry="fintech",
)

_HIPAA = LegalDocument(
    id="hipaa-overview",
    title="HHS HIPAA for Professionals Overview",
    jurisdiction="United States",
    source_url="https://www.hhs.gov/hipaa/for-professionals/index.html",
    summary=(
        "HIPAA sets standards for protecting health information. Covered entities and business associates "
        "must implement administrative, physical, and technical safeguards, provide breach notification, "
        "and ensure minimum necessary use of Protected Health Information (PHI)."
    ),
    keywords=("hipaa", "health", "medical", "phi", "patient", "healthcare", "healthtech"),
    industry="healthtech",
)

_FDA_DIGITAL_HEALTH = LegalDocument(
    id="fda-digital-health",
    title="FDA Digital Health Policy and Guidance",
    jurisdiction="United States",
    source_url="https://www.fda.gov/medical-devices/digital-health-center-excellence",
    summary=(
        "Software that meets the definition of a medical device may require FDA clearance or approval. "
        "Clinical decision support, remote monitoring, and AI/ML-based diagnostic tools may fall under "
        "FDA regulatory authority depending on their intended use and risk classification."
    ),
    keywords=("fda", "medical", "device", "digital", "health", "clinical", "diagnostic", "ai"),
    industry="healthtech",
)

_FERPA = LegalDocument(
    id="ferpa-overview",
    title="US Department of Education FERPA Overview",
    jurisdiction="United States",
    source_url="https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html",
    summary=(
        "FERPA protects student education records. Schools must obtain consent before disclosing "
        "personally identifiable information from records. EdTech vendors acting as school officials "
        "must limit use of data to the purpose specified in their agreement."
    ),
    keywords=("ferpa", "education", "student", "school", "edtech", "records", "children"),
    industry="edtech",
)

_COPPA = LegalDocument(
    id="coppa-overview",
    title="FTC COPPA — Children's Online Privacy Protection Act",
    jurisdiction="United States",
    source_url="https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa",
    summary=(
        "COPPA requires verifiable parental consent before collecting personal information from children "
        "under 13. Operators must post clear privacy policies, minimize data collection, and maintain "
        "reasonable data security. Applies to websites, apps, and online services directed at children."
    ),
    keywords=("coppa", "children", "kids", "parental", "consent", "edtech", "education", "minors"),
    industry="edtech",
)

# --- Jurisdiction collections ---

US_DOCUMENTS = [
    _FTC_ADVERTISING, _FTC_PRIVACY, _SBA_STRUCTURE, _ADA_WEB,
    _FTC_ENDORSEMENTS, _CAN_SPAM, _CCPA, _SEC_CROWDFUNDING, _SOC2_OVERVIEW,
]

EU_DOCUMENTS = [_GDPR, _ECOMMERCE_DIRECTIVE]

UK_DOCUMENTS = [_UK_GDPR]

INDUSTRY_DOCUMENTS = {
    "fintech": [_FINTECH_MONEY_TRANSMISSION, _PCI_DSS],
    "healthtech": [_HIPAA, _FDA_DIGITAL_HEALTH],
    "edtech": [_FERPA, _COPPA],
}

ALL_DOCUMENTS = US_DOCUMENTS + EU_DOCUMENTS + UK_DOCUMENTS
for docs in INDUSTRY_DOCUMENTS.values():
    ALL_DOCUMENTS.extend(docs)

LEGAL_DOCUMENTS = ALL_DOCUMENTS


class LegalKnowledgeBase:
    def __init__(self, documents: list[LegalDocument] | None = None) -> None:
        self.documents = documents or ALL_DOCUMENTS

    @classmethod
    def for_jurisdictions(
        cls,
        jurisdictions: list[str] | None = None,
        industries: list[str] | None = None,
    ) -> LegalKnowledgeBase:
        docs: list[LegalDocument] = []
        jset = {j.lower() for j in (jurisdictions or ["us"])}

        if "us" in jset or "united states" in jset:
            docs.extend(US_DOCUMENTS)
        if "eu" in jset or "european union" in jset:
            docs.extend(EU_DOCUMENTS)
        if "uk" in jset or "united kingdom" in jset:
            docs.extend(UK_DOCUMENTS)

        for ind in (industries or []):
            ind_docs = INDUSTRY_DOCUMENTS.get(ind.lower(), [])
            docs.extend(ind_docs)

        if not docs:
            docs = list(ALL_DOCUMENTS)

        seen: set[str] = set()
        deduped: list[LegalDocument] = []
        for doc in docs:
            if doc.id not in seen:
                seen.add(doc.id)
                deduped.append(doc)
        return cls(documents=deduped)

    def retrieve(self, query: str, limit: int = 5) -> list[LegalDocument]:
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
