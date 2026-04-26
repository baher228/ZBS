from __future__ import annotations

import json
import re
from pathlib import Path

from app.live_demo.extracted_manifest import (
    EXTRACTION_SUMMARY_PATH,
    convert_extracted_manifest,
    load_extracted_demo_manifest,
)
from app.live_demo.models import (
    DemoManifest,
    DemoSetup,
    DemoSetupCreateRequest,
    FounderDemoInput,
    utc_now,
)


class LiveDemoSetupStore:
    def __init__(self) -> None:
        self._setups: dict[str, DemoSetup] = {}
        self._active_startup_id: str | None = None

    def create(self, request: DemoSetupCreateRequest) -> DemoSetup:
        startup_id = request.startup_id or self._startup_id_from_input(request.founder_input)
        if request.source == "provided_manifest":
            if request.manifest is None:
                raise ValueError("provided_manifest source requires manifest")
            manifest = request.manifest.model_copy(update={"startup_id": startup_id})
        else:
            manifest = self._manifest_from_cached_extraction(startup_id, request.founder_input)

        setup = DemoSetup(
            startup_id=startup_id,
            founder_input=request.founder_input,
            manifest=manifest,
            status="approved" if request.approve else "draft",
            source=request.source,
        )
        self._setups[startup_id] = setup
        self._active_startup_id = startup_id
        return setup

    def ensure_default_setup(self) -> DemoSetup:
        if self._active_startup_id and self._active_startup_id in self._setups:
            return self._setups[self._active_startup_id]

        founder_input = FounderDemoInput(
            product_name="Demeo",
            product_description=(
                "Demeo is an AI demo-room builder for technical B2B founders. "
                "It turns a product URL, founder walkthrough, approved knowledge, "
                "and safe actions into a shareable buyer demo room with an AI demo "
                "agent inside it. The demo agent shows the product, answers buyer "
                "questions, qualifies the lead, and prepares follow-up for the founder."
            ),
            product_url="http://127.0.0.1:5175",
            target_customer="technical B2B startup founders selling software",
            prospect_description="a founder evaluating whether Demeo can demo their own startup",
            demo_goals=[
                "show what a founder provides during setup",
                "show the prospect demo room",
                "show the founder what they receive after a prospect finishes the demo",
            ],
            founder_walkthrough=(
                "Start by showing how the founder enters company and product context. "
                "Then show the prospect demo room where a buyer can ask questions. "
                "Finally show the CRM summary and follow-up output that qualifies the lead."
            ),
            cta="book a founder onboarding call",
            qualification_questions=[
                "What product do you want Demeo to demo?",
                "Do you have a safe sandbox or staging account?",
                "Who is the target buyer?",
            ],
        )
        return self.create(
            DemoSetupCreateRequest(
                startup_id="demeo_current_app",
                founder_input=founder_input,
                source="cached_extraction",
                approve=True,
            )
        )

    def get(self, startup_id: str) -> DemoSetup | None:
        return self._setups.get(startup_id)

    def get_active(self) -> DemoSetup:
        return self.ensure_default_setup()

    def approve(self, startup_id: str, approved: bool = True) -> DemoSetup | None:
        setup = self._setups.get(startup_id)
        if setup is None:
            return None
        updated = setup.model_copy(
            update={"status": "approved" if approved else "draft", "updated_at": utc_now()}
        )
        self._setups[startup_id] = updated
        if approved:
            self._active_startup_id = startup_id
        return updated

    def manifest_for(self, startup_id: str | None = None) -> DemoManifest:
        setup = self.get(startup_id) if startup_id else self.get_active()
        if setup is None:
            raise KeyError(startup_id or "active")
        if setup.status != "approved":
            raise PermissionError("Demo setup is not approved")
        return setup.manifest

    def clear(self) -> None:
        self._setups.clear()
        self._active_startup_id = None

    def _manifest_from_cached_extraction(
        self,
        startup_id: str,
        founder_input: FounderDemoInput,
    ) -> DemoManifest:
        if not EXTRACTION_SUMMARY_PATH.exists():
            return load_extracted_demo_manifest().model_copy(update={"startup_id": startup_id})

        summary = json.loads(Path(EXTRACTION_SUMMARY_PATH).read_text())
        manifest_json = _pick_best_manifest_json(summary)
        if manifest_json is None:
            return load_extracted_demo_manifest().model_copy(update={"startup_id": startup_id})
        return convert_extracted_manifest(
            manifest_json=manifest_json,
            founder_input=founder_input.model_dump(),
            startup_id=startup_id,
        )

    def _startup_id_from_input(self, founder_input: FounderDemoInput) -> str:
        base = re.sub(r"[^a-z0-9]+", "_", founder_input.product_name.lower()).strip("_")
        return f"{base or 'startup'}_demo"


def _pick_best_manifest_json(summary: dict) -> dict | None:
    conditions = summary.get("conditions", {})
    for name in ("screenshot_assisted", "url_walkthrough", "url_only"):
        condition = conditions.get(name)
        if isinstance(condition, dict) and isinstance(condition.get("manifest"), dict):
            return condition["manifest"]
    return None


live_demo_setup_store = LiveDemoSetupStore()
