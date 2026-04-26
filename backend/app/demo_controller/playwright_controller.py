from __future__ import annotations

from urllib.parse import urlparse

from app.demo_controller.actions import demo_ids_for_route, route_id_for_url, validate_action
from app.demo_controller.models import (
    BrowserAction,
    BrowserObservation,
    DemoSession,
    VerificationResult,
    utc_now,
)


class BrowserControllerError(RuntimeError):
    pass


class PlaywrightBrowserController:
    """Bounded browser executor.

    The MVP keeps execution deterministic so API tests do not require installed
    browsers. If a real Playwright page is injected later, the same allowlisted
    BrowserAction objects remain the execution boundary.
    """

    def observe(self, session: DemoSession) -> BrowserObservation:
        if session.observations:
            return session.observations[-1]
        dashboard_url = f"{session.app_base_url.rstrip('/')}/sandbox/tracepilot/render"
        return self._observation_for_url(session, dashboard_url)

    def execute(self, session: DemoSession, actions: list[BrowserAction]) -> tuple[list[BrowserAction], list[BrowserObservation]]:
        if len(actions) > session.action_budget:
            raise BrowserControllerError("action budget exhausted")

        observations: list[BrowserObservation] = []
        current_observation = self.observe(session)
        remaining_budget = session.action_budget
        executed_actions: list[BrowserAction] = []

        for action in actions:
            if remaining_budget <= 0:
                raise BrowserControllerError("action budget exhausted")

            validation = validate_action(session, action)
            if not validation.allowed:
                executed_actions.append(
                    action.model_copy(
                        update={
                            "status": "rejected",
                            "reason": validation.reason,
                        }
                    )
                )
                continue

            if validation.needs_approval:
                executed_actions.append(
                    action.model_copy(
                        update={
                            "status": "pending",
                            "reason": validation.reason,
                        }
                    )
                )
                continue

            if action.type == "navigate":
                if action.url is None:
                    raise BrowserControllerError("navigate action requires a URL")
                current_observation = self._observation_for_url(session, action.url)
                observations.append(current_observation)
            elif action.type == "assert_visible":
                if action.expected_demo_id and action.expected_demo_id not in current_observation.visible_demo_ids:
                    executed_actions.append(
                        action.model_copy(
                            update={
                                "status": "failed",
                                "reason": f"{action.expected_demo_id} was not visible",
                                "executed_at": utc_now(),
                            }
                        )
                    )
                    remaining_budget -= 1
                    continue
            elif action.type == "screenshot":
                screenshot_path = f"memory://{session.id}/{action.step_id or 'current'}.png"
                current_observation = current_observation.model_copy(
                    update={"screenshot_path": screenshot_path, "captured_at": utc_now()}
                )
                observations.append(current_observation)
            elif action.type in {"click", "fill", "select", "hover", "wait_for", "snapshot"}:
                # These stay bounded by selector and route validation. The MVP
                # records them without running arbitrary JavaScript.
                pass
            else:
                executed_actions.append(
                    action.model_copy(update={"status": "rejected", "reason": "unsupported action"})
                )
                continue

            executed_actions.append(
                action.model_copy(update={"status": "executed", "executed_at": utc_now()})
            )
            remaining_budget -= 1

        return executed_actions, observations

    def verify(self, session: DemoSession, observation: BrowserObservation | None = None) -> VerificationResult:
        observed = observation or self.observe(session)
        target = None
        if session.current_step_id:
            target = session.manifest.demo_targets.get(session.current_step_id)

        if target is None:
            return VerificationResult(
                step_id=session.current_step_id,
                passed=True,
                message="No active step requires visual verification.",
                observed_demo_ids=observed.visible_demo_ids,
            )

        passed = target in observed.visible_demo_ids
        return VerificationResult(
            step_id=session.current_step_id,
            passed=passed,
            message=f"{target} is visible." if passed else f"{target} is not visible.",
            expected_demo_id=target,
            observed_demo_ids=observed.visible_demo_ids,
        )

    def _observation_for_url(self, session: DemoSession, url: str) -> BrowserObservation:
        route_id = route_id_for_url(session.manifest, url)
        parsed = urlparse(url)
        title = "TracePilot sandbox"
        if route_id:
            title = f"TracePilot / Render / {route_id.replace('_', ' ')}"
        return BrowserObservation(
            url=f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            route_id=route_id,
            visible_demo_ids=demo_ids_for_route(route_id),
            title=title,
        )
