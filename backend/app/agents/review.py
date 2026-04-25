from app.agents.models import AgentRequest, AgentResponse, ReviewResult, ReviewStatus


class ReviewAgent:
    _required_sections = {
        "positioning",
        "landing_copy",
        "icp_notes",
        "launch_email",
        "social_post",
    }
    _required_sections_by_agent = {
        "legal": {
            "important_notice",
            "jurisdiction_scope",
            "relevant_sources",
            "risk_summary",
            "founder_checklist",
            "questions_for_counsel",
            "next_steps",
        }
    }

    def review(self, request: AgentRequest, response: AgentResponse) -> ReviewResult:
        required_sections = self._required_sections_by_agent.get(
            response.agent.value,
            self._required_sections,
        )
        filled_sections = {
            key
            for key, value in response.output.items()
            if key in required_sections and value.strip()
        }
        output_text = " ".join(response.output.values()).lower()
        prompt_terms = self._terms(request.prompt)
        idea_terms = self._terms(request.startup_idea or "")
        relevant_terms = prompt_terms | idea_terms

        relevance = self._score_relevance(output_text, relevant_terms)
        completeness = len(filled_sections) / len(required_sections)
        clarity = self._score_clarity(response.output.values())
        actionability = self._score_actionability(output_text)
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
                revision_instruction="Regenerate the content with concrete, task-specific GTM assets.",
            )

        if score < 0.75 or completeness < 1:
            return ReviewResult(
                status=ReviewStatus.REVISE,
                score=score,
                relevance=relevance,
                completeness=completeness,
                clarity=clarity,
                actionability=actionability,
                feedback="The result is usable but needs more complete and specific GTM assets.",
                revision_instruction=(
                    "Add all required sections and make each section more specific to "
                    "the startup idea, audience, and goal."
                ),
            )

        return ReviewResult(
            status=ReviewStatus.APPROVED,
            score=score,
            relevance=relevance,
            completeness=completeness,
            clarity=clarity,
            actionability=actionability,
            feedback="The result is relevant, complete, clear, and actionable.",
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

    def _score_clarity(self, values) -> float:
        sections = [value.strip() for value in values if value.strip()]
        if not sections:
            return 0
        clear_sections = [
            value for value in sections if 20 <= len(value) <= 700 and "TODO" not in value.upper()
        ]
        return round(len(clear_sections) / len(sections), 2)

    def _score_actionability(self, output_text: str) -> float:
        if not output_text.strip():
            return 0
        action_words = ["prioritize", "look for", "subject:", "building", "launch", "start"]
        matches = sum(1 for word in action_words if word in output_text)
        return round(min(1, matches / 3), 2)
