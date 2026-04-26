from __future__ import annotations

from threading import RLock

from app.agents.campaign_models import ChatMessage
from app.demo_controller.actions import build_tracepilot_manifest
from app.demo_controller.models import (
    BrowserAction,
    BrowserObservation,
    DemoSession,
    DemoSessionCreateRequest,
    VerificationResult,
    utc_now,
)


class InMemoryDemoSessionStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, DemoSession] = {}

    def create_session(self, request: DemoSessionCreateRequest) -> DemoSession:
        with self._lock:
            manifest = build_tracepilot_manifest(request.app_base_url)
            session = DemoSession(
                demo_room_id=request.demo_room_id,
                scenario=request.scenario,
                mode=request.mode,
                app_base_url=request.app_base_url,
                objective=request.objective,
                status="ready",
                manifest=manifest,
            )
            self._sessions[session.id] = session
            return session

    def get_session(self, session_id: str) -> DemoSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def save_session(self, session: DemoSession) -> DemoSession:
        with self._lock:
            updated = session.model_copy(update={"updated_at": utc_now()})
            self._sessions[updated.id] = updated
            return updated

    def append_transcript(
        self, session: DemoSession, user_message: str, assistant_message: str
    ) -> DemoSession:
        return self.save_session(
            session.model_copy(
                update={
                    "transcript": [
                        *session.transcript,
                        ChatMessage(role="user", content=user_message),
                        ChatMessage(role="assistant", content=assistant_message),
                    ]
                }
            )
        )

    def append_actions(self, session: DemoSession, actions: list[BrowserAction]) -> DemoSession:
        return self.save_session(session.model_copy(update={"action_log": [*session.action_log, *actions]}))

    def append_observation(self, session: DemoSession, observation: BrowserObservation) -> DemoSession:
        return self.save_session(
            session.model_copy(update={"observations": [*session.observations, observation]})
        )

    def append_verifications(
        self, session: DemoSession, results: list[VerificationResult]
    ) -> DemoSession:
        return self.save_session(
            session.model_copy(update={"verification_log": [*session.verification_log, *results]})
        )

    def reset_session(self, session: DemoSession) -> DemoSession:
        return self.save_session(
            session.model_copy(
                update={
                    "status": "ready",
                    "current_step_id": None,
                    "action_budget": 20,
                    "transcript": [],
                    "action_log": [],
                    "pending_actions": [],
                    "verification_log": [],
                    "observations": [],
                    "last_error": None,
                }
            )
        )

    def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


demo_session_store = InMemoryDemoSessionStore()
