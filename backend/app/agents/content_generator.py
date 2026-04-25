from app.agents.llm import LLMProvider
from app.agents.models import AgentCapability, AgentRequest, AgentResponse


class ContentGeneratorAgent:
    capability = AgentCapability.CONTENT_GENERATOR

    def __init__(self, llm_provider: LLMProvider) -> None:
        self.llm_provider = llm_provider

    def run(self, request: AgentRequest) -> AgentResponse:
        output = self.llm_provider.generate_content_package(request)
        idea = request.startup_idea or request.prompt
        return AgentResponse(
            agent=self.capability,
            title="GTM Content Package",
            output=output,
            summary=f"Generated a founder-ready GTM content package for: {idea}",
        )
