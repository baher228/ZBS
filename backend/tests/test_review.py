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
