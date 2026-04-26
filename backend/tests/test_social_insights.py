"""Tests for social media insights extraction and contextual image generation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.agents.image_gen import _build_contextual_prompt, _fallback_prompt
from app.agents.social_insights import SocialInsights, _clean_html, _extract_snippets
from app.company.models import CompanyProfile
from app.main import create_app


# ── SocialInsights model tests ───────────────────────────────


class TestSocialInsightsModel:
    def test_empty_insights_produce_empty_context(self):
        insights = SocialInsights()
        assert insights.to_context_block() == ""

    def test_populated_insights_produce_context_block(self):
        insights = SocialInsights(
            tone="professional and bold",
            themes=["AI automation", "B2B sales", "founder life"],
            audience_signals="Technical founders at Series A startups",
            content_style="Short punchy posts with data points",
        )
        block = insights.to_context_block()
        assert "professional and bold" in block
        assert "AI automation" in block
        assert "Technical founders" in block
        assert "Short punchy" in block


# ── HTML cleaning tests ──────────────────────────────────────


class TestHtmlCleaning:
    def test_strips_tags(self):
        html = "<p>Hello <strong>world</strong></p>"
        assert "Hello" in _clean_html(html)
        assert "world" in _clean_html(html)
        assert "<p>" not in _clean_html(html)

    def test_strips_scripts(self):
        html = "<script>alert('x')</script><p>content</p>"
        result = _clean_html(html)
        assert "alert" not in result
        assert "content" in result

    def test_truncates_long_content(self):
        html = "x" * 20000
        assert len(_clean_html(html)) <= 8000


# ── Snippet extraction tests ─────────────────────────────────


class TestSnippetExtraction:
    def test_extracts_reasonable_sentences(self):
        text = (
            "This is too short. "
            "This sentence is long enough to be considered a real content snippet from a social media post. "
            "Another good snippet that discusses AI automation in B2B sales workflows effectively. "
            "Tiny."
        )
        snippets = _extract_snippets(text)
        assert len(snippets) == 2
        assert all(len(s) > 30 for s in snippets)

    def test_limits_max_snippets(self):
        text = ". ".join(
            [f"This is a sufficiently long sentence number {i} for testing snippet extraction" for i in range(20)]
        )
        snippets = _extract_snippets(text, max_snippets=5)
        assert len(snippets) <= 5


# ── CompanyProfile with social media ─────────────────────────


class TestCompanyProfileSocialMedia:
    def test_social_media_links_in_context(self):
        profile = CompanyProfile(
            name="TestCo",
            description="Test company",
            social_media_links={
                "linkedin": "https://linkedin.com/company/testco",
                "twitter": "https://x.com/testco",
            },
        )
        ctx = profile.to_context_string()
        assert "linkedin" in ctx.lower()
        assert "linkedin.com/company/testco" in ctx
        assert "x.com/testco" in ctx

    def test_social_media_links_in_markdown(self):
        profile = CompanyProfile(
            name="TestCo",
            description="Test company",
            social_media_links={
                "linkedin": "https://linkedin.com/company/testco",
            },
        )
        md = profile.to_markdown()
        assert "## Social Media" in md
        assert "linkedin.com/company/testco" in md

    def test_empty_social_links_omitted(self):
        profile = CompanyProfile(
            name="TestCo",
            description="Test company",
            social_media_links={},
        )
        ctx = profile.to_context_string()
        md = profile.to_markdown()
        assert "Social" not in ctx
        assert "Social Media" not in md

    def test_social_media_default_empty(self):
        profile = CompanyProfile(name="X", description="Y")
        assert profile.social_media_links == {}


# ── API tests for social media links ─────────────────────────


@pytest.fixture()
def _clean_data(tmp_path: Path):
    json_path = tmp_path / "company_profile.json"
    md_path = tmp_path / "company_profile.md"
    with (
        patch("app.company.storage.DATA_DIR", tmp_path),
        patch("app.company.storage.PROFILE_JSON", json_path),
        patch("app.company.storage.PROFILE_MD", md_path),
    ):
        yield tmp_path


@pytest.fixture()
def client(_clean_data: Path):
    app = create_app()
    return TestClient(app)


class TestCompanyAPISocialMedia:
    def test_save_and_load_with_social_links(self, client: TestClient):
        profile_data = {
            "name": "SocialCo",
            "description": "A test company with social links",
            "social_media_links": {
                "linkedin": "https://linkedin.com/company/socialco",
                "twitter": "https://x.com/socialco",
            },
        }
        resp = client.post("/api/v1/company", json=profile_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["social_media_links"]["linkedin"] == "https://linkedin.com/company/socialco"
        assert data["social_media_links"]["twitter"] == "https://x.com/socialco"

        resp = client.get("/api/v1/company")
        assert resp.status_code == 200
        assert resp.json()["social_media_links"]["linkedin"] == "https://linkedin.com/company/socialco"


# ── Contextual image prompt tests ────────────────────────────


# ── Iterative refinement loop tests ──────────────────────────


class TestIterativeRefinement:
    def test_orchestrator_revises_content_at_least_once(self):
        from app.agents.content_generator import ContentGeneratorAgent
        from app.agents.llm import MockLLMProvider
        from app.agents.models import (
            AgentCapability,
            LLMReviewEvaluation,
            ReviewStatus,
            TaskRequest,
        )
        from app.agents.orchestrator import Orchestrator
        from app.agents.registry import AgentRegistry
        from app.agents.review import ReviewAgent

        class AlwaysReviseReviewer(MockLLMProvider):
            call_count = 0

            def review_agent_output(self, request, response):
                self.call_count += 1
                if self.call_count <= 1:
                    return LLMReviewEvaluation(
                        relevance=0.6,
                        completeness=0.65,
                        clarity=0.6,
                        actionability=0.55,
                        feedback="Too generic.",
                        revision_instruction="Make positioning more specific.",
                    )
                return LLMReviewEvaluation(
                    relevance=0.82,
                    completeness=0.85,
                    clarity=0.80,
                    actionability=0.78,
                    feedback="Much improved after revision.",
                    revision_instruction=None,
                )

        llm = AlwaysReviseReviewer()
        registry = AgentRegistry([ContentGeneratorAgent(llm)])
        orchestrator = Orchestrator(
            registry=registry,
            review_agent=ReviewAgent(llm_provider=llm),
            llm_provider=llm,
        )

        request = TaskRequest(
            prompt="Create content",
            context={"task_type": "content"},
        )
        result = orchestrator.handle_task(request)

        assert result.agent_response is not None
        assert "revised" in result.agent_response.summary.lower()
        assert result.review.score > 0.7

    def test_mock_revise_adds_prefix(self):
        from app.agents.llm import MockLLMProvider
        from app.agents.models import TaskRequest

        llm = MockLLMProvider()
        original = {"positioning": "Test content", "landing_copy": "Landing content"}
        revised = llm.revise_content_package(
            TaskRequest(prompt="test"),
            original,
            "Make it better",
        )
        assert revised["positioning"].startswith("[REVISED]")
        assert revised["landing_copy"].startswith("[REVISED]")

    def test_images_only_for_visual_sections(self):
        from app.agents.content_generator import IMAGE_SECTIONS

        assert "landing_copy" in IMAGE_SECTIONS
        assert "social_post" in IMAGE_SECTIONS
        assert "positioning" not in IMAGE_SECTIONS
        assert "icp_notes" not in IMAGE_SECTIONS
        assert "launch_email" not in IMAGE_SECTIONS


# ── Contextual image prompt tests ────────────────────────────


class TestContextualImagePrompts:
    def test_fallback_prompt_includes_section_text(self):
        prompt = _fallback_prompt(
            "positioning",
            "AI-powered sales automation for B2B teams",
        )
        assert "AI-powered sales automation" in prompt
        assert "no text" in prompt.lower()

    def test_fallback_prompt_handles_empty_text(self):
        prompt = _fallback_prompt("positioning", "")
        assert "no text" in prompt.lower()

    def test_fallback_prompt_all_sections(self):
        for section in ["positioning", "landing_copy", "icp_notes", "launch_email", "social_post"]:
            prompt = _fallback_prompt(section, "Test content for this section")
            assert "no text" in prompt.lower()
            assert len(prompt) > 50
