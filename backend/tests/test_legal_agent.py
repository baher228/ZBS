from app.agents.legal import LegalAgent
from app.agents.models import AgentCapability, AgentRequest, ReviewStatus
from app.agents.review import ReviewAgent


def test_legal_agent_returns_source_grounded_issue_scan() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Check legal risks for landing page claims, privacy, and company formation",
            startup_idea="AI GTM office for founders",
            target_audience="US startup founders",
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert "not legal advice" in response.output["important_notice"].lower()
    assert "https://www.ftc.gov" in response.output["relevant_sources"]
    assert response.output["questions_for_counsel"]


def test_review_approves_complete_legal_scan() -> None:
    agent_response = LegalAgent().run(
        AgentRequest(prompt="Review privacy and advertising compliance for my SaaS launch")
    )

    review = ReviewAgent().review(
        AgentRequest(prompt="Review privacy and advertising compliance for my SaaS launch"),
        agent_response,
    )

    assert review.status == ReviewStatus.APPROVED
