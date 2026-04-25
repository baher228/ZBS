from __future__ import annotations

from app.agents.campaign_models import (
    CampaignCreateRequest,
    DemoBrief,
    ICPProfile,
    ProductProfile,
    ProspectProfile,
    WorkflowStep,
)
from app.agents.llm import LLMProvider


class DemoBriefAgent:
    name = "demo_brief"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def create_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        return self.llm_provider.generate_demo_brief(
            request,
            product_profile,
            icp,
            prospect_profile,
        )

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="create_demo_brief",
            agent=self.name,
            summary="Created the prospect-specific demo narrative and qualifying questions.",
        )
