from __future__ import annotations

import asyncio
import base64
import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types

from app.core.config import settings
from app.live_demo.models import (
    ConversationTurn,
    DemoEvent,
    DemoFlow,
    DemoFlowStep,
    DemoPageManifest,
    LiveDemoMessageRequest,
    LiveDemoMessageResponse,
    new_id,
)
from app.live_demo.runtime import LiveDemoRuntime
from app.live_demo.store import LiveDemoSessionStore


SEND_AUDIO_MIME = "audio/pcm;rate=16000"
RECEIVE_AUDIO_MIME = "audio/pcm;rate=24000"


class GeminiLiveDemoVoiceBridge:
    def __init__(
        self,
        *,
        websocket: WebSocket,
        runtime: LiveDemoRuntime,
        store: LiveDemoSessionStore,
        session_id: str,
    ) -> None:
        self.websocket = websocket
        self.runtime = runtime
        self.store = store
        self.session_id = session_id
        self.current_page_id: str | None = None
        self.visible_element_ids: list[str] = []
        self.last_input_transcript = ""
        self.audio_chunk_count = 0
        self.audio_byte_count = 0
        self.active_flow: DemoFlow | None = None
        self.active_flow_step_index = 0
        self.transcript_task: asyncio.Task | None = None
        self.last_handled_transcript = ""
        self.pending_flow_step: dict[str, Any] | None = None
        self.flow_interrupted = False
        self.paused_flow: DemoFlow | None = None
        self.paused_flow_step_index: int | None = None

    async def run(self) -> None:
        await self.websocket.accept()
        if not settings.gemini_live_enabled:
            await self._send_error("Gemini Live is disabled")
            await self.websocket.close(code=1013)
            return
        if not settings.gemini_api_key:
            await self._send_error("GEMINI_API_KEY is not configured")
            await self.websocket.close(code=1013)
            return

        client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=settings.gemini_api_key,
        )
        try:
            async with client.aio.live.connect(
                model=settings.gemini_live_model,
                config=self._live_config(),
            ) as gemini_session:
                await self.websocket.send_json(
                    {
                        "type": "voice.ready",
                        "model": settings.gemini_live_model,
                        "audio_input": SEND_AUDIO_MIME,
                        "audio_output": RECEIVE_AUDIO_MIME,
                    }
                )
                async with asyncio.TaskGroup() as task_group:
                    task_group.create_task(self._receive_client(gemini_session))
                    task_group.create_task(self._receive_gemini(gemini_session))
        except asyncio.CancelledError:
            raise
        except WebSocketDisconnect:
            return
        except Exception as exc:
            try:
                await self._send_error(f"Gemini Live bridge failed: {exc}")
            except RuntimeError:
                return

    def _live_config(self) -> types.LiveConnectConfig:
        return types.LiveConnectConfig(
            responseModalities=[types.Modality.AUDIO],
            systemInstruction=self._system_instruction(),
            tools=[
                types.Tool(
                    functionDeclarations=[
                        self._function_declaration(
                            "start_demo_flow",
                            "Start the approved product walkthrough for the current demo manifest.",
                            {
                                "type": "object",
                                "properties": {
                                    "reason": {
                                        "type": "string",
                                        "description": "Why the user wants the full walkthrough.",
                                    }
                                },
                            },
                        ),
                        self._function_declaration(
                            "show_relevant_page",
                            "Show the most relevant approved product page and highlights for a user request.",
                            {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The user request to route to an approved page.",
                                    }
                                },
                                "required": ["query"],
                            },
                        ),
                        self._function_declaration(
                            "continue_demo_flow",
                            "Continue to the next step in the active product walkthrough.",
                            {"type": "object", "properties": {}},
                        ),
                        self._function_declaration(
                            "answer_with_visuals",
                            "Answer a user question and show any relevant approved page/highlights.",
                            {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "The user question to answer from approved demo context.",
                                    }
                                },
                                "required": ["question"],
                            },
                        ),
                        self._function_declaration(
                            "get_demo_context",
                            "Fetch the current approved page index, flow names, and CTA for orientation.",
                            {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "Optional topic to focus the context.",
                                    }
                                },
                            },
                        ),
                        self._function_declaration(
                            "pause_demo_flow",
                            "Pause the current local visual playback when the user interrupts.",
                            {"type": "object", "properties": {}},
                        ),
                    ]
                )
            ],
            speechConfig=types.SpeechConfig(
                voiceConfig=types.VoiceConfig(
                    prebuiltVoiceConfig=types.PrebuiltVoiceConfig(
                        voiceName=settings.gemini_live_voice
                    )
                )
            ),
            inputAudioTranscription=types.AudioTranscriptionConfig(),
            outputAudioTranscription=types.AudioTranscriptionConfig(),
            thinkingConfig=types.ThinkingConfig(thinkingLevel=types.ThinkingLevel.LOW),
            contextWindowCompression=types.ContextWindowCompressionConfig(
                triggerTokens=100_000,
                slidingWindow=types.SlidingWindow(targetTokens=50_000),
            ),
        )

    def _function_declaration(
        self,
        name: str,
        description: str,
        parameters_json_schema: dict[str, Any],
    ) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=name,
            description=description,
            parametersJsonSchema=parameters_json_schema,
        )

    def _system_instruction(self) -> str:
        manifest = self.runtime.manifest
        flow_names = ", ".join(flow.name for flow in manifest.flows) or "primary walkthrough"
        page_index = ", ".join(f"{page.page_id} ({page.title})" for page in manifest.pages)
        product_context = self._business_intro()
        return (
            f"You are the realtime AI guide inside a {manifest.product_name} demo room. "
            f"Approved product purpose: {product_context}. "
            f"Be clear that {manifest.product_name} is the product being shown, and the demo "
            "agent is one capability inside that product. Your job is to greet the prospect, "
            "answer questions, and show the product through approved demo tools. Sound like "
            "a human product specialist, not a script reader. "
            "When greeting or giving a tour, first explain the business problem the product solves "
            "and the outcome it creates. Then use the UI as evidence. "
            "Connect highlighted UI labels to the business story naturally, but do not say "
            "phrases like 'I am pointing at' or 'I am highlighting'. Keep each step to two "
            "short spoken sentences unless the user asks for more detail. Do not claim unsupported pricing, "
            "security, integrations, customer logos, or roadmap items. "
            "When the user asks for a tour, setup walkthrough, or to be shown around, call "
            "start_demo_flow. That tool returns one visual step at a time. Do not call "
            "continue_demo_flow after finishing speech; the browser will notify the backend "
            "when audio and visuals are finished, and the backend will provide the next "
            "validated step for you to narrate. Only call continue_demo_flow when the user "
            "explicitly asks to resume after an interruption. When the user asks to see a "
            "specific part, call show_relevant_page. "
            "When the user asks a product question that benefits from visuals, call answer_with_visuals. "
            "Use pause_demo_flow if the user interrupts an active walkthrough. "
            "Do not call low-level cursor or highlight tools; the frontend plays validated timelines. "
            f"Approved flows: {flow_names}. Approved pages: {page_index}. CTA: {manifest.cta}."
        )

    async def _receive_client(self, gemini_session: Any) -> None:
        while True:
            try:
                message = await self.websocket.receive()
            except (RuntimeError, WebSocketDisconnect):
                return
            if text := message.get("text"):
                await self._handle_client_json(gemini_session, json.loads(text))
            elif data := message.get("bytes"):
                await self._record_audio_received(len(data))
                await gemini_session.send_realtime_input(
                    audio=types.Blob(data=data, mimeType=SEND_AUDIO_MIME)
                )

    async def _handle_client_json(self, gemini_session: Any, payload: dict[str, Any]) -> None:
        event_type = payload.get("type")
        if event_type == "audio":
            raw = base64.b64decode(str(payload.get("data") or ""))
            await self._record_audio_received(len(raw))
            await gemini_session.send_realtime_input(
                audio=types.Blob(
                    data=raw,
                    mimeType=str(payload.get("mime_type") or SEND_AUDIO_MIME),
                )
            )
        elif event_type == "text":
            message = str(payload.get("message") or payload.get("text") or "").strip()
            if message:
                await gemini_session.send_realtime_input(text=message)
        elif event_type == "page_state":
            self.current_page_id = payload.get("current_page_id") or self.current_page_id
            visible = payload.get("visible_element_ids")
            if isinstance(visible, list):
                self.visible_element_ids = [str(item) for item in visible]
        elif event_type == "interrupt":
            self.flow_interrupted = True
            self._pause_active_flow(resume_next=False)
            self.active_flow = None
            self.pending_flow_step = None
            await self.websocket.send_json({"type": "interrupted"})
        elif event_type == "voice_step_done":
            await self._handle_voice_step_done(gemini_session, payload)
        elif event_type == "audio_stream_end":
            await gemini_session.send_realtime_input(audio_stream_end=True)
        elif event_type == "stop":
            await gemini_session.send_realtime_input(audio_stream_end=True)
            await self.websocket.close(code=1000)

    async def _record_audio_received(self, byte_count: int) -> None:
        self.audio_chunk_count += 1
        self.audio_byte_count += byte_count
        if self.audio_chunk_count == 1 or self.audio_chunk_count % 25 == 0:
            await self.websocket.send_json(
                {
                    "type": "audio.received",
                    "chunks": self.audio_chunk_count,
                    "bytes": self.audio_byte_count,
                }
            )

    async def _receive_gemini(self, gemini_session: Any) -> None:
        while True:
            async for response in gemini_session.receive():
                server_content = getattr(response, "server_content", None)
                if getattr(server_content, "interrupted", False):
                    self.flow_interrupted = True
                    self._pause_active_flow(resume_next=False)
                    self.active_flow = None
                    self.pending_flow_step = None
                    await self.websocket.send_json({"type": "interrupted"})

                audio_chunks = self._audio_chunks_from_response(response, server_content)
                if audio_chunks:
                    self._cancel_transcript_fallback(mark_handled=True)
                for audio_chunk in audio_chunks:
                    await self._send_audio_chunk(audio_chunk)

                if getattr(server_content, "generation_complete", False):
                    await self.websocket.send_json({"type": "voice.generation_complete"})
                if getattr(server_content, "turn_complete", False):
                    await self.websocket.send_json(
                        {
                            "type": "voice.turn_complete",
                            "reason": str(
                                getattr(server_content, "turn_complete_reason", "") or ""
                            ),
                        }
                    )

                input_transcription = getattr(server_content, "input_transcription", None)
                if input_transcription and getattr(input_transcription, "text", None):
                    self.last_input_transcript = input_transcription.text
                    await self.websocket.send_json(
                        {"type": "input_transcript", "text": input_transcription.text}
                    )
                    self._schedule_transcript_fallback(gemini_session, input_transcription.text)

                output_transcription = getattr(server_content, "output_transcription", None)
                if output_transcription and getattr(output_transcription, "text", None):
                    self._cancel_transcript_fallback(mark_handled=True)
                    await self.websocket.send_json(
                        {"type": "output_transcript", "text": output_transcription.text}
                    )

                if text := getattr(response, "text", None):
                    self._cancel_transcript_fallback(mark_handled=True)
                    await self.websocket.send_json({"type": "output_transcript", "text": text})

                tool_call = getattr(response, "tool_call", None)
                if tool_call:
                    self._cancel_transcript_fallback(mark_handled=True)
                    function_responses = []
                    for function_call in tool_call.function_calls:
                        result = await self._execute_tool(
                            function_call.name, function_call.args or {}
                        )
                        function_responses.append(
                            types.FunctionResponse(
                                id=function_call.id,
                                name=function_call.name,
                                response=result,
                            )
                        )
                    await gemini_session.send_tool_response(
                        function_responses=function_responses
                    )

    def _audio_chunks_from_response(
        self,
        response: Any,
        server_content: Any,
    ) -> list[bytes]:
        chunks: list[bytes] = []
        model_turn = getattr(server_content, "model_turn", None)
        for part in getattr(model_turn, "parts", []) or []:
            inline_data = getattr(part, "inline_data", None)
            data = getattr(inline_data, "data", None)
            if isinstance(data, bytes):
                chunks.append(data)
        if chunks:
            return chunks
        data = getattr(response, "data", None)
        return [data] if isinstance(data, bytes) else []

    async def _send_audio_chunk(self, data: bytes) -> None:
        await self.websocket.send_json(
            {
                "type": "audio",
                "mime_type": RECEIVE_AUDIO_MIME,
                "data": base64.b64encode(data).decode("ascii"),
            }
        )

    def _cancel_transcript_fallback(self, *, mark_handled: bool) -> None:
        if self.transcript_task and not self.transcript_task.done():
            self.transcript_task.cancel()
        if mark_handled and self.last_input_transcript:
            self.last_handled_transcript = self.last_input_transcript

    async def _execute_tool(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        if self.last_input_transcript:
            self.last_handled_transcript = self.last_input_transcript
        if name == "get_demo_context":
            return self._demo_context(args.get("query"))
        if name == "pause_demo_flow":
            self._pause_active_flow(resume_next=False)
            self.active_flow = None
            self.pending_flow_step = None
            self.flow_interrupted = True
            await self.websocket.send_json({"type": "playback.pause"})
            return {
                "ok": True,
                "summary": "Paused local visual playback.",
                "can_resume": self.paused_flow is not None,
            }
        if name == "start_demo_flow":
            self.active_flow = self.runtime.primary_flow()
            self.active_flow_step_index = 0
            self.paused_flow = None
            self.paused_flow_step_index = None
            self.flow_interrupted = False
            return await self._execute_flow_step()
        if name == "continue_demo_flow":
            if self.pending_flow_step is not None and not self.flow_interrupted:
                return {
                    "ok": True,
                    "waiting": True,
                    "waiting_for_step_id": self.pending_flow_step.get("step_id"),
                    "instruction": (
                        "Do not speak, apologize, or describe this waiting state. "
                        "The browser will request the next step after the current audio "
                        "and visuals finish."
                    ),
                }
            if self.paused_flow is not None and self.paused_flow_step_index is not None:
                self.active_flow = self.paused_flow
                self.active_flow_step_index = self.paused_flow_step_index
                self.paused_flow = None
                self.paused_flow_step_index = None
                self.flow_interrupted = False
                return await self._execute_flow_step()
            if self.active_flow is None:
                return {"ok": False, "error": "No active or paused demo flow to continue."}
            self.flow_interrupted = False
            self.active_flow_step_index += 1
            return await self._execute_flow_step()
        if name == "show_relevant_page":
            self._pause_active_flow(resume_next=False)
            self.active_flow = None
            self.pending_flow_step = None
            prompt = str(args.get("query") or self.last_input_transcript or "Show the relevant page")
        elif name == "answer_with_visuals":
            self._pause_active_flow(resume_next=False)
            self.active_flow = None
            self.pending_flow_step = None
            prompt = str(args.get("question") or self.last_input_transcript or "Answer this question")
        else:
            return {"ok": False, "error": f"Unknown tool: {name}"}

        response = self._handle_runtime_message(prompt)
        events = self._visual_events_only(response.events)
        await self._send_demo_response(response, events)
        return {
            "ok": True,
            "reply": response.reply,
            "current_page_id": response.session.current_page_id,
            "event_count": len(events),
            "instruction": "Say the reply now. The browser is playing the validated visual events.",
        }

    async def _execute_flow_step(self) -> dict[str, Any]:
        flow = self.active_flow
        if flow is None or not flow.steps:
            self.pending_flow_step = None
            return {"ok": False, "error": "No approved flow is available."}
        if self.active_flow_step_index >= len(flow.steps):
            self.active_flow = None
            self.pending_flow_step = None
            self.paused_flow = None
            self.paused_flow_step_index = None
            return {
                "ok": True,
                "done": True,
                "reply": f"That completes the {flow.name} walkthrough. {self.runtime.manifest.cta}.",
                "has_next": False,
                "instruction": "Say the reply and ask what the prospect wants to see next.",
            }

        step = flow.steps[self.active_flow_step_index]
        page = self._page_by_id(step.page_id)
        if page is None:
            return {"ok": False, "error": f"Flow step page not found: {step.page_id}"}

        events = self._flow_step_events(page, step)
        element_summaries = self._highlighted_element_summaries(page, events)
        reply = self._voice_step_reply(
            flow=flow,
            step=step,
            page=page,
            events=events,
            element_summaries=element_summaries,
        )
        response = self._persist_voice_step(reply, page, events)
        has_next = self.active_flow_step_index < len(flow.steps) - 1
        flow_state = {
            "flow_id": flow.id,
            "step_id": step.id,
            "step_index": self.active_flow_step_index,
            "step_token": new_id("step"),
            "has_next": has_next,
        }
        self.pending_flow_step = flow_state if has_next else None
        await self._send_demo_response(response, events, flow_state=flow_state)
        if not has_next:
            self.active_flow = None
            self.paused_flow = None
            self.paused_flow_step_index = None
        return {
            "ok": True,
            "reply": reply,
            "flow_id": flow.id,
            "step_id": step.id,
            "step_index": self.active_flow_step_index,
            "has_next": has_next,
            "current_page_id": page.page_id,
            "event_count": len(events),
            "highlighted_elements": element_summaries,
            "instruction": (
                "Say the reply now in a natural product-demo tone. "
                + ("Wait for the browser to finish this step before continuing." if has_next else "Ask what the prospect wants to see next.")
            ),
        }

    async def _handle_voice_step_done(
        self,
        gemini_session: Any,
        payload: dict[str, Any],
    ) -> None:
        pending = self.pending_flow_step
        if not pending or self.flow_interrupted:
            return
        if payload.get("step_id") != pending.get("step_id"):
            return
        if payload.get("flow_id") != pending.get("flow_id"):
            return
        if payload.get("step_index") != pending.get("step_index"):
            return
        if payload.get("step_token") != pending.get("step_token"):
            return
        if self.active_flow is None or not pending.get("has_next"):
            self.pending_flow_step = None
            return

        self.pending_flow_step = None
        self.active_flow_step_index += 1
        result = await self._execute_flow_step()
        if result.get("ok") and result.get("reply"):
            await gemini_session.send_realtime_input(
                text=(
                    "The previous visual step finished and the user did not interrupt. "
                    "Continue the product walkthrough for the prospect. Say only a natural "
                    "user-facing narration for the next step; do not mention instructions, "
                    "tools, validation, or highlighted UI context. "
                    f"Next-step narration: {result['reply']}"
                )
            )

    def _schedule_transcript_fallback(self, gemini_session: Any, transcript: str) -> None:
        cleaned = transcript.strip()
        if len(cleaned) < 3 or cleaned == self.last_handled_transcript:
            return
        if self.transcript_task and not self.transcript_task.done():
            self.transcript_task.cancel()
        self.transcript_task = asyncio.create_task(
            self._transcript_fallback_after_delay(gemini_session, cleaned)
        )

    async def _transcript_fallback_after_delay(self, gemini_session: Any, transcript: str) -> None:
        try:
            await asyncio.sleep(1.1)
            if transcript != self.last_input_transcript.strip():
                return
            if transcript == self.last_handled_transcript:
                return
            self.last_handled_transcript = transcript
            await gemini_session.send_realtime_input(
                text=(
                    "You heard the prospect say this, but no demo tool has been called yet: "
                    f"{transcript!r}. If they asked for a walkthrough, call start_demo_flow. "
                    "If they asked about a specific part of the product, call show_relevant_page "
                    "or answer_with_visuals. If no visual is needed, answer briefly from the "
                    "approved manifest context."
                )
            )
        except asyncio.CancelledError:
            return

    def _flow_step_events(
        self,
        page: DemoPageManifest,
        step: DemoFlowStep,
    ) -> list[DemoEvent]:
        events: list[DemoEvent] = [
            DemoEvent(type="navigate", page_id=page.page_id, route=page.route),
            DemoEvent(type="wait", duration_ms=400),
        ]
        events.extend(self.runtime._timeline_for_step(page, step))
        return self.runtime._validate_events(events)

    def _voice_step_reply(
        self,
        *,
        flow: DemoFlow,
        step: DemoFlowStep,
        page: DemoPageManifest,
        events: list[DemoEvent],
        element_summaries: list[dict[str, str]],
    ) -> str:
        base = self._clean_talk_track(step.talk_track or step.objective or page.summary)
        element_sentence = self._element_sentence(element_summaries)
        if self.active_flow_step_index == 0:
            business_intro = self._business_intro()
            journey = self._business_journey()
            step_purpose = self._first_step_purpose(base)
            return (
                f"{business_intro}. {journey} "
                f"We start with {step_purpose}. {element_sentence}"
            )
        step_purpose = self._step_purpose(base, page)
        return f"Next, this part shows {step_purpose}. {element_sentence}"

    def _persist_voice_step(
        self,
        reply: str,
        page: DemoPageManifest,
        events: list[DemoEvent],
    ) -> LiveDemoMessageResponse:
        session = self.store.get(self.session_id)
        if session is None:
            raise RuntimeError("Live demo session not found")
        updated = self.store.save(
            session.model_copy(
                update={
                    "current_page_id": page.page_id,
                    "state": "demoing",
                    "transcript": [
                        *session.transcript,
                        ConversationTurn(
                            role="user",
                            content=f"Voice walkthrough step: {page.title}",
                        ),
                        ConversationTurn(role="assistant", content=reply),
                    ],
                    "action_log": [*session.action_log, *events],
                }
            )
        )
        return LiveDemoMessageResponse(
            session=updated,
            reply=reply,
            events=events,
            available_actions=page.allowed_actions,
        )

    async def _send_demo_response(
        self,
        response: LiveDemoMessageResponse,
        events: list[DemoEvent],
        flow_state: dict[str, Any] | None = None,
    ) -> None:
        await self.websocket.send_json(
            {
                "type": "demo_response",
                "voice_controlled": True,
                "reply": response.reply,
                "events": [event.model_dump(mode="json") for event in events],
                "session": response.session.model_dump(mode="json"),
                "flow_state": flow_state,
                "available_actions": [
                    action.model_dump(mode="json") for action in response.available_actions
                ],
            }
        )

    def _visual_events_only(self, events: list[DemoEvent]) -> list[DemoEvent]:
        return [event for event in events if event.type != "say"]

    def _step_element_ids(self, page: DemoPageManifest, step: DemoFlowStep) -> list[str]:
        ids: list[str] = []
        for action_id in step.recommended_action_ids:
            action = next((item for item in page.allowed_actions if item.id == action_id), None)
            if action and action.element_id and action.element_id not in ids:
                ids.append(action.element_id)
        if ids:
            return ids
        return [element.id for element in page.elements[:2]]

    def _pause_active_flow(self, *, resume_next: bool) -> None:
        if self.active_flow is None:
            return
        next_index = self.active_flow_step_index
        if resume_next and self.pending_flow_step and self.pending_flow_step.get("has_next"):
            next_index += 1
        if next_index < len(self.active_flow.steps):
            self.paused_flow = self.active_flow
            self.paused_flow_step_index = next_index
        else:
            self.paused_flow = None
            self.paused_flow_step_index = None

    def _page_by_id(self, page_id: str) -> DemoPageManifest | None:
        return next((page for page in self.runtime.manifest.pages if page.page_id == page_id), None)

    def _element_label(self, element_id: str) -> str | None:
        for page in self.runtime.manifest.pages:
            for element in page.elements:
                if element.id == element_id:
                    return element.label
        return None

    def _clean_sentence(self, value: str) -> str:
        return value.strip().rstrip(".")

    def _clean_talk_track(self, value: str) -> str:
        cleaned = self._clean_sentence(value)
        lowered = cleaned.lower()
        for prefix in ("first, ", "then ", "after the demo, ", "finally, ", "next, "):
            if lowered.startswith(prefix):
                return cleaned[len(prefix):].strip()
        return cleaned

    def _business_intro(self) -> str:
        manifest = self.runtime.manifest
        description = self._clean_sentence(manifest.product_description)
        if description:
            return description
        target = self._clean_sentence(manifest.target_persona)
        if target:
            return f"{manifest.product_name} helps {target}"
        return f"{manifest.product_name} helps teams understand and evaluate the product faster"

    def _business_journey(self) -> str:
        flow = self.active_flow or (self.runtime.manifest.flows[0] if self.runtime.manifest.flows else None)
        if flow is not None and flow.goal:
            return f"The walkthrough follows this approved journey: {self._clean_sentence(flow.goal).lower()}."
        page_titles = ", ".join(page.title for page in self.runtime.manifest.pages[:4])
        if page_titles:
            return f"The walkthrough moves through these approved product areas: {page_titles}."
        return "The walkthrough uses the approved product pages and actions from the manifest."

    def _first_step_purpose(self, base: str) -> str:
        return self._step_purpose(base)

    def _step_purpose(
        self,
        base: str,
        page: DemoPageManifest | None = None,
    ) -> str:
        cleaned = base[:1].lower() + base[1:] if base else ""
        if cleaned:
            return cleaned
        if page is not None and page.summary:
            return page.summary[:1].lower() + page.summary[1:]
        return "the next important part of the product journey"

    def _highlighted_element_summaries(
        self,
        page: DemoPageManifest,
        events: list[DemoEvent],
    ) -> list[dict[str, str]]:
        element_by_id = {element.id: element for element in page.elements}
        summaries: list[dict[str, str]] = []
        seen: set[str] = set()
        for event in events:
            if event.type != "highlight.show" or not event.element_id:
                continue
            if event.element_id in seen:
                continue
            element = element_by_id.get(event.element_id)
            if element is None:
                continue
            summaries.append(
                {
                    "label": element.label,
                    "description": element.description,
                }
            )
            seen.add(event.element_id)
        return summaries

    def _element_sentence(self, element_summaries: list[dict[str, str]]) -> str:
        parts = [
            f"{item['label']} is used for {self._clean_sentence(item['description']).lower()}"
            for item in element_summaries[:2]
            if item.get("label") and item.get("description")
        ]
        if not parts:
            return ""
        return " ".join(parts) + "."

    def _handle_runtime_message(self, prompt: str) -> LiveDemoMessageResponse:
        session = self.store.get(self.session_id)
        if session is None:
            raise RuntimeError("Live demo session not found")
        request = LiveDemoMessageRequest(
            message=prompt,
            current_page_id=self.current_page_id or session.current_page_id,
            visible_element_ids=self.visible_element_ids,
        )
        return self.runtime.handle_message(session, request)

    def _demo_context(self, query: object = None) -> dict[str, Any]:
        manifest = self.runtime.manifest
        return {
            "ok": True,
            "query": str(query or ""),
            "product_name": manifest.product_name,
            "cta": manifest.cta,
            "pages": [
                {"page_id": page.page_id, "title": page.title, "summary": page.summary}
                for page in manifest.pages
            ],
            "flows": [
                {
                    "flow_id": flow.id,
                    "name": flow.name,
                    "goal": flow.goal,
                    "steps": [
                        {
                            "step_id": step.id,
                            "page_id": step.page_id,
                            "talk_track": step.talk_track,
                        }
                        for step in flow.steps
                    ],
                }
                for flow in manifest.flows
            ],
            "restricted_claims": manifest.restricted_claims,
            "active_flow": self.active_flow.id if self.active_flow else None,
            "paused_flow": self.paused_flow.id if self.paused_flow else None,
            "paused_flow_step_index": self.paused_flow_step_index,
        }

    async def _send_error(self, message: str) -> None:
        await self.websocket.send_json({"type": "error", "message": message})
