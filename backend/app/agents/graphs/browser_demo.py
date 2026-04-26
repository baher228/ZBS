from __future__ import annotations

from fastapi import HTTPException
from langgraph.graph import END, START, StateGraph

from app.demo_controller.actions import scripted_tracepilot_plan, validate_action
from app.demo_controller.models import BrowserDemoGraphState, BrowserObservation
from app.demo_controller.playwright_controller import BrowserControllerError, PlaywrightBrowserController
from app.demo_controller.store import InMemoryDemoSessionStore
from app.agents.store import campaign_store


class BrowserDemoGraphRunner:
    def __init__(
        self,
        store: InMemoryDemoSessionStore,
        browser_controller: PlaywrightBrowserController | None = None,
    ) -> None:
        self.store = store
        self.browser_controller = browser_controller or PlaywrightBrowserController()
        self.graph = self._compile_graph()

    def run(self, session_id: str, message: str | None = None):
        state = self.graph.invoke({"session_id": session_id, "message": message})
        return state["session"]

    def _compile_graph(self):
        graph = StateGraph(BrowserDemoGraphState)
        graph.add_node("load_session", self._load_session)
        graph.add_node("observe_browser", self._observe_browser)
        graph.add_node("plan_next_step", self._plan_next_step)
        graph.add_node("safety_gate", self._safety_gate)
        graph.add_node("execute_actions", self._execute_actions)
        graph.add_node("verify_result", self._verify_result)
        graph.add_node("persist_session", self._persist_session)
        graph.add_edge(START, "load_session")
        graph.add_edge("load_session", "observe_browser")
        graph.add_edge("observe_browser", "plan_next_step")
        graph.add_edge("plan_next_step", "safety_gate")
        graph.add_edge("safety_gate", "execute_actions")
        graph.add_edge("execute_actions", "verify_result")
        graph.add_edge("verify_result", "persist_session")
        graph.add_edge("persist_session", END)
        return graph.compile()

    def _load_session(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = self.store.get_session(state["session_id"])
        if session is None:
            raise HTTPException(status_code=404, detail="Demo session not found")
        return {"session": session}

    def _observe_browser(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        observation = self.browser_controller.observe(state["session"])
        return {"observation": observation}

    def _plan_next_step(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = state["session"].model_copy(update={"status": "planning", "last_error": None})
        reply, actions = scripted_tracepilot_plan(session, state.get("message"))
        return {"session": session, "reply": reply, "planned_actions": actions}

    def _safety_gate(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = state["session"]
        executable = []
        rejected = []
        pending = []

        for action in state.get("planned_actions", []):
            validation = validate_action(session, action)
            if not validation.allowed:
                rejected.append(
                    action.model_copy(update={"status": "rejected", "reason": validation.reason})
                )
            elif validation.needs_approval:
                pending.append(
                    action.model_copy(update={"status": "pending", "reason": validation.reason})
                )
            else:
                executable.append(action)

        status = "acting" if executable else "ready"
        if pending:
            status = "waiting_for_approval"
        if rejected and not executable and not pending:
            status = "failed"

        session = session.model_copy(update={"status": status, "pending_actions": pending})
        return {
            "session": session,
            "executable_actions": executable,
            "rejected_actions": rejected,
        }

    def _execute_actions(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = state["session"]
        executable = state.get("executable_actions", [])
        if not executable:
            return {}
        try:
            executed_actions, observations = self.browser_controller.execute(session, executable)
        except BrowserControllerError as exc:
            return {
                "session": session.model_copy(update={"status": "failed", "last_error": str(exc)}),
                "executable_actions": [],
                "metadata": {"execution_error": str(exc)},
            }

        executed_count = len([action for action in executed_actions if action.status == "executed"])
        current_step_id = session.current_step_id
        for action in executed_actions:
            if action.status == "executed" and action.step_id:
                current_step_id = action.step_id

        updates = {
            "status": "verifying",
            "action_budget": max(session.action_budget - executed_count, 0),
            "current_step_id": current_step_id,
        }
        if any(action.status == "failed" for action in executed_actions):
            updates["status"] = "failed"
            updates["last_error"] = "A browser assertion failed."

        return {
            "session": session.model_copy(update=updates),
            "executable_actions": executed_actions,
            "metadata": {"observations": observations},
        }

    def _verify_result(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = state["session"]
        observations: list[BrowserObservation] = state.get("metadata", {}).get("observations", [])
        observation = observations[-1] if observations else state["observation"]
        if session.status == "failed":
            return {"verification_results": []}
        result = self.browser_controller.verify(session, observation)
        status = "ready" if result.passed else "failed"
        return {
            "session": session.model_copy(
                update={
                    "status": status,
                    "last_error": None if result.passed else result.message,
                }
            ),
            "verification_results": [result],
        }

    def _persist_session(self, state: BrowserDemoGraphState) -> BrowserDemoGraphState:
        session = state["session"]
        observations: list[BrowserObservation] = state.get("metadata", {}).get("observations", [])
        action_log = [
            *session.action_log,
            *state.get("rejected_actions", []),
            *state.get("executable_actions", []),
            *session.pending_actions,
        ]
        verification_log = [
            *session.verification_log,
            *state.get("verification_results", []),
        ]
        transcript = session.transcript
        if state.get("message") and state.get("reply"):
            from app.agents.campaign_models import ChatMessage

            transcript = [
                *transcript,
                ChatMessage(role="user", content=state["message"] or ""),
                ChatMessage(role="assistant", content=state["reply"]),
            ]

        updated = self.store.save_session(
            session.model_copy(
                update={
                    "transcript": transcript,
                    "action_log": action_log,
                    "observations": [*session.observations, *observations],
                    "verification_log": verification_log,
                }
            )
        )
        if state.get("message") and state.get("reply"):
            campaign_store.append_demo_messages(
                updated.demo_room_id,
                state["message"] or "",
                state["reply"],
            )
        return {"session": updated}
