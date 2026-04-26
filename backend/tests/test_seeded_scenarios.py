from app.agents.campaign_models import CampaignCreateRequest
from app.agents.graphs import CampaignGraphRunner
from app.agents.llm import MockLLMProvider
from app.agents.store import InMemoryCampaignStore


SEEDED_SCENARIOS = [
    CampaignCreateRequest(
        product_name="AI GTM Office",
        product_description=(
            "An AI GTM office that turns cold outreach into personalized demo rooms, "
            "qualified sales conversations, CRM notes, and follow-up emails."
        ),
        target_audience="technical B2B founders",
        prospect_company="Mubit",
        prospect_description="Agent memory platform that helps AI agents learn from past runs.",
    ),
    CampaignCreateRequest(
        product_name="TracePilot",
        product_description=(
            "An observability tool for teams building AI agents that need to inspect "
            "tool calls, state transitions, and user-facing failures."
        ),
        target_audience="AI platform engineering teams",
        prospect_company="Render",
        prospect_description="Cloud application hosting platform for developers.",
    ),
    CampaignCreateRequest(
        product_name="SecureShip",
        product_description=(
            "A security review assistant that helps developer tool companies answer "
            "enterprise security questionnaires faster and more accurately."
        ),
        target_audience="B2B SaaS founders selling to enterprise buyers",
        prospect_company="Linear",
        prospect_description="Issue tracking and product development platform for software teams.",
    ),
]


def test_seeded_hackathon_scenarios_create_guided_demo_plans() -> None:
    runner = CampaignGraphRunner(MockLLMProvider(), InMemoryCampaignStore())

    for request in SEEDED_SCENARIOS:
        response = runner.run(request)

        assert response.product_profile.name == request.product_name
        assert response.prospect_profile.company_name == request.prospect_company
        assert response.demo_plan.steps
        assert response.demo_plan.steps[0].qualification_question
        assert response.demo_room.demo_plan == response.demo_plan
        assert response.readiness_score.score >= 80
