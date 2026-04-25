from __future__ import annotations

from app.agents.campaign_models import DemoRoom, QualificationReport
from app.agents.llm import LLMProvider


class SalesOpsAgent:
    name = "sales_ops"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def qualify(self, demo_room: DemoRoom) -> QualificationReport:
        return self.llm_provider.generate_qualification(demo_room)
