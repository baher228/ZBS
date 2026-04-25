from __future__ import annotations

from app.agents.campaign_models import CampaignCreateRequest, ProductStrategy, WorkflowStep
from app.agents.llm import LLMProvider


class StrategistAgent:
    name = "strategist"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def build_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        return self.llm_provider.generate_product_strategy(request)

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="build_product_strategy",
            agent=self.name,
            summary="Created product profile, ICP, value props, and objections.",
        )
