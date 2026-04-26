from app.agents.models import AgentCapability, AgentRequest, AgentResponse, ReviewStatus
from app.agents.review import ReviewAgent


def test_review_approves_strong_content_package() -> None:
    result = ReviewAgent().review(
        AgentRequest(
            prompt="Create launch content for a GTM AI office",
            startup_idea="GTM AI office",
            target_audience="founders",
            goal="launch and start sales conversations",
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


def test_review_approves_complete_legal_scan() -> None:
    result = ReviewAgent().review(
        AgentRequest(prompt="Review privacy and advertising compliance for my SaaS launch"),
        AgentResponse(
            agent=AgentCapability.LEGAL,
            title="Founder Legal Issue Scan",
            summary="Generated legal scan",
            output={
                "important_notice": "This is a legal risk scan for founders. A qualified lawyer should review.",
                "jurisdiction_scope": "Seed sources are currently United States-focused.",
                "relevant_sources": "FTC Truth in Advertising (US): https://www.ftc.gov/business-guidance/advertising-marketing/truth-advertising",
                "risk_summary": "Marketing claims and privacy promises need substantiation before launch.",
                "founder_checklist": "1. Confirm the company formation path.\n2. List public claims.",
                "questions_for_counsel": "1. Are the claims substantiated?\n2. What privacy terms are needed?",
                "next_steps": "Collect claims, data flows, and jurisdictions before counsel review.",
            },
        ),
    )

    assert result.status == ReviewStatus.APPROVED


def test_review_fails_empty_output() -> None:
    result = ReviewAgent().review(
        AgentRequest(prompt="Create launch content for a GTM AI office"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Empty",
            summary="No useful content",
            output={},
        ),
    )

    assert result.status == ReviewStatus.FAILED


def test_review_requests_revision_for_partial_output() -> None:
    result = ReviewAgent().review(
        AgentRequest(prompt="Create launch content for a GTM AI office"),
        AgentResponse(
            agent=AgentCapability.CONTENT_GENERATOR,
            title="Partial",
            summary="Partial content",
            output={
                "positioning": "GTM AI office helps founders launch faster.",
                "landing_copy": "Launch faster with clearer GTM content.",
            },
        ),
    )

    assert result.status == ReviewStatus.REVISE
    assert result.revision_instruction is not None
