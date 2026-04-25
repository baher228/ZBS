from __future__ import annotations

from app.agents.campaign_models import CampaignCreateRequest, ProspectProfile, WorkflowStep
from app.agents.llm import LLMProvider


class ResearchAgent:
    name = "research"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def research_prospect(self, request: CampaignCreateRequest) -> ProspectProfile:
        return self.llm_provider.generate_prospect_profile(request)

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="research_prospect",
            agent=self.name,
            summary="Structured prospect context and likely account-specific pains.",
        )
