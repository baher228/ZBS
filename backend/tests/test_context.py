"""Tests for company context enrichment: website parsing, chat insights, context storage."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.company.chat_extractor import _looks_like_company_info, extract_insights_from_messages
from app.company.context_store import (
    CHAT_CONTEXT_JSON,
    WEBSITE_CONTEXT_JSON,
    ChatContext,
    ChatInsight,
    WebsiteContext,
    WebsitePageData,
    add_chat_insight,
    delete_chat_context,
    delete_website_context,
    get_enriched_context,
    load_chat_context,
    load_website_context,
    save_chat_context,
    save_website_context,
)
from app.company.storage import get_company_context, save_profile, delete_profile
from app.company.models import CompanyProfile
from app.company.website_parser import _classify_page, _extract_text, _is_safe_url
from app.main import app

client = TestClient(app)


# ── Fixtures / helpers ──────────────────────────────────────


def _cleanup():
    """Remove context files."""
    for path in (WEBSITE_CONTEXT_JSON, CHAT_CONTEXT_JSON):
        if path.exists():
            path.unlink()


def _sample_website_context() -> WebsiteContext:
    return WebsiteContext(
        source_url="https://acme.io",
        pages=[
            WebsitePageData(
                url="https://acme.io",
                title="Acme - AI Sales",
                page_type="homepage",
                content_summary="Acme helps B2B sales teams close deals faster with AI.",
            ),
            WebsitePageData(
                url="https://acme.io/pricing",
                title="Pricing",
                page_type="pricing",
                content_summary="Starter $29/mo, Pro $99/mo, Enterprise custom.",
            ),
        ],
        company_summary="Acme helps B2B sales teams close deals faster with AI.",
        pricing_info="Starter $29/mo, Pro $99/mo, Enterprise custom.",
    )


def _sample_profile() -> CompanyProfile:
    return CompanyProfile(
        name="Acme Corp",
        description="AI-powered sales acceleration",
        website="https://acme.io",
        industry="SaaS",
    )


# ── Context Store Tests ─────────────────────────────────────


class TestWebsiteContextStorage:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_save_and_load_website_context(self):
        ctx = _sample_website_context()
        save_website_context(ctx)
        loaded = load_website_context()
        assert loaded is not None
        assert loaded.source_url == "https://acme.io"
        assert len(loaded.pages) == 2
        assert loaded.pricing_info == "Starter $29/mo, Pro $99/mo, Enterprise custom."

    def test_load_returns_none_when_empty(self):
        assert load_website_context() is None

    def test_delete_website_context(self):
        save_website_context(_sample_website_context())
        assert delete_website_context() is True
        assert load_website_context() is None
        assert delete_website_context() is False


class TestChatContextStorage:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_add_and_load_insights(self):
        insight = ChatInsight(
            source_agent="legal",
            fact="We operate in 3 jurisdictions: US, EU, UK",
            raw_question="What jurisdictions do you operate in?",
            raw_answer="We operate in 3 jurisdictions: US, EU, UK",
        )
        ctx = add_chat_insight(insight)
        assert len(ctx.insights) == 1
        assert ctx.insights[0].fact == "We operate in 3 jurisdictions: US, EU, UK"

        loaded = load_chat_context()
        assert len(loaded.insights) == 1

    def test_empty_chat_context(self):
        ctx = load_chat_context()
        assert len(ctx.insights) == 0

    def test_delete_chat_context(self):
        add_chat_insight(ChatInsight(source_agent="test", fact="test fact"))
        assert delete_chat_context() is True
        assert len(load_chat_context().insights) == 0
        assert delete_chat_context() is False

    def test_insight_limit_200(self):
        for i in range(210):
            add_chat_insight(ChatInsight(source_agent="test", fact=f"fact {i}"))
        ctx = load_chat_context()
        assert len(ctx.insights) == 200
        assert ctx.insights[0].fact == "fact 10"


class TestEnrichedContext:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_empty_enriched_context(self):
        assert get_enriched_context() == ""

    def test_website_only(self):
        save_website_context(_sample_website_context())
        text = get_enriched_context()
        assert "Website Context" in text
        assert "Acme" in text
        assert "Starter $29/mo" in text

    def test_chat_only(self):
        add_chat_insight(ChatInsight(source_agent="legal", fact="Company has 50 employees"))
        text = get_enriched_context()
        assert "Previous Conversations" in text
        assert "50 employees" in text

    def test_combined(self):
        save_website_context(_sample_website_context())
        add_chat_insight(ChatInsight(source_agent="content", fact="Brand color is blue"))
        text = get_enriched_context()
        assert "Website Context" in text
        assert "Previous Conversations" in text

    def test_company_context_includes_enriched(self):
        profile = _sample_profile()
        save_profile(profile)
        save_website_context(_sample_website_context())

        ctx = get_company_context()
        assert ctx is not None
        assert "Acme Corp" in ctx
        assert "Website Context" in ctx
        assert "Acme helps B2B" in ctx

    def test_company_context_returns_enriched_without_profile(self):
        add_chat_insight(ChatInsight(source_agent="legal", fact="We are incorporated in Delaware"))

        ctx = get_company_context()

        assert ctx is not None
        assert "Previous Conversations" in ctx
        assert "incorporated in Delaware" in ctx


# ── Chat Extractor Tests ────────────────────────────────────


class TestChatExtractor:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_looks_like_company_info_positive(self):
        assert _looks_like_company_info("We use React and TypeScript for our frontend")
        assert _looks_like_company_info("Our team consists of 12 engineers and 3 designers")
        assert _looks_like_company_info("We offer three pricing tiers for our SaaS product")

    def test_looks_like_company_info_negative(self):
        assert not _looks_like_company_info("Yes")
        assert not _looks_like_company_info("Can you help me?")
        assert not _looks_like_company_info("What is the weather today?")

    def test_extract_insights_stores_last_user_message_only(self):
        messages = [
            {"role": "assistant", "content": "What does your company do?"},
            {"role": "user", "content": "We provide AI-powered analytics for e-commerce stores. Our team has 25 people."},
            {"role": "assistant", "content": "Got it. What markets do you target?"},
            {"role": "user", "content": "We target mid-market e-commerce brands in the US and UK."},
        ]
        stored = extract_insights_from_messages(messages, source_agent="marketing_research")
        assert len(stored) == 1
        assert "mid-market" in stored[0].fact
        ctx = load_chat_context()
        assert len(ctx.insights) == 1

    def test_extract_understands_short_reply_from_chat_context(self):
        messages = [
            {"role": "assistant", "content": "Where does your company operate?"},
            {"role": "user", "content": "UK and EU"},
        ]

        stored = extract_insights_from_messages(messages, source_agent="legal")

        assert len(stored) == 1
        assert "Company operates in UK and EU" in stored[0].fact

    def test_extract_understands_short_pricing_reply_from_chat_context(self):
        messages = [
            {"role": "assistant", "content": "What is your pricing?"},
            {"role": "user", "content": "£19/month for students"},
        ]

        stored = extract_insights_from_messages(messages, source_agent="content")

        assert len(stored) == 1
        assert "Company pricing is £19/month for students" in stored[0].fact

    def test_extract_no_duplicates_on_resend(self):
        messages = [
            {"role": "user", "content": "We have 50 employees and we operate in the US."},
        ]
        extract_insights_from_messages(messages, source_agent="legal")
        extract_insights_from_messages(messages, source_agent="legal")
        ctx = load_chat_context()
        # Each call only extracts the last message, so 2 total (not quadratic)
        assert len(ctx.insights) == 2

    def test_extract_skips_when_fact_already_in_context(self):
        messages = [
            {"role": "user", "content": "We have 50 employees and we operate in the US."},
        ]

        stored = extract_insights_from_messages(
            messages,
            source_agent="legal",
            existing_context="Stored context: We have 50 employees and we operate in the US.",
        )

        assert stored == []
        assert len(load_chat_context().insights) == 0

    def test_extract_skips_non_company_messages(self):
        messages = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Thanks, that's helpful"},
        ]
        stored = extract_insights_from_messages(messages, source_agent="legal")
        assert len(stored) == 0


# ── Website Parser Tests ────────────────────────────────────


class TestWebsiteParser:
    def test_classify_page(self):
        assert _classify_page("https://x.com/", "Home", "") == "homepage"
        assert _classify_page("https://x.com/about", "About Us", "") == "about"
        assert _classify_page("https://x.com/pricing", "Plans", "") == "pricing"
        assert _classify_page("https://x.com/privacy", "Privacy Policy", "") == "privacy_policy"
        assert _classify_page("https://x.com/terms", "Terms", "") == "terms_of_service"
        assert _classify_page("https://x.com/features", "Features", "") == "features"

    def test_ssrf_blocks_private_ips(self):
        assert not _is_safe_url("http://127.0.0.1/")
        assert not _is_safe_url("http://localhost/")
        assert not _is_safe_url("http://169.254.169.254/latest/meta-data/")
        assert not _is_safe_url("http://10.0.0.1/")
        assert not _is_safe_url("http://192.168.1.1/")
        assert not _is_safe_url("ftp://example.com/file")
        assert not _is_safe_url("file:///etc/passwd")

    def test_extract_text_from_html(self):
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <nav>Nav content</nav>
            <main><h1>Hello World</h1><p>This is the main content.</p></main>
            <footer>Footer stuff</footer>
        </body>
        </html>
        """
        title, text = _extract_text(html)
        assert title == "Test Page"
        assert "Hello World" in text
        assert "main content" in text
        assert "Nav content" not in text
        assert "Footer stuff" not in text


