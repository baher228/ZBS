from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, File, Form, UploadFile

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.legal import LegalAgent
from app.agents.llm import get_llm_provider
from app.agents.models import TaskRequest, TaskResponse
from app.agents.orchestrator import Orchestrator
from app.agents.registry import AgentRegistry
from app.agents.review import ReviewAgent
from app.company.storage import get_company_context, load_profile

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


def _enrich_with_company_context(request: TaskRequest) -> TaskRequest:
    """Inject saved company profile context into the request if available."""
    company_context = get_company_context()
    if company_context is None:
        return request

    profile = load_profile()
    if profile is None:
        return request

    data = request.model_dump()
    data["context"] = {**data.get("context", {}), "company_profile": company_context}

    if not data.get("startup_idea") and profile.description:
        data["startup_idea"] = f"{profile.name}: {profile.description}"
    if not data.get("target_audience") and profile.target_audience:
        data["target_audience"] = profile.target_audience

    return TaskRequest.model_validate(data)


@router.post("", response_model=TaskResponse)
def create_task(request: TaskRequest) -> TaskResponse:
    enriched = _enrich_with_company_context(request)
    return get_orchestrator().handle_task(enriched)


@router.post("/upload", response_model=TaskResponse)
async def create_task_with_upload(
    prompt: str = Form(...),
    startup_idea: str = Form(default=""),
    target_audience: str = Form(default=""),
    goal: str = Form(default=""),
    tone: str = Form(default=""),
    channel: str = Form(default=""),
    jurisdictions: str = Form(default="US"),
    industries: str = Form(default=""),
    startup_url: str = Form(default=""),
    review_mode: bool = Form(default=False),
    document: UploadFile | None = File(default=None),
) -> TaskResponse:
    uploaded_doc_text: str | None = None
    if document is not None:
        raw = await document.read()
        uploaded_doc_text = raw.decode("utf-8", errors="replace")

    jurisdiction_list = [j.strip() for j in jurisdictions.split(",") if j.strip()]
    industry_list = [i.strip() for i in industries.split(",") if i.strip()]

    request = TaskRequest(
        prompt=prompt,
        startup_idea=startup_idea or None,
        target_audience=target_audience or None,
        goal=goal or None,
        tone=tone or None,
        channel=channel or None,
        jurisdictions=jurisdiction_list or ["US"],
        industries=industry_list,
        uploaded_doc_text=uploaded_doc_text,
        startup_url=startup_url or None,
        review_mode=review_mode,
    )
    enriched = _enrich_with_company_context(request)
    return get_orchestrator().handle_task(enriched)
