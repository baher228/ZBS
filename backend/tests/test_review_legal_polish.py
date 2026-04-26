"""Tests for Iteration 3: Review Agent + Legal Agent polish."""

from app.agents.legal import LegalAgent, _INDUSTRY_MAP
from app.agents.llm import MockLLMProvider
from app.agents.models import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    LLMReviewEvaluation,
    ReviewStatus,
)
from app.agents.review import ReviewAgent


def _mock_llm() -> MockLLMProvider:
    return MockLLMProvider()


# --- Review Agent threshold changes ---


def test_review_revise_when_revision_instruction_present() -> None:
    """If the LLM returns a revision_instruction, status should be REVISE even with decent scores."""

    class StrictReviewer(MockLLMProvider):
        def review_agent_output(self, request, response):
            return LLMReviewEvaluation(
                relevance=0.75,
                completeness=0.80,
                clarity=0.75,
                actionability=0.70,
                feedback="The content mentions the company name but doesn't reference specific product features.",
                revision_instruction="Add concrete references to the product's key features and differentiators.",
            )

    reviewer = ReviewAgent(llm_provider=StrictReviewer())
    result = reviewer.review(
        AgentRequest(prompt="Create content", startup_idea="TestCorp AI"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Content",
            summary="Generated",
            output={"positioning": "TestCorp AI is a great product for everyone."},
        ),
    )

    assert result.status == ReviewStatus.REVISE
    assert result.revision_instruction is not None


def test_review_fails_on_very_low_score() -> None:
    """Score below 0.35 should FAIL."""

    class FailReviewer(MockLLMProvider):
        def review_agent_output(self, request, response):
            return LLMReviewEvaluation(
                relevance=0.2,
                completeness=0.3,
                clarity=0.3,
                actionability=0.2,
                feedback="Output is completely generic.",
            )

    reviewer = ReviewAgent(llm_provider=FailReviewer())
    result = reviewer.review(
        AgentRequest(prompt="Create content"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Content",
            summary="Generated",
            output={"positioning": "We help businesses grow."},
        ),
    )

    assert result.status == ReviewStatus.FAILED


def test_review_revise_on_low_relevance() -> None:
    """Relevance below 0.6 should trigger REVISE even if other scores are high."""

    class LowRelevanceReviewer(MockLLMProvider):
        def review_agent_output(self, request, response):
            return LLMReviewEvaluation(
                relevance=0.5,
                completeness=0.9,
                clarity=0.85,
                actionability=0.8,
                feedback="Output is well-structured but doesn't address the specific company.",
            )

    reviewer = ReviewAgent(llm_provider=LowRelevanceReviewer())
    result = reviewer.review(
        AgentRequest(prompt="Create content for TestCorp AI"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Content",
            summary="Generated",
            output={"positioning": "A great SaaS platform for B2B teams."},
        ),
    )

    assert result.status == ReviewStatus.REVISE


def test_review_approves_genuinely_good_output() -> None:
    """High scores with no revision instruction should approve."""

    class GoodReviewer(MockLLMProvider):
        def review_agent_output(self, request, response):
            return LLMReviewEvaluation(
                relevance=0.85,
                completeness=0.90,
                clarity=0.85,
                actionability=0.80,
                feedback="The output is specific to TestCorp AI, references key features, and is ready to use.",
            )

    reviewer = ReviewAgent(llm_provider=GoodReviewer())
    result = reviewer.review(
        AgentRequest(prompt="Create content for TestCorp AI"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Content",
            summary="Generated",
            output={
                "positioning": "TestCorp AI automates outbound sales for B2B teams with AI personalization and CRM sync.",
            },
        ),
    )

    assert result.status == ReviewStatus.APPROVED
    assert result.score >= 0.70


# --- Legal Agent auto-detect ---


def test_legal_auto_detect_fintech_industry() -> None:
    """FinTech company profile should auto-detect FinTech industry docs."""
    detected = LegalAgent._detect_industries("FinTech SaaS", None)
    assert detected == ["FinTech"]


def test_legal_auto_detect_healthtech_industry() -> None:
    """HealthTech company should auto-detect HealthTech industry docs."""
    detected = LegalAgent._detect_industries("Digital Healthcare Platform", None)
    assert detected == ["HealthTech"]


def test_legal_auto_detect_edtech_industry() -> None:
    """EdTech company should auto-detect EdTech industry docs."""
    detected = LegalAgent._detect_industries("Online Education Marketplace", None)
    assert detected == ["EdTech"]


def test_legal_explicit_industries_override_auto_detect() -> None:
    """Explicit industries from user should override auto-detection."""
    detected = LegalAgent._detect_industries("FinTech SaaS", ["HealthTech"])
    assert detected == ["HealthTech"]


def test_legal_no_industry_returns_none() -> None:
    """Generic industry string should return None (no filtering)."""
    detected = LegalAgent._detect_industries("SaaS", None)
    assert detected is None


def test_legal_auto_detect_empty_string_returns_none() -> None:
    """Empty industry string should return None."""
    detected = LegalAgent._detect_industries("", None)
    assert detected is None


def test_legal_agent_uses_company_profile_jurisdictions() -> None:
    """Legal agent should use jurisdictions from company profile when request has defaults."""
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)

    company_context = (
        "Company: TestCorp\n"
        "Description: AI sales automation\n"
        "Industry: FinTech\n"
        "Jurisdictions: US, EU, UK"
    )

    response = agent.run(
        AgentRequest(
            prompt="Check legal risks for my company",
            context={"company_profile": company_context},
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert response.output["relevant_sources"]


def test_legal_agent_auto_detects_industry_from_profile() -> None:
    """Legal agent should auto-detect industry from company profile."""
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)

    company_context = (
        "Company: HealthApp\n"
        "Description: Patient monitoring platform\n"
        "Industry: HealthTech\n"
        "Jurisdictions: US"
    )

    response = agent.run(
        AgentRequest(
            prompt="Check compliance for my healthcare app",
            context={"company_profile": company_context},
        )
    )

    assert response.agent == AgentCapability.LEGAL
    sources = response.output["relevant_sources"]
    assert "HIPAA" in sources or "hipaa" in sources.lower()


def test_industry_map_covers_expected_keywords() -> None:
    """Ensure the industry map has entries for all three regulated sectors."""
    fintech_keywords = [k for k, v in _INDUSTRY_MAP.items() if "FinTech" in v]
    healthtech_keywords = [k for k, v in _INDUSTRY_MAP.items() if "HealthTech" in v]
    edtech_keywords = [k for k, v in _INDUSTRY_MAP.items() if "EdTech" in v]

    assert len(fintech_keywords) >= 3
    assert len(healthtech_keywords) >= 3
    assert len(edtech_keywords) >= 2
