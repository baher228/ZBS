from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.agents.campaign_models import (
    CampaignCreateRequest,
    CampaignResponse,
    ChatRequest,
    ChatResponse,
    DemoRoom,
    QualificationReport,
)
from app.agents.graphs import CampaignGraphRunner, DemoChatGraphRunner, QualificationGraphRunner
from app.agents.llm import get_llm_provider
from app.agents.store import campaign_store

router = APIRouter(tags=["campaigns"])


@lru_cache
def get_campaign_graph_runner() -> CampaignGraphRunner:
    return CampaignGraphRunner(llm_provider=get_llm_provider(), store=campaign_store)


@lru_cache
def get_demo_chat_graph_runner() -> DemoChatGraphRunner:
    return DemoChatGraphRunner(llm_provider=get_llm_provider(), store=campaign_store)


@lru_cache
def get_qualification_graph_runner() -> QualificationGraphRunner:
    return QualificationGraphRunner(llm_provider=get_llm_provider(), store=campaign_store)


@router.post("/campaigns", response_model=CampaignResponse)
def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    return get_campaign_graph_runner().run(request)


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str) -> CampaignResponse:
    campaign = campaign_store.get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/demo-rooms/{demo_room_id}", response_model=DemoRoom)
def get_demo_room(demo_room_id: str) -> DemoRoom:
    demo_room = campaign_store.get_demo_room(demo_room_id)
    if demo_room is None:
        raise HTTPException(status_code=404, detail="Demo room not found")
    return demo_room


@router.post("/demo-rooms/{demo_room_id}/chat", response_model=ChatResponse)
def chat_with_demo_room(demo_room_id: str, request: ChatRequest) -> ChatResponse:
    return get_demo_chat_graph_runner().run(demo_room_id, request.message)


@router.post("/demo-rooms/{demo_room_id}/qualify", response_model=QualificationReport)
def qualify_demo_room(demo_room_id: str) -> QualificationReport:
    return get_qualification_graph_runner().run(demo_room_id)
