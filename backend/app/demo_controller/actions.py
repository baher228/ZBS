from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from app.demo_controller.models import BrowserAction, DemoActionManifest, DemoSession


TRACEPILOT_ROUTES = {
    "dashboard": "/sandbox/tracepilot/render",
    "traces": "/sandbox/tracepilot/render/traces",
    "tool_call": "/sandbox/tracepilot/render/tool-call",
    "state_diff": "/sandbox/tracepilot/render/state-diff",
    "alerts": "/sandbox/tracepilot/render/alerts",
}

TRACEPILOT_TARGETS = {
    "dashboard": "render-dashboard",
    "traces": "trace-timeline",
    "tool_call": "tool-call-detail",
    "state_diff": "state-diff",
    "alerts": "alert-setup",
}

TRACEPILOT_ALLOWED_SELECTORS = [
    "[data-demo-id='render-dashboard']",
    "[data-demo-id='trace-timeline']",
    "[data-demo-id='tool-call-detail']",
    "[data-demo-id='state-diff']",
    "[data-demo-id='alert-setup']",
    "[data-demo-id='open-traces']",
    "[data-demo-id='open-tool-call']",
    "[data-demo-id='open-state-diff']",
    "[data-demo-id='open-alerts']",
    "[data-demo-id='slack-toggle']",
    "[data-demo-id='linear-toggle']",
    "[data-demo-id='pagerduty-toggle']",
]

LOW_RISK_ACTIONS = {"navigate", "hover", "wait_for", "assert_visible", "snapshot", "screenshot"}
MEDIUM_RISK_ACTIONS = {"click", "fill", "select"}
BLOCKED_ACTIONS = {"arbitrary_js", "external_navigation", "file_upload", "download"}


@dataclass(frozen=True)
class ActionValidationResult:
    allowed: bool
    reason: str | None = None
    needs_approval: bool = False


def build_tracepilot_manifest(app_base_url: str) -> DemoActionManifest:
    return DemoActionManifest(
        scenario="tracepilot_render",
        app_base_url=app_base_url,
        allowed_routes=TRACEPILOT_ROUTES,
        allowed_selectors=TRACEPILOT_ALLOWED_SELECTORS,
        demo_targets=TRACEPILOT_TARGETS,
        workflow_steps=["dashboard", "traces", "tool_call", "state_diff", "alerts"],
    )


def absolute_demo_url(app_base_url: str, path: str) -> str:
    return urljoin(app_base_url.rstrip("/") + "/", path.lstrip("/"))


def is_allowed_local_url(app_base_url: str, candidate_url: str) -> bool:
    base = urlparse(app_base_url)
    candidate = urlparse(candidate_url)
    if candidate.scheme not in {"http", "https"}:
        return False
    if candidate.hostname not in {"localhost", "127.0.0.1", "::1"}:
        return False
    return candidate.scheme == base.scheme and candidate.netloc == base.netloc


def route_id_for_url(manifest: DemoActionManifest, url: str) -> str | None:
    parsed = urlparse(url)
    for route_id, path in manifest.allowed_routes.items():
        if parsed.path.rstrip("/") == path.rstrip("/"):
            return route_id
    return None


def demo_ids_for_route(route_id: str | None) -> list[str]:
    if route_id is None:
        return []
    target = TRACEPILOT_TARGETS.get(route_id)
    if target is None:
        return []
    ids = [target]
    if route_id != "dashboard":
        ids.append("tracepilot-shell")
    return ids


def action_for_step(session: DemoSession, step_id: str, label: str | None = None) -> BrowserAction:
    route = session.manifest.allowed_routes[step_id]
    target = session.manifest.demo_targets[step_id]
    return BrowserAction(
        type="navigate",
        label=label or f"Open {step_id.replace('_', ' ')}",
        step_id=step_id,
        route_id=step_id,
        url=absolute_demo_url(session.app_base_url, route),
        expected_demo_id=target,
        risk="low",
    )


def verification_action_for_step(step_id: str) -> BrowserAction:
    target = TRACEPILOT_TARGETS[step_id]
    return BrowserAction(
        type="assert_visible",
        label=f"Verify {target} is visible",
        step_id=step_id,
        selector=f"[data-demo-id='{target}']",
        expected_demo_id=target,
        risk="low",
    )


