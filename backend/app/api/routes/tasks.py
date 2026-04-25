from fastapi import APIRouter

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.legal import LegalAgent
from app.agents.llm import get_llm_provider
from app.agents.models import TaskRequest, TaskResponse
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_orchestrator() -> Orchestrator:
    content_agent = ContentGeneratorAgent(get_llm_provider())
    legal_agent = LegalAgent()
    registry = AgentRegistry([content_agent, legal_agent])
    return Orchestrator(registry=registry, review_agent=ReviewAgent())


@router.post("", response_model=TaskResponse)
def create_task(request: TaskRequest) -> TaskResponse:
    return get_orchestrator().handle_task(request)
