from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, WebSocket

from app.live_demo.models import (
    DemoManifest,
    DemoSetup,
    DemoSetupApproveRequest,
    DemoSetupCreateRequest,
    LiveDemoMessageRequest,
    LiveDemoMessageResponse,
    LiveDemoSession,
    LiveDemoSessionCreateRequest,
)
from app.live_demo.runtime import LiveDemoRuntime
from app.live_demo.setup_store import live_demo_setup_store
from app.live_demo.store import live_demo_session_store
from app.live_demo.voice_bridge import GeminiLiveDemoVoiceBridge

router = APIRouter(tags=["live-demo"])


def get_live_demo_runtime(manifest: DemoManifest) -> LiveDemoRuntime:
    return LiveDemoRuntime(store=live_demo_session_store, manifest=manifest)


@router.post("/live-demo/setups", response_model=DemoSetup)
def create_live_demo_setup(request: DemoSetupCreateRequest) -> DemoSetup:
    try:
        return live_demo_setup_store.create(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/live-demo/setups/{startup_id}", response_model=DemoSetup)
def get_live_demo_setup(startup_id: str) -> DemoSetup:
    setup = live_demo_setup_store.get(startup_id)
    if setup is None:
        raise HTTPException(status_code=404, detail="Unknown startup demo setup")
    return setup


@router.post("/live-demo/setups/{startup_id}/approve", response_model=DemoSetup)
def approve_live_demo_setup(
    startup_id: str,
    request: DemoSetupApproveRequest,
) -> DemoSetup:
    setup = live_demo_setup_store.approve(startup_id, approved=request.approved)
    if setup is None:
        raise HTTPException(status_code=404, detail="Unknown startup demo setup")
    return setup


@router.get("/live-demo/manifest", response_model=DemoManifest)
def get_live_demo_manifest(startup_id: str | None = Query(default=None)) -> DemoManifest:
    try:
        return live_demo_setup_store.manifest_for(startup_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown startup demo setup") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="Demo setup is not approved") from exc


@router.post("/live-demo/sessions", response_model=LiveDemoSession)
def create_live_demo_session(request: LiveDemoSessionCreateRequest) -> LiveDemoSession:
    manifest = get_live_demo_manifest(request.startup_id)
    startup_id = request.startup_id or manifest.startup_id
    current_page_id = request.current_page_id or manifest.pages[0].page_id
    if current_page_id not in {page.page_id for page in manifest.pages}:
        raise HTTPException(status_code=400, detail="Unknown page id")
    return live_demo_session_store.create(
        startup_id=startup_id,
        current_page_id=current_page_id,
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
    manifest = get_live_demo_manifest(session.startup_id)
    return get_live_demo_runtime(manifest).handle_message(session, request)


@router.websocket("/live-demo/sessions/{session_id}/voice")
async def live_demo_voice(session_id: str, websocket: WebSocket) -> None:
    session = live_demo_session_store.get(session_id)
    if session is None:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Live demo session not found"})
        await websocket.close(code=1008)
        return
    try:
        manifest = get_live_demo_manifest(session.startup_id)
    except HTTPException as exc:
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": str(exc.detail)})
        await websocket.close(code=1008)
        return
    bridge = GeminiLiveDemoVoiceBridge(
        websocket=websocket,
        runtime=get_live_demo_runtime(manifest),
        store=live_demo_session_store,
        session_id=session_id,
    )
    await bridge.run()
