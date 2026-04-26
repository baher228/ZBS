from __future__ import annotations

import json
import os
import re

from openai import OpenAI

from app.core.config import settings
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

        decision = self._decide_with_llm(session, request, current_page) or self._decide(
            request.message, current_page
        )
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

    def _decide_with_llm(
        self,
        session: LiveDemoSession,
        request: LiveDemoMessageRequest,
        current_page: DemoPageManifest,
    ) -> dict | None:
        if os.getenv("LIVE_DEMO_PLANNER", "").lower() not in {"1", "true", "openai", "llm"}:
            return None
        api_key = settings.resolved_llm_api_key
        if not api_key:
            return None

        allowed_page_ids = {page.page_id for page in self.manifest.pages}
        allowed_element_ids = {
            element.id for page in self.manifest.pages for element in page.elements
        }
        client = OpenAI(api_key=api_key, timeout=float(os.getenv("LIVE_DEMO_PLANNER_TIMEOUT", "45")))
        model = os.getenv("LIVE_DEMO_PLANNER_MODEL", "gpt-5.4-mini")
        model_kwargs: dict[str, object] = {"model": model}
        if model.startswith("gpt-5"):
            model_kwargs["reasoning"] = {"effort": os.getenv("LIVE_DEMO_REASONING_EFFORT", "low")}
            model_kwargs["text"] = {"verbosity": os.getenv("LIVE_DEMO_TEXT_VERBOSITY", "low")}
        else:
            model_kwargs["temperature"] = 0.1
        response = client.responses.create(
            **model_kwargs,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are the planner for a safe AI product demo room. "
                        "You can choose narration, an approved page, approved elements to highlight, "
                        "and a lead-profile patch. You cannot invent pages or elements. "
                        "Route startup/founder input/setup questions to setup. "
                        "Route approved answers, security, pricing, and claims questions to knowledge. "
                        "Route safe actions, cursor, Stagehand, browser control, and flow questions to flow. "
                        "Route prospect room, demo room, live demo, voice, Gemini, and real-time experience questions to live_room. "
                        "Route after-demo, qualification, CRM, lead score, and follow-up questions to summary. "
                        "Return strict JSON only: {\"reply\":\"string\",\"page_id\":\"string\","
                        "\"element_ids\":[\"string\"],\"state\":\"demoing|answering_question|qualifying\","
                        "\"lead_patch\":{\"use_case\":\"string|null\",\"urgency\":\"string|null\","
                        "\"interested_features\":[\"string\"],\"score\":number|null}}."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "message": request.message,
                            "current_page_id": current_page.page_id,
                            "visible_element_ids": request.visible_element_ids,
                            "lead_profile": session.lead_profile.model_dump(),
                            "recent_transcript": [
                                turn.model_dump(mode="json") for turn in session.transcript[-6:]
                            ],
                            "manifest": self._manifest_context(),
                        },
                        indent=2,
                    ),
                },
            ],
        )
        try:
            raw = self._parse_json(response.output_text)
        except (json.JSONDecodeError, TypeError):
            return None

        page_id = raw.get("page_id")
        if page_id not in allowed_page_ids:
            return None
        element_ids = [
            element_id
            for element_id in raw.get("element_ids", [])
            if isinstance(element_id, str) and element_id in allowed_element_ids
        ][:4]
        state = raw.get("state")
        if state not in {"demoing", "answering_question", "qualifying"}:
            state = "answering_question"
        lead_patch = raw.get("lead_patch") if isinstance(raw.get("lead_patch"), dict) else {}
        cleaned_patch: dict[str, object] = {}
        for key in ["use_case", "urgency", "current_solution"]:
            value = lead_patch.get(key)
            if isinstance(value, str) and value:
                cleaned_patch[key] = value
        features = lead_patch.get("interested_features")
        if isinstance(features, list):
            cleaned_patch["interested_features"] = [
                str(feature) for feature in features if str(feature).strip()
            ][:5]
        score = lead_patch.get("score")
        if isinstance(score, int) and 0 <= score <= 100:
            cleaned_patch["score"] = score

        return {
            "page_id": page_id,
            "element_ids": element_ids,
            "state": state,
            "lead_patch": cleaned_patch,
            "reply": str(raw.get("reply") or "").strip()
            or f"I will show the {self._page_by_id(page_id).title.lower()} step.",
        }

    def _manifest_context(self) -> dict[str, object]:
        return {
            "product_name": self.manifest.product_name,
            "target_persona": self.manifest.target_persona,
            "cta": self.manifest.cta,
            "pages": [
                {
                    "page_id": page.page_id,
                    "title": page.title,
                    "summary": page.summary,
                    "visible_concepts": page.visible_concepts,
                    "elements": [
                        {
                            "id": element.id,
                            "label": element.label,
                            "description": element.description,
                            "safe_to_click": element.safe_to_click,
                        }
                        for element in page.elements
                    ],
                    "allowed_actions": [action.model_dump() for action in page.allowed_actions],
                }
                for page in self.manifest.pages
            ],
            "flows": [flow.model_dump() for flow in self.manifest.flows],
            "knowledge": [record.model_dump() for record in self.manifest.knowledge],
            "qualification_questions": self.manifest.qualification_questions,
            "restricted_claims": self.manifest.restricted_claims,
        }

    def _parse_json(self, text: str) -> dict:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                raise
            return json.loads(match.group(0))

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
