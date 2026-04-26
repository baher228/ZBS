"""Tests for the dashboard API endpoint."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.company.context_store import (
    CHAT_CONTEXT_JSON,
    WEBSITE_CONTEXT_JSON,
    ChatInsight,
    WebsiteContext,
    WebsitePageData,
    add_chat_insight,
    save_website_context,
)
from app.company.models import CompanyProfile
from app.company.storage import PROFILE_JSON, PROFILE_MD, delete_profile, save_profile
from app.main import app

client = TestClient(app)


def _cleanup():
    for path in (PROFILE_JSON, PROFILE_MD, WEBSITE_CONTEXT_JSON, CHAT_CONTEXT_JSON):
        if path.exists():
            path.unlink()


class TestDashboardEndpoint:
    def setup_method(self):
        _cleanup()

    def teardown_method(self):
        _cleanup()

    def test_dashboard_no_profile(self):
        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert data["company"]["has_profile"] is False
        assert data["company"]["name"] == ""
        assert data["context"]["website_parsed"] is False
        assert data["context"]["insights_count"] == 0
        assert data["provider"]["provider"] in ("mock", "gateway", "openai")
        assert len(data["agents"]) == 3

    def test_dashboard_with_profile(self):
        profile = CompanyProfile(
            name="TestCorp",
            description="A test company",
            industry="SaaS",
            stage="growth",
            website="https://testcorp.io",
            jurisdictions=["US", "EU"],
            key_features=["AI", "automation"],
            target_audience="B2B founders",
            social_media_links={"linkedin": "https://linkedin.com/company/test"},
        )
        save_profile(profile)

        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        co = data["company"]
        assert co["has_profile"] is True
        assert co["name"] == "TestCorp"
        assert co["industry"] == "SaaS"
        assert co["stage"] == "growth"
        assert co["website"] == "https://testcorp.io"
        assert co["jurisdictions"] == ["US", "EU"]
        assert co["key_features"] == ["AI", "automation"]
        assert co["target_audience"] == "B2B founders"
        assert co["social_links_count"] == 1

    def test_dashboard_with_website_context(self):
        ctx = WebsiteContext(
            source_url="https://example.com",
            pages=[
                WebsitePageData(url="https://example.com", title="Home", page_type="homepage"),
                WebsitePageData(url="https://example.com/about", title="About", page_type="about"),
            ],
            company_summary="An example company.",
        )
        save_website_context(ctx)

        resp = client.get("/api/v1/dashboard")
        data = resp.json()
        assert data["context"]["website_parsed"] is True
        assert data["context"]["pages_count"] == 2
        assert data["context"]["website_url"] == "https://example.com"
        assert "example" in data["context"]["company_summary"].lower()

    def test_dashboard_with_chat_insights(self):
        add_chat_insight(ChatInsight(source_agent="legal", fact="Operates in US"))
        add_chat_insight(ChatInsight(source_agent="legal", fact="Has 50 employees"))
        add_chat_insight(ChatInsight(source_agent="content", fact="Brand color is blue"))

        resp = client.get("/api/v1/dashboard")
        data = resp.json()
        assert data["context"]["insights_count"] == 3
        assert data["context"]["insights_by_agent"]["legal"] == 2
        assert data["context"]["insights_by_agent"]["content"] == 1

    def test_dashboard_agents_list(self):
        resp = client.get("/api/v1/dashboard")
        data = resp.json()
        agents = data["agents"]
        assert len(agents) == 3
        slugs = [a["slug"] for a in agents]
        assert "legal" in slugs
        assert "content" in slugs
        assert "marketing-research" in slugs
        for a in agents:
            assert a["status"] == "live"
            assert a["name"]
            assert a["description"]

    def test_dashboard_provider_info(self):
        resp = client.get("/api/v1/dashboard")
        data = resp.json()
        prov = data["provider"]
        assert "provider" in prov
        assert "model" in prov
        assert "status" in prov
        assert prov["status"] in ("online", "mock")

    def test_dashboard_full_state(self):
        """Test with all data populated."""
        profile = CompanyProfile(
            name="FullCorp",
            description="Full test",
            industry="FinTech",
            stage="launched",
            website="https://fullcorp.com",
            jurisdictions=["UK"],
            key_features=["payments", "analytics"],
            differentiators="Best in class",
            social_media_links={"twitter": "https://x.com/full", "linkedin": "https://linkedin.com/full"},
        )
        save_profile(profile)

        save_website_context(WebsiteContext(
            source_url="https://fullcorp.com",
            pages=[WebsitePageData(url="https://fullcorp.com", title="Home", page_type="homepage")],
            company_summary="FullCorp is a fintech company.",
        ))

        add_chat_insight(ChatInsight(source_agent="marketing_research", fact="TAM is $5B"))

        resp = client.get("/api/v1/dashboard")
        assert resp.status_code == 200
        data = resp.json()

        assert data["company"]["has_profile"] is True
        assert data["company"]["name"] == "FullCorp"
        assert data["company"]["differentiators"] == "Best in class"
        assert data["company"]["social_links_count"] == 2

        assert data["context"]["website_parsed"] is True
        assert data["context"]["pages_count"] == 1
        assert data["context"]["insights_count"] == 1
        assert data["context"]["insights_by_agent"]["marketing_research"] == 1

        assert len(data["agents"]) == 3
