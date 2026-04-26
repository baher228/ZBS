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

        decision = self._decide_guided_walkthrough(request.message) or self._decide_with_llm(
            session, request, current_page
        ) or self._decide(request.message, current_page)
        target_page = self._page_by_id(decision["page_id"]) or current_page
        reply = decision["reply"]
        events = decision.get("events") or self._build_events(
            reply,
            target_page,
            decision["element_ids"],
            decision["lead_patch"],
        )
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

    def _decide_guided_walkthrough(self, message: str) -> dict | None:
        text = message.lower()
        if not any(term in text for term in ["walk me through", "walkthrough", "demo the app", "show me around", "full demo"]):
            return None

        flow = self._primary_flow()
        if flow is None or not flow.steps:
            return None

        events: list[DemoEvent] = [
            DemoEvent(
                type="say",
                text=f"I'll walk through the approved flow: {flow.goal}",
                duration_ms=2600,
            )
        ]
        final_page = self._page_by_id(flow.steps[-1].page_id)
        for step in flow.steps:
            page = self._page_by_id(step.page_id)
            if page is None:
                continue
            element_ids = self._action_element_ids(page, step.recommended_action_ids)
            if not element_ids:
                element_ids = self._primary_element_ids(page, limit=2)
            events.extend(
                [
                    DemoEvent(type="navigate", page_id=page.page_id, route=page.route),
                    DemoEvent(type="wait", duration_ms=650),
                    DemoEvent(
                        type="say",
                        text=step.talk_track or f"{page.title} {page.summary}".strip(),
                        duration_ms=3200,
                    ),
                ]
            )
            for element_id in element_ids:
                events.extend(
                    [
                        DemoEvent(type="cursor.move", element_id=element_id, duration_ms=480),
                        DemoEvent(
                            type="highlight.show",
                            element_id=element_id,
                            label=self._element_label(element_id),
                        ),
                        DemoEvent(type="wait", duration_ms=1300),
                    ]
                )
            if element_ids:
                events.append(DemoEvent(type="highlight.hide", element_id=element_ids[-1]))
        events.append(
            DemoEvent(
                type="lead.profile.updated",
                patch={"interested_features": ["guided product walkthrough"]},
            )
        )

        if final_page is None:
            final_page = self.manifest.pages[0]
        return {
            "page_id": final_page.page_id,
            "element_ids": [],
            "state": "demoing",
            "lead_patch": {"interested_features": ["guided product walkthrough"]},
            "reply": (
                f"I'll walk through the approved flow: {flow.goal}"
            ),
            "events": events,
        }

    def available_actions(self, page_id: str) -> list[PageAction]:
        page = self._page_by_id(page_id)
        return page.allowed_actions if page else []

    def _decide(self, message: str, current_page: DemoPageManifest) -> dict:
        generic = self._decide_from_manifest(message, current_page)
        if generic is not None:
            return generic

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

    def _decide_from_manifest(
        self,
        message: str,
        current_page: DemoPageManifest,
    ) -> dict | None:
        words = {
            word
            for word in re.findall(r"[a-z0-9]+", message.lower())
            if len(word) > 2
        }
        best_page = current_page
        best_score = -1
        for page in self.manifest.pages:
            haystack = " ".join(
                [
                    page.page_id,
                    page.title,
                    page.summary,
                    " ".join(page.visible_concepts),
                    " ".join(element.label + " " + element.description for element in page.elements),
                    " ".join(action.label + " " + action.intent for action in page.allowed_actions),
                ]
            ).lower()
            score = sum(1 for word in words if word in haystack)
            if score > best_score:
                best_score = score
                best_page = page

        element_ids = [
            action.element_id
            for action in best_page.allowed_actions
            if action.element_id and action.type in {"highlight", "cursor.move", "navigate"}
        ][:3]
        if not element_ids:
            element_ids = [element.id for element in best_page.elements[:3]]

        return {
            "page_id": best_page.page_id,
            "element_ids": element_ids,
            "state": "demoing",
            "lead_patch": {"interested_features": [best_page.title]},
            "reply": (
                f"I'll show {best_page.title.lower()}. "
                f"{best_page.summary or 'This is the relevant part of the extracted app.'}"
            ),
        }

    def _primary_flow(self):
        return self.manifest.flows[0] if self.manifest.flows else None

    def _action_element_ids(self, page: DemoPageManifest, action_ids: list[str]) -> list[str]:
        ids: list[str] = []
        for action_id in action_ids:
            action = next((item for item in page.allowed_actions if item.id == action_id), None)
            if action and action.element_id and action.element_id not in ids:
                ids.append(action.element_id)
        return ids

    def _primary_element_ids(self, page: DemoPageManifest, limit: int = 2) -> list[str]:
        action_element_ids = [
            action.element_id
            for action in page.allowed_actions
            if action.element_id and action.type in {"highlight", "cursor.move", "navigate"}
        ]
        element_ids = action_element_ids + [element.id for element in page.elements]
        deduped: list[str] = []
        for element_id in element_ids:
            if element_id not in deduped:
                deduped.append(element_id)
        return deduped[:limit]

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
                        "Use the provided manifest pages, page summaries, actions, and flow steps to choose the best page. "
                        "Prefer the current page when the user asks a local follow-up. "
                        "For broad onboarding requests, follow the manifest flow. "
                        "For questions about output after the demo, prefer CRM/summary/follow-up pages if present. "
                        "For demo-room questions, prefer demo/prospect-room pages if present. "
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
                            "manifest": self._manifest_context(request.message, current_page),
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

    def _manifest_context(self, message: str, current_page: DemoPageManifest) -> dict[str, object]:
        relevant_pages = self._relevant_pages(message, current_page)
        return {
            "product_name": self.manifest.product_name,
            "target_persona": self.manifest.target_persona,
            "cta": self.manifest.cta,
            "current_page": self._page_context(current_page),
            "relevant_pages": [self._page_context(page) for page in relevant_pages],
            "page_index": [
                {"page_id": page.page_id, "title": page.title, "summary": page.summary}
                for page in self.manifest.pages
            ],
            "flows": [flow.model_dump() for flow in self.manifest.flows],
            "knowledge": [record.model_dump() for record in self._relevant_knowledge(message)],
            "qualification_questions": self.manifest.qualification_questions,
            "restricted_claims": self.manifest.restricted_claims,
        }

    def _page_context(self, page: DemoPageManifest) -> dict[str, object]:
        return {
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

    def _relevant_pages(
        self,
        message: str,
        current_page: DemoPageManifest,
        limit: int = 4,
    ) -> list[DemoPageManifest]:
        words = {
            word
            for word in re.findall(r"[a-z0-9]+", message.lower())
            if len(word) > 2
        }
        scored: list[tuple[int, DemoPageManifest]] = []
        for page in self.manifest.pages:
            haystack = " ".join(
                [
                    page.page_id,
                    page.title,
                    page.summary,
                    " ".join(page.visible_concepts),
                    " ".join(element.label + " " + element.description for element in page.elements),
                ]
            ).lower()
            score = sum(1 for word in words if word in haystack)
            if page.page_id == current_page.page_id:
                score += 2
            scored.append((score, page))
        scored.sort(key=lambda item: item[0], reverse=True)
        pages: list[DemoPageManifest] = []
        for _, page in scored:
            if page.page_id not in {item.page_id for item in pages}:
                pages.append(page)
            if len(pages) >= limit:
                break
        return pages

    def _relevant_knowledge(self, message: str, limit: int = 4):
        words = {
            word
            for word in re.findall(r"[a-z0-9]+", message.lower())
            if len(word) > 2
        }
        scored = []
        for record in self.manifest.knowledge:
            haystack = f"{record.topic} {record.content} {' '.join(record.tags)}".lower()
            scored.append((sum(1 for word in words if word in haystack), record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:limit]]

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
