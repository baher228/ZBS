from __future__ import annotations

from collections.abc import Iterable

from app.agents.models import AgentCapability, AgentRequest, AgentResponse, ReviewResult, ReviewStatus


class ReviewAgent:
    _required_sections = {
        AgentCapability.CONTENT_GENERATOR: {
            "positioning",
            "landing_copy",
            "icp_notes",
            "launch_email",
            "social_post",
        },
        AgentCapability.LEGAL: {
            "important_notice",
            "jurisdiction_scope",
            "relevant_sources",
            "risk_summary",
            "founder_checklist",
            "questions_for_counsel",
            "next_steps",
        },
    }

    def review(self, request: AgentRequest, response: AgentResponse) -> ReviewResult:
        required_sections = self._required_sections.get(response.agent, set(response.output.keys()))
        filled_sections = {
            key for key, value in response.output.items() if key in required_sections and value.strip()
        }
        output_text = " ".join(response.output.values()).lower()
        prompt_terms = self._terms(request.prompt)
        idea_terms = self._terms(request.startup_idea or "")
        relevant_terms = prompt_terms | idea_terms

        relevance = self._score_relevance(output_text, relevant_terms)
        completeness = len(filled_sections) / max(1, len(required_sections))
        clarity = self._score_clarity(response.output.values())
        actionability = self._score_actionability(output_text, response.agent)
        score = round((relevance + completeness + clarity + actionability) / 4, 2)

        if not response.output or score < 0.4:
            return ReviewResult(
                status=ReviewStatus.FAILED,
                score=score,
                relevance=relevance,
                completeness=completeness,
                clarity=clarity,
                actionability=actionability,
                feedback="The result is too thin or disconnected from the task.",
                revision_instruction=self._revision_instruction(response.agent),
            )

        if score < 0.75 or completeness < 1:
            return ReviewResult(
                status=ReviewStatus.REVISE,
                score=score,
                relevance=relevance,
                completeness=completeness,
                clarity=clarity,
                actionability=actionability,
                feedback=self._feedback(response.agent, passed=False),
                revision_instruction=self._revision_instruction(response.agent),
            )

        return ReviewResult(
            status=ReviewStatus.APPROVED,
            score=score,
            relevance=relevance,
            completeness=completeness,
            clarity=clarity,
            actionability=actionability,
            feedback=self._feedback(response.agent, passed=True),
        )

    def _terms(self, text: str) -> set[str]:
        return {term.strip(".,!?;:()[]").lower() for term in text.split() if len(term) > 3}

    def _score_relevance(self, output_text: str, terms: set[str]) -> float:
        if not output_text.strip():
            return 0
        if not terms:
            return 0.8
        matches = sum(1 for term in terms if term in output_text)
        return round(min(1, matches / max(2, len(terms) * 0.4)), 2)

    def _score_clarity(self, values: Iterable[str]) -> float:
        sections = [value.strip() for value in values if value.strip()]
        if not sections:
            return 0
        clear_sections = [
            value for value in sections if 20 <= len(value) <= 1400 and "TODO" not in value.upper()
        ]
        return round(len(clear_sections) / len(sections), 2)

    def _score_actionability(self, output_text: str, capability: AgentCapability) -> float:
        if not output_text.strip():
            return 0
        action_words = ["prioritize", "look for", "subject:", "launch", "start", "review", "next"]
        if capability == AgentCapability.LEGAL:
            action_words.extend(["counsel", "privacy", "claims", "notice", "terms"])
        matches = sum(1 for word in action_words if word in output_text)
        return round(min(1, matches / 4), 2)

    def _feedback(self, capability: AgentCapability, passed: bool) -> str:
        if capability == AgentCapability.LEGAL:
            if passed:
                return "The issue scan is source-grounded, complete, and gives the founder clear next steps for counsel review."
            return "The issue scan is useful but needs stronger citations, clearer counsel handoff questions, or more launch-specific guidance."
        if passed:
            return "The result is relevant, complete, clear, and actionable."
        return "The result is usable but needs more complete and specific GTM assets."

    def _revision_instruction(self, capability: AgentCapability) -> str:
        if capability == AgentCapability.LEGAL:
            return (
                "Add the missing legal sections, cite the most relevant public guidance, and make the counsel handoff more specific to the launch."
            )
        return (
            "Add all required sections and make each section more specific to the startup idea, audience, and goal."
        )
