from abc import ABC, abstractmethod

from app.agents.models import AgentRequest
from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate_content_package(self, request: AgentRequest) -> dict[str, str]:
        """Return a GTM content package for a founder's startup idea."""


class MockLLMProvider(LLMProvider):
    def generate_content_package(self, request: AgentRequest) -> dict[str, str]:
        idea = request.startup_idea or request.prompt
        audience = request.target_audience or "early customers"
        goal = request.goal or "validate demand and start founder-led sales"
        tone = request.tone or "clear, confident, and practical"
        channel = request.channel or "multi-channel launch"

        return {
            "positioning": (
                f"{idea} helps {audience} solve a painful GTM problem with a "
                f"{tone} approach focused on {goal}."
            ),
            "landing_copy": (
                f"Launch faster with a GTM AI office built for {audience}. "
                "Plan the offer, create first-touch assets, and keep momentum "
                "from idea to first conversations."
            ),
            "icp_notes": (
                f"Prioritize {audience} who already feel urgency around {goal}. "
                "Look for buyers with active launches, unclear messaging, or too "
                "many manual GTM tasks."
            ),
            "launch_email": (
                f"Subject: A faster way to start {idea}\n\n"
                f"Hi,\n\nWe are building {idea} for {audience}. It helps teams "
                f"{goal} without stitching together disconnected tools. If this "
                "is on your roadmap, I would value your feedback.\n\nBest,"
            ),
            "social_post": (
                f"Building {idea} for {audience}. The goal: {goal}. "
                f"Starting with a {channel} package so founders can move from "
                "rough idea to real market conversations faster."
            ),
        }


class UnconfiguredLLMProvider(LLMProvider):
    def generate_content_package(self, request: AgentRequest) -> dict[str, str]:
        raise RuntimeError(
            f"LLM provider '{settings.llm_provider}' is not configured. "
            "Set LLM_PROVIDER=mock or provide a supported provider adapter."
        )


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider.lower() == "mock" or not settings.llm_api_key:
        return MockLLMProvider()
    return UnconfiguredLLMProvider()
