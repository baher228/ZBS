from __future__ import annotations

from app.agents.campaign_models import DemoRoom
from app.agents.llm import LLMProvider


class DemoAgent:
    name = "demo_agent"

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def reply(self, demo_room: DemoRoom, message: str) -> str:
        return self.llm_provider.generate_demo_reply(demo_room, message)
