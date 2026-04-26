from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, File, Form, UploadFile

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.image_gen import generate_image
from app.agents.legal import LegalAgent
from app.agents.llm import get_llm_provider
from app.agents.models import SocialPostRequest, SocialPostResponse, TaskRequest, TaskResponse
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
    """Inject saved company profile context and social media insights into the request."""
    company_context = get_company_context()
    if company_context is None:
        return request

    profile = load_profile()
    if profile is None:
        return request

    data = request.model_dump()
    data["context"] = {**data.get("context", {}), "company_profile": company_context}

    if profile.social_media_links:
        from app.agents.social_insights import extract_social_insights

        insights = extract_social_insights(
            profile.social_media_links,
            company_context=company_context,
        )
        insights_block = insights.to_context_block()
        if insights_block:
            data["context"]["social_insights"] = insights_block

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
    additional_context: str = Form(default=""),
    document_type: str = Form(default=""),
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
        additional_context=additional_context or None,
        document_type=document_type or None,
    )
    enriched = _enrich_with_company_context(request)
    return get_orchestrator().handle_task(enriched)


@router.post("/social-post", response_model=SocialPostResponse)
def create_social_post(request: SocialPostRequest) -> SocialPostResponse:
    llm = get_llm_provider()
    company_context = get_company_context() or ""

    post = llm.generate_social_post(request, company_context)

    images: list[str] = []
    if request.num_images > 0:
        from app.agents.image_gen import _build_contextual_prompt

        caption = post.caption or request.topic
        prompt = _build_contextual_prompt(
            section=f"{request.platform}_post",
            section_text=caption,
            company_context=company_context,
        )
        for _ in range(request.num_images):
            img = generate_image(prompt, "social_post")
            if img:
                images.append(img.url)

    return SocialPostResponse(
        post=post.as_output_dict(),
        images=images,
        platform=request.platform,
    )
