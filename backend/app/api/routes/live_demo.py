from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, HTTPException

from app.live_demo.manifest import DEMO_MANIFEST
from app.live_demo.models import (
    DemoManifest,
    LiveDemoMessageRequest,
    LiveDemoMessageResponse,
    LiveDemoSession,
    LiveDemoSessionCreateRequest,
)
from app.live_demo.runtime import LiveDemoRuntime
from app.live_demo.store import live_demo_session_store

router = APIRouter(tags=["live-demo"])


@lru_cache
def get_live_demo_runtime() -> LiveDemoRuntime:
    return LiveDemoRuntime(store=live_demo_session_store)


@router.get("/live-demo/manifest", response_model=DemoManifest)
def get_live_demo_manifest() -> DemoManifest:
    return DEMO_MANIFEST


@router.post("/live-demo/sessions", response_model=LiveDemoSession)
def create_live_demo_session(request: LiveDemoSessionCreateRequest) -> LiveDemoSession:
    if request.startup_id != DEMO_MANIFEST.startup_id:
        raise HTTPException(status_code=400, detail="Unknown startup demo manifest")
    if request.current_page_id not in {page.page_id for page in DEMO_MANIFEST.pages}:
        raise HTTPException(status_code=400, detail="Unknown page id")
    return live_demo_session_store.create(
        startup_id=request.startup_id,
        current_page_id=request.current_page_id,
    )


@router.get("/live-demo/sessions/{session_id}", response_model=LiveDemoSession)
def get_live_demo_session(session_id: str) -> LiveDemoSession:
    session = live_demo_session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Live demo session not found")
    return session


@router.post("/live-demo/sessions/{session_id}/message", response_model=LiveDemoMessageResponse)
def send_live_demo_message(
    session_id: str,
    request: LiveDemoMessageRequest,
) -> LiveDemoMessageResponse:
    session = live_demo_session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Live demo session not found")
    return get_live_demo_runtime().handle_message(session, request)