def screenshot_action_for_step(step_id: str) -> BrowserAction:
    return BrowserAction(
        type="screenshot",
        label=f"Capture {step_id.replace('_', ' ')} screenshot",
        step_id=step_id,
        risk="low",
    )


def validate_action(session: DemoSession, action: BrowserAction) -> ActionValidationResult:
    if action.type in BLOCKED_ACTIONS:
        return ActionValidationResult(False, f"{action.type} is blocked in the demo controller")

    if action.type == "navigate":
        if not action.url:
            return ActionValidationResult(False, "navigate action requires a URL")
        if not is_allowed_local_url(session.app_base_url, action.url):
            return ActionValidationResult(False, "external navigation is blocked")
        if route_id_for_url(session.manifest, action.url) is None:
            return ActionValidationResult(False, "URL is not in the demo manifest")

    if action.selector and action.selector not in session.manifest.allowed_selectors:
        return ActionValidationResult(False, "selector is not in the demo manifest")

    if action.type in MEDIUM_RISK_ACTIONS and session.mode != "bounded_auto" and action.status != "approved":
        return ActionValidationResult(True, "manual approval required", needs_approval=True)

    if action.risk in {"medium", "high"} and action.status != "approved":
        return ActionValidationResult(True, "approval required", needs_approval=True)

    return ActionValidationResult(True)


def scripted_tracepilot_plan(session: DemoSession, message: str | None) -> tuple[str, list[BrowserAction]]:
    text = (message or "").lower()
    actions: list[BrowserAction] = []

    if any(term in text for term in ["privacy", "redaction", "security", "pii"]):
        return (
            "TracePilot redacts prompt payloads before they leave the agent runtime and keeps raw tool inputs out of the demo surface. For Render, I would focus the browser on trace metadata, latency, retries, and the sanitized state diff.",
            [],
        )

    if any(term in text for term in ["alert", "slack", "linear", "pagerduty", "catch this next time"]):
        actions.append(action_for_step(session, "alerts", "Open alert setup"))
        reply = "I opened the alert workflow. This is where Render can route failed-agent spikes to Slack, create a Linear issue, and page only when retries keep failing."
    elif any(term in text for term in ["why", "root cause", "state", "diff", "fail"]):
        if "walk" in text or "through" in text or "failure" in text:
            actions.extend(
                [
                    action_for_step(session, "dashboard", "Open Render service dashboard"),
                    action_for_step(session, "traces", "Open TracePilot trace timeline"),
                    action_for_step(session, "tool_call", "Inspect failed tool call"),
                ]
            )
            reply = "I walked into the failing run: first the Render worker health, then the TracePilot timeline, and now the failed tool call where the timeout happened."
        else:
            actions.append(action_for_step(session, "state_diff", "Open state diff"))
            reply = "I opened the state diff. The run failed because the timed-out deploy lookup left the planner with a stale service version and the next step used the wrong rollout target."
    elif any(term in text for term in ["tool", "call", "inspect", "request", "response", "timeout"]):
        actions.append(action_for_step(session, "tool_call", "Inspect failed tool call"))
        reply = "I opened the failed tool-call panel. The key signal is the 2.4s timeout, two retries, and a redacted payload that still preserves the operation and service identifiers."
    elif any(term in text for term in ["trace", "timeline", "show the failure"]):
        actions.append(action_for_step(session, "traces", "Open TracePilot trace timeline"))
        reply = "I opened the trace timeline so you can see the prompt, planner, tool call, state transition, and failed output in order."
    else:
        actions.append(action_for_step(session, "dashboard", "Open Render service dashboard"))
        reply = "I opened the Render service dashboard. This starts from the operational view your team would recognize before drilling into the failed AI-worker run."

    enriched_actions: list[BrowserAction] = []
    for action in actions:
        enriched_actions.append(action)
        if action.step_id:
            enriched_actions.append(verification_action_for_step(action.step_id))
    if actions:
        enriched_actions.append(screenshot_action_for_step(actions[-1].step_id or "dashboard"))
    return reply, enriched_actions
