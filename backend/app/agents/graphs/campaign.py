from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents.campaign_models import (
    CampaignCreateRequest,
    CampaignGraphState,
    CampaignResponse,
    DemoRoom,
)
from app.agents.capabilities import (
    DemoBriefAgent,
    DemoPlanAgent,
    OrchestratorAgent,
    OutreachAgent,
    ReadinessAgent,
    ResearchAgent,
    StrategistAgent,
)
from app.agents.llm import LLMProvider
from app.agents.store import InMemoryCampaignStore
from app.core.config import settings


class CampaignGraphRunner:
    def __init__(self, llm_provider: LLMProvider, store: InMemoryCampaignStore) -> None:
        self.store = store
        self.orchestrator = OrchestratorAgent()
        self.strategist = StrategistAgent(llm_provider)
        self.research = ResearchAgent(llm_provider)
        self.demo_brief = DemoBriefAgent(llm_provider)
        self.demo_plan = DemoPlanAgent(llm_provider)
        self.outreach = OutreachAgent(llm_provider)
        self.readiness = ReadinessAgent()
        self.graph = self._compile_graph()

    def run(self, request: CampaignCreateRequest) -> CampaignResponse:
        state = self.graph.invoke({"request": request})
        return CampaignResponse(
            campaign_id=state["campaign_id"],
            product_profile=state["product_profile"],
            icp=state["icp"],
            prospect_profile=state["prospect_profile"],
            demo_brief=state["demo_brief"],
            demo_plan=state["demo_plan"],
            outreach_message=state["outreach_message"],
            demo_room=state["demo_room"],
            readiness_score=state["readiness_score"],
            workflow_steps=state["workflow_steps"],
        )

    def _compile_graph(self):
        graph = StateGraph(CampaignGraphState)
        graph.add_node("orchestrator", self._orchestrator)
        graph.add_node("strategist", self._strategist)
        graph.add_node("research", self._research)
        graph.add_node("demo_brief", self._demo_brief)
        graph.add_node("demo_plan", self._demo_plan)
        graph.add_node("outreach", self._outreach)
        graph.add_node("readiness", self._readiness)
        graph.add_node("persist_demo_room", self._persist_demo_room)

        graph.add_edge(START, "orchestrator")
        graph.add_edge("orchestrator", "strategist")
        graph.add_edge("strategist", "research")
        graph.add_edge("research", "demo_brief")
        graph.add_edge("demo_brief", "demo_plan")
        graph.add_edge("demo_plan", "outreach")
        graph.add_edge("outreach", "readiness")
        graph.add_edge("readiness", "persist_demo_room")
        graph.add_edge("persist_demo_room", END)
        return graph.compile()

    def _orchestrator(self, state: CampaignGraphState) -> CampaignGraphState:
        return self.orchestrator.initialize_campaign()

    def _strategist(self, state: CampaignGraphState) -> CampaignGraphState:
        strategy = self.strategist.build_strategy(state["request"])
        return {
            "product_profile": strategy.product_profile,
            "icp": strategy.icp,
            "workflow_steps": [
                *state["workflow_steps"],
                self.strategist.completed_step(),
            ],
        }

    def _research(self, state: CampaignGraphState) -> CampaignGraphState:
        prospect_profile = self.research.research_prospect(state["request"])
        return {
            "prospect_profile": prospect_profile,
            "workflow_steps": [
                *state["workflow_steps"],
                self.research.completed_step(),
            ],
        }

    def _demo_brief(self, state: CampaignGraphState) -> CampaignGraphState:
        demo_brief = self.demo_brief.create_brief(
            state["request"],
            state["product_profile"],
            state["icp"],
            state["prospect_profile"],
        )
        return {
            "demo_brief": demo_brief,
            "workflow_steps": [
                *state["workflow_steps"],
                self.demo_brief.completed_step(),
            ],
        }

    def _demo_plan(self, state: CampaignGraphState) -> CampaignGraphState:
        demo_plan = self.demo_plan.create_plan(
            state["request"],
            state["product_profile"],
            state["prospect_profile"],
            state["demo_brief"],
        )
        return {
            "demo_plan": demo_plan,
            "workflow_steps": [
                *state["workflow_steps"],
                self.demo_plan.completed_step(),
            ],
        }

    def _outreach(self, state: CampaignGraphState) -> CampaignGraphState:
        demo_room_url = f"{settings.frontend_base_url.rstrip('/')}/demo-rooms/{state['demo_room_id']}"
        outreach_message = self.outreach.write_outreach(
            state["request"],
            state["product_profile"],
            state["prospect_profile"],
            state["demo_brief"],
            demo_room_url,
        )
        return {
            "outreach_message": outreach_message,
            "workflow_steps": [
                *state["workflow_steps"],
                self.outreach.completed_step(),
            ],
        }

    def _readiness(self, state: CampaignGraphState) -> CampaignGraphState:
        readiness_score = self.readiness.score(state["request"], state["prospect_profile"])
        return {
            "readiness_score": readiness_score,
            "workflow_steps": [
                *state["workflow_steps"],
                self.readiness.completed_step(),
            ],
        }

    def _persist_demo_room(self, state: CampaignGraphState) -> CampaignGraphState:
        prospect = state["prospect_profile"]
        demo_brief = state["demo_brief"]
        demo_room = DemoRoom(
            id=state["demo_room_id"],
            campaign_id=state["campaign_id"],
            prospect_company=prospect.company_name,
            headline=demo_brief.title,
            relevance_summary=prospect.relevance_angle,
            demo_plan=state["demo_plan"],
            suggested_questions=demo_brief.qualifying_questions,
        )
        campaign = CampaignResponse(
            campaign_id=state["campaign_id"],
            product_profile=state["product_profile"],
            icp=state["icp"],
            prospect_profile=state["prospect_profile"],
            demo_brief=demo_brief,
            demo_plan=state["demo_plan"],
            outreach_message=state["outreach_message"],
            demo_room=demo_room,
            readiness_score=state["readiness_score"],
            workflow_steps=[
                *state["workflow_steps"],
                self.orchestrator.persisted_step(),
            ],
        )
        self.store.save_campaign(campaign)
        return {"demo_room": demo_room, "workflow_steps": campaign.workflow_steps}
