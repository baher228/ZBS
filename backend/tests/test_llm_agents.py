"""Tests for LLM-powered agent upgrades (legal, review, orchestrator, content)."""

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.legal import LegalAgent
from app.agents.llm import MockLLMProvider
from app.agents.models import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    OrchestratorStatus,
    ReviewStatus,
)
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent


def _mock_llm() -> MockLLMProvider:
    return MockLLMProvider()


# --- Legal Agent with LLM ---


def test_legal_agent_with_llm_provider_returns_source_grounded_scan() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Check legal risks for privacy and advertising compliance",
            startup_idea="AI GTM office for founders",
            target_audience="US startup founders",
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert response.output["important_notice"]
    assert response.output["relevant_sources"]
    assert response.output["founder_checklist"]
    assert response.output["questions_for_counsel"]


def test_legal_agent_without_llm_falls_back_to_template() -> None:
    agent = LegalAgent(llm_provider=None)
    response = agent.run(
        AgentRequest(prompt="Check privacy compliance for a SaaS launch")
    )

    assert response.agent == AgentCapability.LEGAL
    assert response.output["important_notice"]
    assert "https://www.ftc.gov" in response.output["relevant_sources"]


# --- Review Agent with LLM ---


def test_review_agent_with_llm_approves_strong_output() -> None:
    llm = _mock_llm()
    reviewer = ReviewAgent(llm_provider=llm)
    result = reviewer.review(
        AgentRequest(
            prompt="Create launch content for a GTM AI office",
            startup_idea="GTM AI office",
        ),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="GTM Content Package",
            summary="Generated content",
            output={
                "positioning": "GTM AI office helps founders launch and start sales conversations with practical content.",
                "landing_copy": "Launch your GTM AI office with clear landing copy for founders and first buyers.",
                "icp_notes": "Prioritize founders who need launch support and practical sales conversations.",
                "launch_email": "Subject: Launch your GTM AI office\n\nFounders can start faster with this launch workflow.",
                "social_post": "Building a GTM AI office for founders who want to launch and start sales conversations.",
            },
        ),
    )

    assert result.status == ReviewStatus.APPROVED
    assert result.score > 0.5
    assert result.feedback


def test_review_agent_with_llm_fails_empty_output() -> None:
    llm = _mock_llm()
    reviewer = ReviewAgent(llm_provider=llm)
    result = reviewer.review(
        AgentRequest(prompt="Create content"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Empty",
            summary="Nothing",
            output={},
        ),
    )

    assert result.status == ReviewStatus.FAILED


def test_review_agent_without_llm_uses_heuristics() -> None:
    reviewer = ReviewAgent(llm_provider=None)
    result = reviewer.review(
        AgentRequest(
            prompt="Create launch content for a GTM AI office",
            startup_idea="GTM AI office",
        ),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="GTM Content Package",
            summary="Generated content",
            output={
                "positioning": "GTM AI office helps founders launch and start sales conversations.",
                "landing_copy": "Launch your GTM AI office with clear landing copy.",
                "icp_notes": "Prioritize founders who need launch support.",
                "launch_email": "Subject: Launch your GTM AI office\n\nFounders can start faster.",
                "social_post": "Building a GTM AI office for founders.",
            },
        ),
    )

    assert result.status in (ReviewStatus.APPROVED, ReviewStatus.REVISE)
    assert result.score > 0


# --- Orchestrator with LLM ---


def test_orchestrator_with_llm_classifies_legal_task() -> None:
    llm = _mock_llm()
    registry = AgentRegistry([ContentGeneratorAgent(llm), LegalAgent(llm_provider=llm)])
    orchestrator = Orchestrator(
        registry=registry,
        review_agent=ReviewAgent(llm_provider=llm),
        llm_provider=llm,
    )

    response = orchestrator.handle_task(
        AgentRequest(
            prompt="Review privacy and compliance risks for my SaaS launch",
            context={"task_type": "legal"},
        )
    )

    assert response.selected_agent == AgentCapability.LEGAL
    assert response.decision.status == OrchestratorStatus.COMPLETED


def test_orchestrator_with_llm_classifies_content_task() -> None:
    llm = _mock_llm()
    registry = AgentRegistry([ContentGeneratorAgent(llm), LegalAgent(llm_provider=llm)])
    orchestrator = Orchestrator(
        registry=registry,
        review_agent=ReviewAgent(llm_provider=llm),
        llm_provider=llm,
    )

    response = orchestrator.handle_task(
        AgentRequest(
            prompt="Create landing page copy and a launch email",
            startup_idea="AI sales platform",
            context={"task_type": "content"},
        )
    )

    assert response.selected_agent == AgentCapability.CONTENT_GENERATOR
    assert response.decision.status == OrchestratorStatus.COMPLETED


def test_orchestrator_llm_classify_without_explicit_task_type() -> None:
    llm = _mock_llm()
    registry = AgentRegistry([ContentGeneratorAgent(llm), LegalAgent(llm_provider=llm)])
    orchestrator = Orchestrator(
        registry=registry,
        review_agent=ReviewAgent(llm_provider=llm),
        llm_provider=llm,
    )

    response = orchestrator.handle_task(
        AgentRequest(prompt="Check GDPR compliance for our data handling")
    )

    assert response.selected_agent == AgentCapability.LEGAL


def test_orchestrator_without_llm_falls_back_to_keywords() -> None:
    llm = _mock_llm()
    registry = AgentRegistry([ContentGeneratorAgent(llm), LegalAgent()])
    orchestrator = Orchestrator(
        registry=registry,
        review_agent=ReviewAgent(),
        llm_provider=None,
    )

    response = orchestrator.handle_task(
        AgentRequest(prompt="Create landing page copy for my product")
    )

    assert response.selected_agent == AgentCapability.CONTENT_GENERATOR


# --- Mock LLM new methods ---


def test_mock_llm_classify_task() -> None:
    llm = _mock_llm()
    classification = llm.classify_task(
        AgentRequest(prompt="Check legal compliance", context={"task_type": "legal"})
    )
    assert classification.agent == AgentCapability.LEGAL
    assert classification.confidence == 1.0


def test_mock_llm_review_agent_output() -> None:
    llm = _mock_llm()
    evaluation = llm.review_agent_output(
        AgentRequest(prompt="Create content"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Test",
            summary="Test",
            output={"positioning": "A" * 200, "landing_copy": "B" * 200},
        ),
    )
    assert evaluation.relevance > 0
    assert evaluation.completeness > 0
    assert evaluation.feedback


def test_mock_llm_generate_legal_scan() -> None:
    llm = _mock_llm()
    scan = llm.generate_legal_scan(
        AgentRequest(prompt="Check privacy risks"),
        "FTC Privacy Guide: https://www.ftc.gov/...",
    )
    assert scan.important_notice
    assert scan.relevant_sources
    assert scan.founder_checklist