# ── API Endpoint Tests ──────────────────────────────────────


class TestContextAPI:
    def setup_method(self):
        _cleanup()
        delete_profile()

    def teardown_method(self):
        _cleanup()
        delete_profile()

    def test_get_empty_context(self):
        response = client.get("/api/v1/company/context")
        assert response.status_code == 200
        data = response.json()
        assert data["website_context"] is None
        assert data["chat_context"]["insights"] == []
        assert data["combined_text"] == ""

    def test_add_insight_via_api(self):
        response = client.post(
            "/api/v1/company/context/insight",
            json={
                "source_agent": "legal",
                "fact": "Company registered in Delaware",
                "raw_question": "Where is your company registered?",
                "raw_answer": "We are registered in Delaware",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["insights"]) == 1
        assert data["insights"][0]["fact"] == "Company registered in Delaware"

    def test_clear_context(self):
        add_chat_insight(ChatInsight(source_agent="test", fact="test"))
        save_website_context(_sample_website_context())

        response = client.delete("/api/v1/company/context")
        assert response.status_code == 200
        data = response.json()
        assert data["website_deleted"] is True
        assert data["chat_deleted"] is True

    @patch("app.api.routes.context.parse_website", new_callable=AsyncMock)
    def test_parse_website_endpoint(self, mock_parse):
        mock_parse.return_value = _sample_website_context()

        response = client.post(
            "/api/v1/company/context/parse-website",
            json={"url": "https://acme.io"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["pages_parsed"] == 2
        assert data["source_url"] == "https://acme.io"

    def test_parse_website_no_url(self):
        response = client.post(
            "/api/v1/company/context/parse-website",
            json={},
        )
        assert response.status_code == 400

    @patch("app.api.routes.context.parse_website", new_callable=AsyncMock)
    def test_parse_website_uses_profile_url(self, mock_parse):
        mock_parse.return_value = _sample_website_context()
        save_profile(_sample_profile())

        response = client.post(
            "/api/v1/company/context/parse-website",
            json={},
        )
        assert response.status_code == 200
        mock_parse.assert_called_once_with("https://acme.io")

    def test_enriched_context_after_insert(self):
        save_website_context(_sample_website_context())
        add_chat_insight(ChatInsight(source_agent="content", fact="We use Tailwind CSS"))

        response = client.get("/api/v1/company/context")
        assert response.status_code == 200
        data = response.json()
        assert data["website_context"] is not None
        assert len(data["chat_context"]["insights"]) == 1
        assert "Website Context" in data["combined_text"]
        assert "Tailwind CSS" in data["combined_text"]


# ── Integration: Chat routes extract context ────────────────


class TestChatContextExtraction:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_legal_chat_extracts_context(self):
        response = client.post(
            "/api/v1/legal/chat",
            json={
                "messages": [
                    {"role": "user", "content": "We have 50 employees and we operate in California and New York."},
                ],
                "mode": "legal_advice",
            },
        )
        assert response.status_code == 200
        ctx = load_chat_context()
        assert len(ctx.insights) >= 1
        assert any("50 employees" in i.fact for i in ctx.insights)

    @patch("app.api.routes.legal_chat.get_llm_provider")
    def test_legal_chat_loads_existing_context_then_extracts_in_background(self, mock_get_provider):
        class CapturingProvider:
            company_context = ""

            def chat_legal(self, messages, mode, source_context, company_context, document_type=None):
                self.company_context = company_context
                return LegalChatResponse(
                    reply="Done",
                    document=None,
                    follow_up_questions=[],
                    mode=mode,
                    sources_used=[],
                )

        from app.agents.models import LegalChatResponse

        provider = CapturingProvider()
        mock_get_provider.return_value = provider

        response = client.post(
            "/api/v1/legal/chat",
            json={
                "messages": [
                    {"role": "user", "content": "We are incorporated in Delaware and we process EU customer data."},
                ],
                "mode": "legal_advice",
            },
        )

        assert response.status_code == 200
        assert "incorporated in Delaware" not in provider.company_context
        ctx = load_chat_context()
        assert any("incorporated in Delaware" in insight.fact for insight in ctx.insights)
        assert any("process EU customer data" in insight.fact for insight in ctx.insights)

    @patch("app.api.routes.content_chat.get_llm_provider")
    def test_content_chat_loads_existing_context_then_extracts_in_background(self, mock_get_provider):
        from app.agents.models import ContentChatResponse

        class CapturingProvider:
            company_context = ""

            def chat_content(self, messages, company_context, workflow=None):
                self.company_context = company_context
                return ContentChatResponse(
                    reply="Done",
                    follow_up_questions=[],
                    content_ready=True,
                    generated_content={"draft": "Launch copy"},
                )

        provider = CapturingProvider()
        mock_get_provider.return_value = provider

        response = client.post(
            "/api/v1/content/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Our company sells AI finance training to UK university students."},
                ],
                "image_mode": "none",
            },
        )

        assert response.status_code == 200
        assert "AI finance training" not in provider.company_context
        ctx = load_chat_context()
        assert any("AI finance training" in insight.fact for insight in ctx.insights)
        assert any("UK university students" in insight.fact for insight in ctx.insights)

    @patch("app.api.routes.marketing_research.get_llm_provider")
    def test_marketing_research_loads_existing_context_then_extracts_in_background(self, mock_get_provider):
        from app.agents.models import MarketingResearchResponse

        class CapturingProvider:
            company_context = ""

            def chat_marketing_research(self, messages, company_context, workflow=None):
                self.company_context = company_context
                return MarketingResearchResponse(
                    reply="Done",
                    follow_up_questions=[],
                    research_ready=True,
                    research_data={"summary": "Market notes"},
                )

        provider = CapturingProvider()
        mock_get_provider.return_value = provider

        response = client.post(
            "/api/v1/marketing-research/chat",
            json={
                "messages": [
                    {"role": "user", "content": "We target aspiring investment bankers and our pricing is £19 per month."},
                ],
                "workflow": "competitor_analysis",
            },
        )

        assert response.status_code == 200
        assert "aspiring investment bankers" not in provider.company_context
        ctx = load_chat_context()
        assert any("aspiring investment bankers" in insight.fact for insight in ctx.insights)
        assert any("pricing is £19 per month" in insight.fact for insight in ctx.insights)

    def test_content_chat_extracts_context(self):
        response = client.post(
            "/api/v1/content/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Our company uses a freemium model and we have 10,000 active users."},
                ],
            },
        )
        assert response.status_code == 200
        ctx = load_chat_context()
        assert len(ctx.insights) >= 1

    def test_marketing_research_extracts_context(self):
        response = client.post(
            "/api/v1/marketing-research/chat",
            json={
                "messages": [
                    {"role": "user", "content": "We sell our product to enterprise customers with an average deal size of $50k."},
                ],
            },
        )
        assert response.status_code == 200
        ctx = load_chat_context()
        assert len(ctx.insights) >= 1
