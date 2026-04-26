from __future__ import annotations

from app.live_demo.manifest import DEMO_MANIFEST
from app.live_demo.models import (
    ConversationTurn,
    DemoEvent,
    DemoManifest,
    DemoPageManifest,
    LeadProfile,
    LiveDemoMessageRequest,
    LiveDemoMessageResponse,
    LiveDemoSession,
    PageAction,
)
from app.live_demo.store import LiveDemoSessionStore


class LiveDemoRuntime:
    def __init__(
        self,
        store: LiveDemoSessionStore,
        manifest: DemoManifest = DEMO_MANIFEST,
    ) -> None:
        self.store = store
        self.manifest = manifest

    def handle_message(
        self, session: LiveDemoSession, request: LiveDemoMessageRequest
    ) -> LiveDemoMessageResponse:
        observed_page_id = request.current_page_id or session.current_page_id
        current_page = self._page_by_id(observed_page_id) or self._page_by_id(session.current_page_id)
        if current_page is None:
            current_page = self.manifest.pages[0]

        decision = self._decide(request.message, current_page)
        target_page = self._page_by_id(decision["page_id"]) or current_page
        reply = decision["reply"]
        events = self._build_events(reply, target_page, decision["element_ids"], decision["lead_patch"])
        events = self._validate_events(events)

        lead_profile = self._update_lead_profile(session.lead_profile, decision["lead_patch"])
        updated = self.store.save(
            session.model_copy(
                update={
                    "current_page_id": target_page.page_id,
                    "state": decision["state"],
                    "transcript": [
                        *session.transcript,
                        ConversationTurn(role="user", content=request.message),
                        ConversationTurn(role="assistant", content=reply),
                    ],
                    "lead_profile": lead_profile,
                    "action_log": [*session.action_log, *events],
                }
            )
        )
        return LiveDemoMessageResponse(
            session=updated,
            reply=reply,
            events=events,
            available_actions=target_page.allowed_actions,
        )

    def available_actions(self, page_id: str) -> list[PageAction]:
        page = self._page_by_id(page_id)
        return page.allowed_actions if page else []

    def _decide(self, message: str, current_page: DemoPageManifest) -> dict:
        text = message.lower()
        lead_patch: dict[str, object] = {}

        if any(term in text for term in ["voice", "gemini", "realtime", "real time", "talk"]):
            return {
                "page_id": "live_room",
                "element_ids": ["voice-control", "event-stream"],
                "state": "answering_question",
                "lead_patch": {"interested_features": ["voice demo agent"]},
                "reply": (
                    "Yes. Gemini Live can sit on top of this same event loop. "
                    "The voice model should call safe tools like highlight, move cursor, and show page; "
                    "our backend still validates every visual action."
                ),
            }

        if any(term in text for term in ["input", "founder", "provide", "startup", "setup", "start"]):
            lead_patch["use_case"] = "creating an agent-led product demo"
            return {
                "page_id": "setup",
                "element_ids": ["product-url", "persona-card", "walkthrough-card"],
                "state": "demoing",
                "lead_patch": lead_patch,
                "reply": (
                    "The founder starts with a product URL or sandbox, the target buyer, "
                    "the demo goals, a plain-English walkthrough, approved Q&A, CTA, and qualification questions. "
                    "That is enough to build the first reviewed demo room."
                ),
            }

        if any(term in text for term in ["knowledge", "q&a", "pricing", "security", "roadmap", "claim"]):
            return {
                "page_id": "knowledge",
                "element_ids": ["approved-qna", "restricted-claims", "qualification-rules"],
                "state": "answering_question",
                "lead_patch": {"interested_features": ["approved answers"]},
                "reply": (
                    "The knowledge bank separates approved answers from restricted claims. "
                    "That lets the agent answer pricing, security, integration, and roadmap questions without inventing."
                ),
            }

        if any(term in text for term in ["action", "click", "cursor", "flow", "page", "safe", "stagehand"]):
            return {
                "page_id": "flow",
                "element_ids": ["page-actions", "safety-gate", "flow-graph"],
                "state": "demoing",
                "lead_patch": {"interested_features": ["safe guided actions"]},
                "reply": (
                    "The agent is adaptive, but it only receives actions available on the current page. "
                    "It can highlight, move the cursor, navigate approved pages, or propose a click that passes the safety gate."
                ),
            }

        if any(term in text for term in ["prospect", "room", "demo", "show me", "walk", "real"]):
            return {
                "page_id": "live_room",
                "element_ids": ["agent-cursor-preview", "event-stream"],
                "state": "demoing",
                "lead_patch": {"urgency": "active evaluation"},
                "reply": (
                    "This is the prospect-facing room. The agent answers the question, then the page plays the same decision as visual events: "
                    "navigation, cursor movement, highlights, and action logging."
                ),
            }

        if any(term in text for term in ["qualify", "lead", "crm", "summary", "follow", "score"]):
            return {
                "page_id": "summary",
                "element_ids": ["lead-score", "crm-summary", "follow-up"],
                "state": "qualifying",
                "lead_patch": {"score": 82, "interested_features": ["lead qualification"]},
                "reply": (
                    "After the demo, the founder gets the useful sales output: lead score, use case, objections, CRM summary, and a follow-up draft."
                ),
            }

        return {
            "page_id": current_page.page_id,
            "element_ids": [element.id for element in current_page.elements[:2]],
            "state": "answering_question",
            "lead_patch": {},
            "reply": (
                f"On this page, the important idea is {current_page.summary.lower()} "
                "Ask me to show inputs, knowledge, safe actions, voice, or qualification and I will move the demo there."
            ),
        }

    def _build_events(
        self,
        reply: str,
        target_page: DemoPageManifest,
        element_ids: list[str],
        lead_patch: dict[str, object],
    ) -> list[DemoEvent]:
        events: list[DemoEvent] = [
            DemoEvent(type="say", text=reply, duration_ms=1600),
            DemoEvent(type="navigate", page_id=target_page.page_id, route=target_page.route),
            DemoEvent(type="wait", duration_ms=180),
        ]
        for element_id in element_ids:
            events.extend(
                [
                    DemoEvent(type="cursor.move", element_id=element_id, duration_ms=520),
                    DemoEvent(type="highlight.show", element_id=element_id, label=self._element_label(element_id)),
                    DemoEvent(type="wait", duration_ms=520),
                ]
            )
        if element_ids:
            events.append(DemoEvent(type="highlight.hide", element_id=element_ids[-1]))
        if lead_patch:
            events.append(DemoEvent(type="lead.profile.updated", patch=lead_patch))
        return events

    def _validate_events(self, events: list[DemoEvent]) -> list[DemoEvent]:
        allowed_page_ids = {page.page_id for page in self.manifest.pages}
        allowed_element_ids = {
            element.id for page in self.manifest.pages for element in page.elements
        }
        valid: list[DemoEvent] = []
        for event in events:
            if event.page_id and event.page_id not in allowed_page_ids:
                continue
            if event.element_id and event.element_id not in allowed_element_ids:
                continue
            valid.append(event)
        return valid

    def _update_lead_profile(self, lead_profile: LeadProfile, patch: dict[str, object]) -> LeadProfile:
        updates = lead_profile.model_dump()
        if "interested_features" in patch:
            existing = list(updates["interested_features"])
            for feature in patch["interested_features"] or []:
                if feature not in existing:
                    existing.append(str(feature))
            updates["interested_features"] = existing
        for key in ["use_case", "urgency", "current_solution", "score"]:
            if key in patch:
                updates[key] = patch[key]
        return LeadProfile(**updates)

    def _page_by_id(self, page_id: str) -> DemoPageManifest | None:
        return next((page for page in self.manifest.pages if page.page_id == page_id), None)

    def _element_label(self, element_id: str) -> str | None:
        for page in self.manifest.pages:
            for element in page.elements:
                if element.id == element_id:
                    return element.label
        return None
