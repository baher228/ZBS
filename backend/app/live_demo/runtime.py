from __future__ import annotations

import json
import os
import re

from openai import OpenAI

from app.core.config import settings
from app.live_demo.manifest import DEMO_MANIFEST
from app.live_demo.models import (
    DemoFlow,
    DemoFlowStep,
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

        decision = (
            self._decide_with_llm(session, request, current_page)
            or self._decide_guided_walkthrough(request.message)
            or self._decide(request.message, current_page)
        )
        target_page = self._page_by_id(decision["page_id"]) or current_page
        reply = decision["reply"]
        events = decision.get("events")
        if not events and decision.get("action_ids"):
            events = self._build_action_events(
                reply,
                target_page,
                decision["action_ids"],
                decision["lead_patch"],
            )
        if not events:
            events = self._build_events(
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
        return self._build_guided_walkthrough_decision(flow)

    def _build_guided_walkthrough_decision(self, flow: DemoFlow) -> dict:
        events: list[DemoEvent] = [
            DemoEvent(
                type="say",
                text=self._walkthrough_intro(flow),
                duration_ms=2400,
            )
        ]
        final_page = self._page_by_id(flow.steps[-1].page_id)
        active_walkthrough_page_id: str | None = None
        for step_index, step in enumerate(flow.steps):
            page = self._page_by_id(step.page_id)
            if page is None:
                continue
            if active_walkthrough_page_id != page.page_id:
                events.extend(
                    [
                        DemoEvent(type="navigate", page_id=page.page_id, route=page.route),
                        DemoEvent(type="wait", duration_ms=650),
                    ]
                )
                active_walkthrough_page_id = page.page_id
            events.append(
                DemoEvent(
                    type="say",
                    text=self._walkthrough_step_narration(
                        step,
                        page,
                        step_index=step_index,
                    ),
                    duration_ms=2600,
                )
            )
            events.extend(self._timeline_for_step(page, step))
            for event in reversed(events):
                if event.type == "navigate" and event.page_id:
                    active_walkthrough_page_id = event.page_id
                    break
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
            "action_ids": [],
            "state": "demoing",
            "lead_patch": {"interested_features": ["guided product walkthrough"]},
            "reply": self._walkthrough_intro(flow),
            "events": events,
        }

    def available_actions(self, page_id: str) -> list[PageAction]:
        page = self._page_by_id(page_id)
        return page.allowed_actions if page else []

    def primary_flow(self) -> DemoFlow | None:
        return self._primary_flow()

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
        best_page = current_page
        best_score = float("-inf")
        for page in self.manifest.pages:
            score = self._score_page_for_message(message, page)
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
        action_ids = [action.id for action in self._best_actions_for_message(message, best_page)[:3]]

        return {
            "page_id": best_page.page_id,
            "element_ids": element_ids,
            "action_ids": action_ids,
            "state": "demoing",
            "lead_patch": {"interested_features": [best_page.title]},
            "reply": (
                f"I'll show {best_page.title.lower()}. "
                f"{best_page.summary or 'This is the relevant part of the extracted app.'}"
            ),
        }

    def _score_page_for_message(self, message: str, page: DemoPageManifest) -> float:
        tokens = self._meaningful_tokens(message)
        phrases = self._query_phrases(message)
        title = page.title.lower()
        summary = page.summary.lower()
        concepts = " ".join(page.visible_concepts).lower()
        elements = " ".join(
            element.label + " " + element.description for element in page.elements
        ).lower()
        actions = " ".join(
            action.label + " " + action.intent for action in page.allowed_actions
        ).lower()
        flow_context = " ".join(
            step.objective + " " + step.talk_track
            for flow in self.manifest.flows
            for step in flow.steps
            if step.page_id == page.page_id
        ).lower()

        score = 0.0
        weighted_fields = [
            (title, 4.0),
            (summary, 3.0),
            (concepts, 2.5),
            (actions, 2.0),
            (flow_context, 2.0),
            (elements, 1.5),
            (page.page_id.lower().replace("_", " "), 1.0),
        ]
        for token in tokens:
            for field, weight in weighted_fields:
                if self._contains_token(field, token):
                    score += weight
        for phrase in phrases:
            for field, weight in weighted_fields[:5]:
                if phrase in field:
                    score += weight * (len(phrase.split()) + 1)

        if (
            self._is_specific_navigation_request(message)
            and self._looks_like_entry_page(page)
            and not self._asks_for_entry_page(message)
        ):
            score -= 30.0
        return score

    def _contains_token(self, field: str, token: str) -> bool:
        return re.search(rf"(^|[^a-z0-9]){re.escape(token)}([^a-z0-9]|$)", field) is not None

    def _meaningful_tokens(self, message: str) -> list[str]:
        stopwords = {
            "the",
            "and",
            "for",
            "you",
            "your",
            "what",
            "how",
            "does",
            "can",
            "show",
            "open",
            "take",
            "tell",
            "me",
            "this",
            "that",
            "with",
            "from",
            "into",
            "about",
        }
        return [
            word
            for word in re.findall(r"[a-z0-9]+", message.lower())
            if len(word) > 2 and word not in stopwords
        ]

    def _query_phrases(self, message: str) -> list[str]:
        tokens = self._meaningful_tokens(message)
        phrases: list[str] = []
        for size in (4, 3, 2):
            for index in range(0, max(0, len(tokens) - size + 1)):
                phrases.append(" ".join(tokens[index : index + size]))
        return phrases

    def _is_specific_navigation_request(self, message: str) -> bool:
        text = message.lower()
        return any(term in text for term in ["show", "open", "take me", "go to", "walk me to"])

    def _looks_like_entry_page(self, page: DemoPageManifest) -> bool:
        page_text = " ".join(
            [page.page_id, page.title, page.summary, " ".join(page.visible_concepts)]
        ).lower()
        return any(
            term in page_text
            for term in [
                "home",
                "homepage",
                "landing",
                "overview",
                "entry point",
                "entry points",
                "navigation",
                "quick links",
                "listing",
                "directory",
                "menu",
                "lab",
            ]
        )

    def _asks_for_entry_page(self, message: str) -> bool:
        text = message.lower()
        return any(
            term in text
            for term in [
                "home",
                "homepage",
                "landing page",
                "overview",
                "directory",
                "menu",
                "all pages",
                "all agents",
                "agent lab",
            ]
        )

    def _primary_flow(self) -> DemoFlow | None:
        if not self.manifest.flows:
            return None
        flow = self.manifest.flows[0]
        steps = list(flow.steps)
        seen_step_ids = {step.id for step in steps}
        last_page_id = steps[-1].page_id if steps else flow.entry_page_id

        # Stitch independently extracted flow fragments when they are connected
        # by page id, e.g. setup -> demo and demo -> summary.
        changed = True
        while changed:
            changed = False
            for candidate in self.manifest.flows[1:]:
                if not candidate.steps:
                    continue
                if candidate.steps[0].page_id != last_page_id:
                    continue
                appended: list[DemoFlowStep] = []
                for step in candidate.steps:
                    if step.id in seen_step_ids:
                        continue
                    appended.append(step)
                    seen_step_ids.add(step.id)
                if appended:
                    steps.extend(appended)
                    last_page_id = steps[-1].page_id
                    changed = True

        if steps == flow.steps:
            return flow
        return flow.model_copy(update={"steps": steps})

    def _flow_by_id(self, flow_id: str) -> DemoFlow | None:
        flow = next((item for item in self.manifest.flows if item.id == flow_id), None)
        if flow is None:
            return None
        if self.manifest.flows and flow.id == self.manifest.flows[0].id:
            return self._primary_flow()
        return flow

    def _walkthrough_intro(self, flow) -> str:
        description = self.manifest.product_description.strip().rstrip(".")
        if description:
            return (
                f"{description}. I will follow the approved product journey: "
                f"{flow.goal[:1].lower() + flow.goal[1:]}"
            )
        return (
            f"{self.manifest.product_name} is built for {self.manifest.target_persona}. "
            f"I will show the product journey: {flow.goal[:1].lower() + flow.goal[1:]}"
        )

    def _walkthrough_step_narration(
        self,
        step,
        page: DemoPageManifest,
        *,
        step_index: int,
    ) -> str:
        base = self._clean_step_text(step.talk_track or step.objective or page.summary)
        action_context = self._action_context_sentence(page, step)
        prefix = "We start here because" if step_index == 0 else "This step matters because"
        purpose = (base or page.summary).strip()
        if not purpose:
            purpose = f"it shows {page.title.lower()}"
        return f"{prefix} {purpose[:1].lower() + purpose[1:]}. {action_context}".strip()

    def _action_context_sentence(
        self,
        page: DemoPageManifest,
        step: DemoFlowStep,
    ) -> str:
        actions = self._step_actions(page, step)
        recommended_ids = set(step.recommended_action_ids)
        show_actions = [
            action
            for action in actions
            if action.element_id
            and (action.type != "navigate" or action.id not in recommended_ids)
        ]
        move_action = next(
            (
                action
                for action in reversed(actions)
                if action.id in recommended_ids
                and action.type == "navigate"
                and action.target_page_id != page.page_id
            ),
            None,
        )
        labels = [self._presentation_label(action.label) for action in show_actions[:4] if action.label]
        if not labels:
            if move_action:
                return f"Then we move through {self._presentation_label(move_action.label)}."
            return ""
        if len(labels) == 1:
            sentence = f"This page covers {labels[0]}."
        else:
            sentence = f"This page covers {', '.join(labels[:-1])}, and {labels[-1]}."
        if move_action:
            sentence += f" Then we move through {self._presentation_label(move_action.label)}."
        return sentence

    def _presentation_label(self, value: str) -> str:
        label = value.strip()
        for prefix in ("Highlight ", "Open ", "Show "):
            if label.lower().startswith(prefix.lower()):
                return label[len(prefix):].strip()
        return label

    def _clean_step_text(self, value: str) -> str:
        cleaned = value.strip().rstrip(".")
        lowered = cleaned.lower()
        for prefix in ("first, ", "then ", "after the demo, ", "finally, ", "next, "):
            if lowered.startswith(prefix):
                return cleaned[len(prefix):].strip()
        return cleaned

    def _action_element_ids(self, page: DemoPageManifest, action_ids: list[str]) -> list[str]:
        ids: list[str] = []
        for action_id in action_ids:
            action = next((item for item in page.allowed_actions if item.id == action_id), None)
            if action and action.element_id and action.element_id not in ids:
                ids.append(action.element_id)
        return ids

    def _actions_by_ids(self, page: DemoPageManifest, action_ids: list[str]) -> list[PageAction]:
        actions: list[PageAction] = []
        for action_id in action_ids:
            action = next((item for item in page.allowed_actions if item.id == action_id), None)
            if action and not action.requires_approval:
                actions.append(action)
        return actions

    def _step_actions(self, page: DemoPageManifest, step: DemoFlowStep) -> list[PageAction]:
        recommended = self._actions_by_ids(page, step.recommended_action_ids)
        recommended_ids = {action.id for action in recommended}
        support: list[PageAction] = []
        for action in page.allowed_actions:
            if action.id in recommended_ids or action.requires_approval or not action.element_id:
                continue
            if action.type == "highlight":
                support.append(action)
            if len(support) >= 4:
                break
        if len(support) < 4:
            for action in page.allowed_actions:
                if action.id in recommended_ids or action in support:
                    continue
                if action.requires_approval or not action.element_id:
                    continue
                if action.type in {"cursor.move", "navigate"}:
                    support.append(action)
                if len(support) >= 4:
                    break

        nav_recommended = [action for action in recommended if action.type == "navigate"]
        non_nav_recommended = [action for action in recommended if action.type != "navigate"]
        if nav_recommended:
            return [*support, *non_nav_recommended, nav_recommended[0]]
        return [*recommended, *support[: max(0, 5 - len(recommended))]]

    def _timeline_for_step(
        self,
        page: DemoPageManifest,
        step: DemoFlowStep,
    ) -> list[DemoEvent]:
        actions = self._step_actions(page, step)
        if not actions:
            return self._highlight_elements(self._primary_element_ids(page, limit=2))

        events: list[DemoEvent] = []
        for action in actions:
            execute_action = action.id in set(step.recommended_action_ids)
            if action.type == "navigate" and not execute_action:
                events.extend(self._preview_action(action))
                continue
            events.extend(self._timeline_for_actions(page, [action], execute_navigation=execute_action))
        return events

    def _best_actions_for_message(
        self,
        message: str,
        page: DemoPageManifest,
    ) -> list[PageAction]:
        tokens = self._meaningful_tokens(message)
        scored: list[tuple[float, PageAction]] = []
        for action in page.allowed_actions:
            if action.requires_approval:
                continue
            text = f"{action.id} {action.label} {action.intent} {action.type}".lower()
            score = 0.0
            for token in tokens:
                if self._contains_token(text, token):
                    score += 1.0
            if action.type == "highlight":
                score += 0.4
            if action.element_id:
                score += 0.2
            scored.append((score, action))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [action for _, action in scored]

    def _timeline_for_actions(
        self,
        page: DemoPageManifest,
        actions: list[PageAction],
        *,
        execute_navigation: bool = True,
    ) -> list[DemoEvent]:
        events: list[DemoEvent] = []
        for action in actions:
            if action.element_id:
                events.extend(
                    [
                        DemoEvent(
                            type="cursor.move",
                            element_id=action.element_id,
                            duration_ms=560,
                        ),
                        DemoEvent(
                            type="highlight.show",
                            element_id=action.element_id,
                            label=action.label,
                        ),
                        DemoEvent(type="wait", duration_ms=900),
                    ]
                )
            if action.type in {"click", "navigate"} and action.element_id and execute_navigation:
                events.extend(
                    [
                        DemoEvent(type="cursor.click", element_id=action.element_id),
                        DemoEvent(type="wait", duration_ms=260),
                    ]
                )
            if action.type == "navigate" and action.target_page_id and execute_navigation:
                target = self._page_by_id(action.target_page_id)
                if target:
                    events.extend(
                        [
                            DemoEvent(type="highlight.hide", element_id=action.element_id),
                            DemoEvent(
                                type="navigate",
                                page_id=target.page_id,
                                route=target.route,
                            ),
                            DemoEvent(type="wait", duration_ms=650),
                        ]
                    )
            elif action.element_id:
                events.append(DemoEvent(type="highlight.hide", element_id=action.element_id))
        if not events:
            events.extend(self._highlight_elements(self._primary_element_ids(page, limit=2)))
        return events

    def _preview_action(self, action: PageAction) -> list[DemoEvent]:
        if not action.element_id:
            return []
        return [
            DemoEvent(type="cursor.move", element_id=action.element_id, duration_ms=520),
            DemoEvent(type="highlight.show", element_id=action.element_id, label=action.label),
            DemoEvent(type="wait", duration_ms=850),
            DemoEvent(type="highlight.hide", element_id=action.element_id),
        ]

    def _highlight_elements(self, element_ids: list[str]) -> list[DemoEvent]:
        events: list[DemoEvent] = []
        for element_id in element_ids:
            events.extend(
                [
                    DemoEvent(type="cursor.move", element_id=element_id, duration_ms=520),
                    DemoEvent(
                        type="highlight.show",
                        element_id=element_id,
                        label=self._element_label(element_id),
                    ),
                    DemoEvent(type="wait", duration_ms=900),
                    DemoEvent(type="highlight.hide", element_id=element_id),
                ]
            )
        return events

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
        planner_setting = os.getenv("LIVE_DEMO_PLANNER", "openai").lower()
        if planner_setting in {"0", "false", "off", "disabled"}:
            return None
        api_key = settings.resolved_llm_api_key
        if not api_key:
            return None

        allowed_page_ids = {page.page_id for page in self.manifest.pages}
        allowed_element_ids = {
            element.id for page in self.manifest.pages for element in page.elements
        }
        allowed_action_ids = {
            action.id
            for page in self.manifest.pages
            for action in page.allowed_actions
            if not action.requires_approval
        }
        allowed_flow_ids = {flow.id for flow in self.manifest.flows}
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
                        "You must choose only from the provided manifest. The manifest contains "
                        "global product knowledge plus page-local allowed_actions. "
                        "For a broad walkthrough, return mode='flow' and a flow_id. "
                        "For a local question, return mode='actions', one approved page_id, "
                        "and action_ids from that page's allowed_actions. Prefer action_ids over raw element_ids. "
                        "Do not invent pages, elements, selectors, actions, claims, or flows. "
                        "Return strict JSON only: {\"mode\":\"flow|actions\",\"reply\":\"string\","
                        "\"flow_id\":\"string|null\",\"page_id\":\"string\",\"action_ids\":[\"string\"],"
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

        if raw.get("mode") == "flow":
            flow = self._flow_by_id(str(raw.get("flow_id") or "")) or self._primary_flow()
            if flow is not None:
                return self._build_guided_walkthrough_decision(flow)

        page_id = raw.get("page_id")
        if page_id not in allowed_page_ids:
            return None
        action_ids = [
            action_id
            for action_id in raw.get("action_ids", [])
            if isinstance(action_id, str) and action_id in allowed_action_ids
        ][:4]
        element_ids = [
            element_id
            for element_id in raw.get("element_ids", [])
            if isinstance(element_id, str) and element_id in allowed_element_ids
        ][:4]
        if not element_ids and action_ids:
            page = self._page_by_id(page_id)
            if page is not None:
                element_ids = [
                    action.element_id
                    for action in self._actions_by_ids(page, action_ids)
                    if action.element_id
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
            "action_ids": action_ids,
            "state": state,
            "lead_patch": cleaned_patch,
            "reply": str(raw.get("reply") or "").strip()
            or f"I will show the {self._page_by_id(page_id).title.lower()} step.",
        }

    def _manifest_context(self, message: str, current_page: DemoPageManifest) -> dict[str, object]:
        return {
            "product_name": self.manifest.product_name,
            "target_persona": self.manifest.target_persona,
            "cta": self.manifest.cta,
            "current_page": self._page_context(current_page),
            "all_page_actions": [self._page_context(page) for page in self.manifest.pages],
            "page_index": [
                {"page_id": page.page_id, "title": page.title, "summary": page.summary}
                for page in self.manifest.pages
            ],
            "flows": [flow.model_dump() for flow in self.manifest.flows],
            "knowledge": [record.model_dump() for record in self.manifest.knowledge],
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
        events.extend(self._highlight_elements(element_ids))
        if lead_patch:
            events.append(DemoEvent(type="lead.profile.updated", patch=lead_patch))
        return events

    def _build_action_events(
        self,
        reply: str,
        target_page: DemoPageManifest,
        action_ids: list[str],
        lead_patch: dict[str, object],
    ) -> list[DemoEvent]:
        actions = self._actions_by_ids(target_page, action_ids)
        events: list[DemoEvent] = [
            DemoEvent(type="say", text=reply, duration_ms=1600),
            DemoEvent(type="navigate", page_id=target_page.page_id, route=target_page.route),
            DemoEvent(type="wait", duration_ms=180),
            *self._timeline_for_actions(target_page, actions),
        ]
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
