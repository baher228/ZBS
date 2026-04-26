from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from app.live_demo.models import LiveDemoSession
from app.live_demo.runtime import LiveDemoRuntime
from app.live_demo.setup_store import live_demo_setup_store
from app.live_demo.store import LiveDemoSessionStore
from app.live_demo.voice_bridge import GeminiLiveDemoVoiceBridge


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_json(self, payload: dict[str, Any]) -> None:
        self.messages.append(payload)


class FakeGeminiSession:
    def __init__(self) -> None:
        self.realtime_inputs: list[str] = []

    async def send_realtime_input(self, *, text: str | None = None, **_: Any) -> None:
        if text:
            self.realtime_inputs.append(text)


@pytest.fixture()
def voice_bridge() -> tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession]:
    live_demo_setup_store.clear()
    manifest = live_demo_setup_store.ensure_default_setup().manifest
    store = LiveDemoSessionStore()
    session: LiveDemoSession = store.create(
        startup_id=manifest.startup_id,
        current_page_id=manifest.pages[0].page_id,
    )
    websocket = FakeWebSocket()
    gemini_session = FakeGeminiSession()
    bridge = GeminiLiveDemoVoiceBridge(
        websocket=websocket,  # type: ignore[arg-type]
        runtime=LiveDemoRuntime(store=store, manifest=manifest),
        store=store,
        session_id=session.id,
    )
    return bridge, websocket, gemini_session


@pytest.mark.anyio
async def test_voice_step_done_advances_one_manifest_step(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    assert first["ok"] is True
    assert first["step_index"] == 0
    assert first["has_next"] is True
    assert websocket.messages[-1]["type"] == "demo_response"

    first_flow_state = websocket.messages[-1]["flow_state"]
    await bridge._handle_voice_step_done(gemini_session, first_flow_state)

    second_response = websocket.messages[-1]
    assert second_response["type"] == "demo_response"
    assert second_response["flow_state"]["step_index"] == 1
    assert second_response["session"]["current_page_id"] != first["current_page_id"]
    assert gemini_session.realtime_inputs


@pytest.mark.anyio
async def test_interruption_question_then_continue_resumes_next_step(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    await bridge._handle_client_json(gemini_session, {"type": "interrupt"})
    await bridge._execute_tool(
        "answer_with_visuals",
        {"question": "How does the agent know what it can click?"},
    )
    resumed = await bridge._execute_tool("continue_demo_flow", {})

    assert resumed["ok"] is True
    assert resumed["step_index"] == 0
    assert resumed["step_id"] == first["step_id"]
    assert websocket.messages[-1]["flow_state"]["step_index"] == 0


@pytest.mark.anyio
async def test_direct_interrupt_then_continue_replays_interrupted_step(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    await bridge._handle_client_json(gemini_session, {"type": "interrupt"})
    resumed = await bridge._execute_tool("continue_demo_flow", {})

    assert resumed["ok"] is True
    assert resumed["step_index"] == first["step_index"]
    assert resumed["step_id"] == first["step_id"]
    assert websocket.messages[-1]["flow_state"]["step_token"] != websocket.messages[0].get(
        "flow_state", {}
    ).get("step_token")


@pytest.mark.anyio
async def test_stale_step_done_after_interrupt_does_not_advance(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    first_flow_state = websocket.messages[-1]["flow_state"]
    await bridge._handle_client_json(gemini_session, {"type": "interrupt"})
    message_count = len(websocket.messages)

    await bridge._handle_voice_step_done(
        gemini_session,
        {
            "flow_id": first["flow_id"],
            "step_id": first["step_id"],
            "step_index": first["step_index"],
            "step_token": first_flow_state["step_token"],
        },
    )

    assert len(websocket.messages) == message_count


@pytest.mark.anyio
async def test_stale_step_done_with_missing_token_does_not_advance(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    message_count = len(websocket.messages)

    await bridge._handle_voice_step_done(
        gemini_session,
        {
            "flow_id": first["flow_id"],
            "step_id": first["step_id"],
            "step_index": first["step_index"],
        },
    )

    assert len(websocket.messages) == message_count


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("flow_id", "wrong_flow"),
        ("step_id", "wrong_step"),
        ("step_index", 99),
        ("step_token", "wrong_token"),
    ],
)
async def test_stale_step_done_with_wrong_identity_does_not_advance(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
    field: str,
    value: object,
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    await bridge._execute_tool("start_demo_flow", {})
    flow_state = dict(websocket.messages[-1]["flow_state"])
    flow_state[field] = value
    message_count = len(websocket.messages)

    await bridge._handle_voice_step_done(gemini_session, flow_state)

    assert len(websocket.messages) == message_count


@pytest.mark.anyio
async def test_replayed_valid_step_done_does_not_advance_again(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, gemini_session = voice_bridge

    await bridge._execute_tool("start_demo_flow", {})
    flow_state = dict(websocket.messages[-1]["flow_state"])
    await bridge._handle_voice_step_done(gemini_session, flow_state)
    message_count = len(websocket.messages)

    await bridge._handle_voice_step_done(gemini_session, flow_state)

    assert len(websocket.messages) == message_count


@pytest.mark.anyio
async def test_specific_page_question_pauses_flow_for_resume(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, websocket, _gemini_session = voice_bridge

    first = await bridge._execute_tool("start_demo_flow", {})
    await bridge._execute_tool("show_relevant_page", {"query": "Show the prospect demo room"})
    resumed = await bridge._execute_tool("continue_demo_flow", {})

    assert resumed["step_index"] == first["step_index"]
    assert websocket.messages[-1]["flow_state"]["step_id"] == first["step_id"]


@pytest.mark.anyio
async def test_transcript_fallback_prompts_gemini_without_advancing_visuals(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bridge, websocket, gemini_session = voice_bridge
    bridge.last_input_transcript = "Walk me through the app setup"

    async def no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    await bridge._transcript_fallback_after_delay(
        gemini_session,
        bridge.last_input_transcript,
    )

    assert gemini_session.realtime_inputs
    assert "call start_demo_flow" in gemini_session.realtime_inputs[-1]
    assert not any(message.get("type") == "demo_response" for message in websocket.messages)


def test_audio_chunks_prefer_inline_model_turn_parts(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, _websocket, _gemini_session = voice_bridge
    response = SimpleNamespace(data=b"fallback")
    server_content = SimpleNamespace(
        model_turn=SimpleNamespace(
            parts=[
                SimpleNamespace(inline_data=SimpleNamespace(data=b"one")),
                SimpleNamespace(inline_data=SimpleNamespace(data=b"two")),
            ]
        )
    )

    assert bridge._audio_chunks_from_response(response, server_content) == [b"one", b"two"]


def test_audio_chunks_fall_back_to_response_data(
    voice_bridge: tuple[GeminiLiveDemoVoiceBridge, FakeWebSocket, FakeGeminiSession],
) -> None:
    bridge, _websocket, _gemini_session = voice_bridge
    response = SimpleNamespace(data=b"fallback")
    server_content = SimpleNamespace(model_turn=SimpleNamespace(parts=[]))

    assert bridge._audio_chunks_from_response(response, server_content) == [b"fallback"]
