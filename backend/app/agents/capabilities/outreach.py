from __future__ import annotations

from app.agents.campaign_models import (
    CampaignCreateRequest,
    DemoBrief,
    OutreachMessage,
    ProductProfile,
    ProspectProfile,
    WorkflowStep,
)
from app.agents.llm import LLMProvider


class OutreachAgent:
    name = "outreach"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def write_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> OutreachMessage:
        output = self.llm_provider.generate_outreach(
            request,
            product_profile,
            prospect_profile,
            demo_brief,
            demo_room_url,
        )
        return OutreachMessage(**output)

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="write_outreach",
            agent=self.name,
            summary="Wrote personalized outreach with a demo-room link.",
        )
