from __future__ import annotations

from app.agents.campaign_models import CampaignCreateRequest, ProspectProfile, ReadinessScore, WorkflowStep


class ReadinessAgent:
    name = "readiness"

    def score(self, request: CampaignCreateRequest, prospect_profile: ProspectProfile) -> ReadinessScore:
        score = 86
        gaps = []
        if not request.prospect_description:
            score -= 10
            gaps.append("Prospect description was not provided; research uses assumptions.")
        if not request.product_url:
            score -= 4
            gaps.append("Product URL was not provided; strategy uses pasted product description only.")
        return ReadinessScore(
            score=score,
            verdict="ready" if score >= 80 else "needs_more_context",
            strengths=[
                "Clear product positioning",
                f"Specific relevance angle for {prospect_profile.company_name}",
                "Demo brief includes qualifying questions and objection handling",
            ],
            gaps=gaps,
        )

    def completed_step(self) -> WorkflowStep:
        return WorkflowStep(
            name="score_readiness",
            agent=self.name,
            summary="Scored the demo room for personalization and launch readiness.",
        )
