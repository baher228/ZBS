"""Dashboard API — aggregates real project data for the frontend dashboard."""
from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from app.agents.llm import get_last_llm_error
from app.company.context_store import load_chat_context, load_website_context
from app.company.storage import load_profile
from app.core.config import settings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# ── Response models ─────────────────────────────────────────


class CompanySummary(BaseModel):
    has_profile: bool = False
    name: str = ""
    description: str = ""
    industry: str = ""
    stage: str = ""
    website: str = ""
    jurisdictions: list[str] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list)
    differentiators: str = ""
    target_audience: str = ""
    social_links_count: int = 0


class ContextStatus(BaseModel):
    website_parsed: bool = False
    website_url: str = ""
    pages_count: int = 0
    company_summary: str = ""
    insights_count: int = 0
    insights_by_agent: dict[str, int] = Field(default_factory=dict)


class ProviderStatus(BaseModel):
    provider: str = "mock"
    model: str = ""
    status: str = "offline"
    last_error: str | None = None


class AgentInfo(BaseModel):
    name: str
    slug: str
    description: str
    status: str = "live"


class DashboardResponse(BaseModel):
    company: CompanySummary
    context: ContextStatus
    provider: ProviderStatus
    agents: list[AgentInfo]


# ── Endpoint ────────────────────────────────────────────────


AGENTS = [
    AgentInfo(
        name="Legal Agent",
        slug="legal",
        description="Legal advice, tax guidance, and document drafting with jurisdiction-aware knowledge base.",
    ),
    AgentInfo(
        name="Content Creator",
        slug="content",
        description="Social posts, emails, landing pages, and blog posts with creative AI generation.",
    ),
    AgentInfo(
        name="Marketing Research",
        slug="marketing-research",
        description="Competitor analysis, market sizing, audience research, and trend intelligence.",
    ),
]


@router.get("", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    # Company profile
    profile = load_profile()
    company = CompanySummary()
    if profile is not None:
        company = CompanySummary(
            has_profile=True,
            name=profile.name,
            description=profile.description,
            industry=profile.industry,
            stage=profile.stage,
            website=profile.website,
            jurisdictions=profile.jurisdictions,
            key_features=profile.key_features,
            differentiators=profile.differentiators,
            target_audience=profile.target_audience,
            social_links_count=sum(1 for v in profile.social_media_links.values() if v),
        )

    # Context enrichment
    context = ContextStatus()
    website = load_website_context()
    if website is not None:
        context.website_parsed = True
        context.website_url = website.source_url
        context.pages_count = len(website.pages)
        context.company_summary = website.company_summary[:300]

    chat = load_chat_context()
    context.insights_count = len(chat.insights)
    agent_counts: dict[str, int] = {}
    for insight in chat.insights:
        agent_counts[insight.source_agent] = agent_counts.get(insight.source_agent, 0) + 1
    context.insights_by_agent = agent_counts

    # Provider
    provider = ProviderStatus(
        provider=settings.resolved_llm_provider,
        model=settings.resolved_llm_model,
        status="online" if settings.resolved_llm_provider != "mock" else "mock",
        last_error=get_last_llm_error(),
    )

    return DashboardResponse(
        company=company,
        context=context,
        provider=provider,
        agents=AGENTS,
    )
