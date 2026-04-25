from app.agents.campaign_models import CampaignCreateRequest, ChatMessage, DemoRoom
from app.agents.capabilities import (
    DemoAgent,
    DemoBriefAgent,
    OutreachAgent,
    ReadinessAgent,
    ResearchAgent,
    SalesOpsAgent,
    StrategistAgent,
)
from app.agents.llm import MockLLMProvider


def make_request() -> CampaignCreateRequest:
    return CampaignCreateRequest(
        product_name="TracePilot",
        product_description=(
            "An observability tool for teams building AI agents that need to inspect "
            "tool calls, state transitions, and user-facing failures."
        ),
        target_audience="AI platform engineering teams",
        prospect_company="Render",
        prospect_description="Cloud application hosting platform for developers.",
    )


def test_reusable_campaign_capabilities_can_run_without_graph() -> None:
    provider = MockLLMProvider()
    request = make_request()

    strategy = StrategistAgent(provider).build_strategy(request)
    prospect = ResearchAgent(provider).research_prospect(request)
    brief = DemoBriefAgent(provider).create_brief(
        request,
        strategy.product_profile,
        strategy.icp,
        prospect,
    )
    outreach = OutreachAgent(provider).write_outreach(
        request,
        strategy.product_profile,
        prospect,
        brief,
        "http://localhost:5173/demo-rooms/room_test",
    )
    readiness = ReadinessAgent().score(request, prospect)

    assert strategy.product_profile.name == "TracePilot"
    assert prospect.company_name == "Render"
    assert brief.qualifying_questions
    assert "TracePilot" in outreach.subject
    assert readiness.score >= 80


def test_demo_and_sales_ops_capabilities_can_run_without_graph() -> None:
    provider = MockLLMProvider()
    demo_room = DemoRoom(
        id="room_test",
        campaign_id="camp_test",
        prospect_company="Render",
        headline="TracePilot for Render",
        relevance_summary="Debug agent failures with state-level observability.",
        suggested_questions=["How would this fit our workflow?"],
    )

    reply = DemoAgent(provider).reply(demo_room, "How does this work?")
    qualified_room = demo_room.model_copy(
        update={
            "transcript": [
                ChatMessage(role="user", content="How does this work?"),
                ChatMessage(role="assistant", content=reply),
            ]
        }
    )
    report = SalesOpsAgent(provider).qualify(qualified_room)

    assert "demo room" in reply.lower() or "context" in reply.lower()
    assert report.demo_room_id == "room_test"
    assert report.lead_score >= 80
