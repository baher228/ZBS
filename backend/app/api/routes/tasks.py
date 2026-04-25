from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.legal import LegalAgent
from app.agents.llm import get_llm_provider
from app.agents.models import TaskRequest, TaskResponse
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])


@lru_cache
def get_orchestrator() -> Orchestrator:
    llm = get_llm_provider()
    registry = AgentRegistry(
        [
            ContentGeneratorAgent(llm),
            LegalAgent(llm_provider=llm),
        ]
    )
    return Orchestrator(
        registry=registry,
        review_agent=ReviewAgent(llm_provider=llm),
        llm_provider=llm,
    )


@router.post("", response_model=TaskResponse)
def create_task(request: TaskRequest) -> TaskResponse:
    return get_orchestrator().handle_task(request)
