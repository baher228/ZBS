from __future__ import annotations

from app.agents.campaign_models import (
    CampaignCreateRequest,
    DemoBrief,
    DemoPlan,
    ProductProfile,
    ProspectProfile,
    WorkflowStep,
)
from app.agents.llm import LLMProvider


class DemoPlanAgent:
    name = "demo_plan"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def create_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
        return self.llm_provider.generate_demo_plan(
            request,
            product_profile,
            prospect_profile,
            demo_brief,
        )

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="create_demo_plan",
            agent=self.name,
            summary="Created guided demo steps, assets, talk tracks, and routing rules.",
        )
