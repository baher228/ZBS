from __future__ import annotations

from uuid import uuid4

from app.agents.campaign_models import WorkflowStep


class OrchestratorAgent:
    name = "orchestrator"

    def initialize_campaign(self) -> dict:
        return {
            "campaign_id": f"camp_{uuid4().hex[:12]}",
            "demo_room_id": f"room_{uuid4().hex[:12]}",
            "workflow_steps": [
                WorkflowStep(
                    name="orchestrate_campaign",
                    agent=self.name,
                    summary="Initialized campaign state and routed to GTM strategy.",
                )
            ],
        }

    def persisted_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="persist_demo_room",
            agent=self.name,
            summary="Stored the campaign package and personalized demo room.",
        )
