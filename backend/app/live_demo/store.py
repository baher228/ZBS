from __future__ import annotations

from threading import RLock

from app.live_demo.models import LiveDemoSession, utc_now


class LiveDemoSessionStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._sessions: dict[str, LiveDemoSession] = {}

    def create(self, startup_id: str = "demeo", current_page_id: str = "setup") -> LiveDemoSession:
        with self._lock:
            session = LiveDemoSession(startup_id=startup_id, current_page_id=current_page_id)
            self._sessions[session.id] = session
            return session

    def get(self, session_id: str) -> LiveDemoSession | None:
        with self._lock:
            return self._sessions.get(session_id)

    def save(self, session: LiveDemoSession) -> LiveDemoSession:
        with self._lock:
            updated = session.model_copy(update={"updated_at": utc_now()})
            self._sessions[updated.id] = updated
            return updated

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()


live_demo_session_store = LiveDemoSessionStore()
