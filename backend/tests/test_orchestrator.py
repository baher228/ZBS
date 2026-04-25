from app.agents.content_generator import ContentGeneratorAgent
from app.agents.llm import MockLLMProvider
from app.agents.models import AgentCapability, AgentRequest, OrchestratorStatus
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent


def make_orchestrator() -> Orchestrator:
    registry = AgentRegistry([ContentGeneratorAgent(MockLLMProvider())])
    return Orchestrator(registry=registry, review_agent=ReviewAgent())


def test_content_prompt_selects_content_generator() -> None:
    orchestrator = make_orchestrator()

    response = orchestrator.handle_task(
        AgentRequest(
            prompt="Create landing page copy for my AI office",
            startup_idea="GTM AI office for founders",
            target_audience="solo founders",
            goal="start sales conversations",
        )
    )

    assert response.selected_agent == AgentCapability.CONTENT_GENERATOR
    assert response.agent_response is not None
    assert response.review is not None
    assert response.decision.status == OrchestratorStatus.COMPLETED


def test_demo_prompt_returns_unavailable() -> None:
    orchestrator = make_orchestrator()

    response = orchestrator.handle_task(AgentRequest(prompt="Build a demo walkthrough"))

    assert response.selected_agent == AgentCapability.DEMO
    assert response.agent_response is None
    assert response.review is None
    assert response.decision.status == OrchestratorStatus.UNAVAILABLE


def test_unknown_prompt_returns_unsupported() -> None:
    orchestrator = make_orchestrator()

    response = orchestrator.handle_task(AgentRequest(prompt="Please reconcile vendor invoices"))

    assert response.selected_agent == AgentCapability.UNSUPPORTED
    assert response.agent_response is None
    assert response.review is None
    assert response.decision.status == OrchestratorStatus.UNSUPPORTED
