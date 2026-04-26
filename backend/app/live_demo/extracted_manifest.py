from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.live_demo.manifest import DEMO_MANIFEST as FALLBACK_MANIFEST
from app.live_demo.models import (
    DemoElement,
    DemoFlow,
    DemoFlowStep,
    DemoManifest,
    DemoPageManifest,
    KnowledgeRecord,
    PageAction,
)


BACKEND_ROOT = Path(__file__).resolve().parents[2]
EXTRACTION_SUMMARY_PATH = BACKEND_ROOT / "tools" / "extraction_reports" / "summary.json"

ROLE_BY_ACTION_TYPE = {
    "click": "button",
    "navigate": "link",
    "highlight": "section",
    "answer": "section",
}


def load_extracted_demo_manifest(path: Path = EXTRACTION_SUMMARY_PATH) -> DemoManifest:
    if not path.exists():
        return FALLBACK_MANIFEST

    summary = json.loads(path.read_text())
    manifest_json = _pick_manifest(summary)
    if manifest_json is None:
        return FALLBACK_MANIFEST
    return convert_extracted_manifest(
        manifest_json=manifest_json,
        founder_input=summary.get("founder_input", {}),
        startup_id="demeo_extracted",
    )


def convert_extracted_manifest(
    manifest_json: dict[str, Any],
    founder_input: dict[str, Any],
    startup_id: str,
) -> DemoManifest:
    pages = [_convert_page(page) for page in manifest_json.get("pages", [])]
    pages = [page for page in pages if page.page_id]
    if not pages:
        return FALLBACK_MANIFEST

    flows = [_convert_flow(flow, pages) for flow in manifest_json.get("flows", [])]
    flows = [flow for flow in flows if flow.steps]
    if not flows:
        flows = [
            DemoFlow(
                id="extracted_primary_flow",
                name="Extracted product walkthrough",
                goal="Guide the prospect through the extracted product pages.",
                entry_page_id=pages[0].page_id,
                steps=[
                    DemoFlowStep(
                        id=f"step_{page.page_id}",
                        page_id=page.page_id,
                        objective=page.summary,
                        talk_track=page.summary,
                        recommended_action_ids=[action.id for action in page.allowed_actions[:2]],
                    )
                    for page in pages[:5]
                ],
            )
        ]

    approved_answers = manifest_json.get("approved_answers", [])
    knowledge = [
        KnowledgeRecord(
            id=f"approved_{index}",
            topic=str(answer.get("topic") or answer.get("question") or f"approved answer {index + 1}"),
            content=str(answer.get("answer") or answer.get("content") or ""),
            tags=["approved_answer"],
        )
        for index, answer in enumerate(approved_answers)
        if answer.get("answer") or answer.get("content")
    ]
    if not knowledge:
        knowledge = [
            KnowledgeRecord(
                id="extracted_notes",
                topic="extracted demo notes",
                content=" ".join(str(note) for note in manifest_json.get("notes", [])),
                tags=["extracted"],
            )
        ]

    return DemoManifest(
        startup_id=startup_id,
        product_name=str(founder_input.get("product_name") or "Demeo extracted demo"),
        target_persona=str(
            founder_input.get("prospect_description")
            or founder_input.get("target_customer")
            or "Founder evaluating an AI demo room"
        ),
        cta=str(founder_input.get("cta") or "Book a setup call"),
        pages=pages,
        flows=flows,
        knowledge=knowledge,
        qualification_questions=[
            str(question) for question in founder_input.get("qualification_questions", [])
        ],
        restricted_claims=[
            "Do not invent pricing, customer claims, security claims, integrations, or roadmap commitments.",
            "Do not perform destructive or production-changing actions.",
        ],
    )


def _pick_manifest(summary: dict[str, Any]) -> dict[str, Any] | None:
    conditions = summary.get("conditions", {})
    for name in ("screenshot_assisted", "url_walkthrough", "url_only"):
        condition = conditions.get(name)
        if isinstance(condition, dict) and isinstance(condition.get("manifest"), dict):
            return condition["manifest"]
    for condition in conditions.values():
        if isinstance(condition, dict) and isinstance(condition.get("manifest"), dict):
            return condition["manifest"]
    return None


def _convert_page(page: dict[str, Any]) -> DemoPageManifest:
    page_id = str(page.get("page_id") or "").strip() or "page"
    elements = [_convert_element(element) for element in page.get("important_elements", [])]
    actions = [_convert_action(action) for action in page.get("allowed_actions", [])]
    element_ids = {element.id for element in elements}
    for action in actions:
        if action.element_id and action.element_id not in element_ids:
            elements.append(
                DemoElement(
                    id=action.element_id,
                    label=action.label,
                    role=ROLE_BY_ACTION_TYPE.get(action.type, "section"),
                    description=action.intent,
                    selector=_selector_from_element_id(action.element_id),
                    safe_to_click=action.type == "click",
                    requires_approval=action.type == "click",
                )
            )
            element_ids.add(action.element_id)
    return DemoPageManifest(
        page_id=page_id,
        route=str(page.get("route") or f"/{page_id}"),
        title=str(page.get("purpose") or page_id.replace("_", " ").title()),
        summary=str(page.get("purpose") or ""),
        visible_concepts=[
            str(element.get("label") or element.get("why") or "")
            for element in page.get("important_elements", [])[:5]
            if element.get("label") or element.get("why")
        ],
        elements=elements,
        allowed_actions=actions,
    )


def _convert_element(element: dict[str, Any]) -> DemoElement:
    element_id = str(element.get("element_id") or element.get("label") or "element")
    return DemoElement(
        id=element_id,
        label=str(element.get("label") or element_id),
        role="section",
        description=str(element.get("why") or element.get("label") or element_id),
        selector=str(element.get("selector_hint") or _selector_from_element_id(element_id)),
    )


def _convert_action(action: dict[str, Any]) -> PageAction:
    action_type = str(action.get("type") or "highlight")
    if action_type not in {"highlight", "cursor.move", "click", "navigate"}:
        action_type = "highlight"
    return PageAction(
        id=str(action.get("action_id") or action.get("label") or "action"),
        type=action_type,
        label=str(action.get("label") or action.get("intent") or action_type),
        element_id=action.get("element_id"),
        target_page_id=action.get("target_page_id"),
        intent=str(action.get("intent") or action.get("label") or ""),
        requires_approval=action_type == "click",
    )


def _convert_flow(flow: dict[str, Any], pages: list[DemoPageManifest]) -> DemoFlow:
    valid_page_ids = {page.page_id for page in pages}
    steps = []
    for index, step in enumerate(flow.get("steps", [])):
        page_id = str(step.get("page_id") or "")
        if page_id not in valid_page_ids:
            continue
        steps.append(
            DemoFlowStep(
                id=f"{flow.get('flow_id') or 'flow'}_{index}",
                page_id=page_id,
                objective=str(step.get("say") or step.get("objective") or page_id),
                talk_track=str(step.get("say") or ""),
                recommended_action_ids=[
                    str(step["action_id"])
                ]
                if step.get("action_id")
                else [],
            )
        )
    return DemoFlow(
        id=str(flow.get("flow_id") or "extracted_flow"),
        name=str(flow.get("goal") or flow.get("flow_id") or "Extracted flow"),
        goal=str(flow.get("goal") or "Guide the prospect through the extracted app."),
        entry_page_id=steps[0].page_id if steps else pages[0].page_id,
        steps=steps,
    )


def _selector_from_element_id(element_id: str) -> str:
    return f"[data-demo-id='{element_id}']"
