from app.agents.campaign_models import CampaignCreateRequest
from app.agents.graphs import CampaignGraphRunner
from app.agents.llm import MockLLMProvider
from app.agents.store import InMemoryCampaignStore


def make_request(product_name: str = "DemoRoom AI") -> CampaignCreateRequest:
    return CampaignCreateRequest(
        product_name=product_name,
        product_description=(
            "AI demo rooms for technical B2B founders that turn cold outreach "
            "into qualified sales conversations."
        ),
        target_audience="technical B2B founders",
        prospect_company="Pydantic",
        prospect_description="Python data validation and agent reliability tooling company.",
    )


def test_campaign_graph_creates_structured_demo_room() -> None:
    store = InMemoryCampaignStore()
    runner = CampaignGraphRunner(MockLLMProvider(), store)

    response = runner.run(make_request())

    assert response.campaign_id.startswith("camp_")
    assert response.demo_room.id.startswith("room_")
    assert response.product_profile.name == "DemoRoom AI"
    assert response.icp.primary_buyer == "technical B2B founders"
    assert response.prospect_profile.company_name == "Pydantic"
    assert response.demo_plan.steps
    assert response.demo_room.demo_plan == response.demo_plan
    assert response.outreach_message.demo_room_url.endswith(f"/demo-rooms/{response.demo_room.id}")
    assert response.readiness_score.score >= 80
    assert store.get_demo_room(response.demo_room.id) == response.demo_room


def test_campaign_graph_records_expected_node_order() -> None:
    store = InMemoryCampaignStore()
    runner = CampaignGraphRunner(MockLLMProvider(), store)

    response = runner.run(make_request())

    assert [step.name for step in response.workflow_steps] == [
        "orchestrate_campaign",
        "build_product_strategy",
        "research_prospect",
        "create_demo_brief",
        "create_demo_plan",
        "write_outreach",
        "score_readiness",
        "persist_demo_room",
    ]


def test_campaign_graph_uses_new_product_inputs() -> None:
    store = InMemoryCampaignStore()
    runner = CampaignGraphRunner(MockLLMProvider(), store)

    response = runner.run(
        CampaignCreateRequest(
            product_name="TracePilot",
            product_description=(
                "An observability tool for teams building AI agents that need to inspect "
                "tool calls, state transitions, and user-facing failures."
            ),
            target_audience="AI platform engineering teams",
            prospect_company="Render",
            prospect_description="Cloud application hosting platform for developers.",
        )
    )

    assert response.product_profile.name == "TracePilot"
    assert response.icp.primary_buyer == "AI platform engineering teams"
    assert response.prospect_profile.company_name == "Render"
    assert response.demo_plan.steps[1].asset_needed
    assert "TracePilot" in response.outreach_message.subject
