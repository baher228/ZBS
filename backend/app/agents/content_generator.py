from __future__ import annotations

import logging

from app.agents.image_gen import generate_content_images
from app.agents.llm import LLMProvider
from app.agents.models import AgentCapability, AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

CONTENT_KEYS = ["positioning", "landing_copy", "icp_notes", "launch_email", "social_post"]
IMAGE_SECTIONS = ["landing_copy", "social_post"]


class ContentGeneratorAgent:
    capability = AgentCapability.CONTENT_GENERATOR

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def run(self, request: AgentRequest) -> AgentResponse:
        output = self.llm_provider.generate_content_package(request)
        idea = request.startup_idea or request.prompt
        company_context = request.context.get("company_profile", "")

        section_texts = {k: v for k, v in output.items() if k in CONTENT_KEYS}

        images = generate_content_images(
            idea,
            sections=IMAGE_SECTIONS,
            section_texts=section_texts,
            company_context=company_context,
        )
        for section, image in images.items():
            output[f"{section}_image"] = image.url

        return AgentResponse(
            agent=self.capability,
            title="GTM Content Package",
            output=output,
            summary=f"Generated a founder-ready GTM content package for: {idea}",
        )
