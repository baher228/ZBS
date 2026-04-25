"""Tests for company profile CRUD, markdown generation, and agent context injection."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.company.models import CompanyProfile
from app.company.storage import (
    DATA_DIR,
    PROFILE_JSON,
    PROFILE_MD,
    delete_profile,
    get_company_context,
    load_profile,
    save_profile,
)
from app.main import create_app


@pytest.fixture()
def _clean_data(tmp_path: Path):
    """Redirect storage to a temp directory so tests don't conflict."""
    json_path = tmp_path / "company_profile.json"
    md_path = tmp_path / "company_profile.md"
    with (
        patch("app.company.storage.DATA_DIR", tmp_path),
        patch("app.company.storage.PROFILE_JSON", json_path),
        patch("app.company.storage.PROFILE_MD", md_path),
    ):
        yield tmp_path


SAMPLE_PROFILE = CompanyProfile(
    name="Acme GTM",
    description="AI-powered go-to-market platform for B2B founders.",
    industry="SaaS",
    target_audience="Solo founders and lean sales teams",
    product="Automated outreach, AI demo rooms, and CRM qualification",
    website="https://acme-gtm.com",
    stage="pre-launch",
    key_features=["AI demo rooms", "Automated outreach", "Lead scoring"],
    differentiators="All-in-one platform; no manual GTM work",
    jurisdictions=["US", "EU"],
)


# ── Model unit tests ────────────────────────────────────────


class TestCompanyProfileModel:
    def test_to_context_string_contains_all_fields(self):
        ctx = SAMPLE_PROFILE.to_context_string()
        assert "Acme GTM" in ctx
        assert "SaaS" in ctx
        assert "Solo founders" in ctx
        assert "US, EU" in ctx
        assert "AI demo rooms" in ctx

    def test_to_markdown_is_valid(self):
        md = SAMPLE_PROFILE.to_markdown()
        assert md.startswith("# Acme GTM")
        assert "**Industry:** SaaS" in md
        assert "## Key Features" in md
        assert "- AI demo rooms" in md
        assert "## Differentiators" in md

    def test_minimal_profile(self):
        p = CompanyProfile(name="X", description="Y")
        ctx = p.to_context_string()
        assert "X" in ctx
        assert "Y" in ctx

    def test_stage_validation(self):
        for stage in ("pre-launch", "launched", "growth"):
            p = CompanyProfile(name="X", description="Y", stage=stage)
            assert p.stage == stage

    def test_invalid_stage_rejected(self):
        with pytest.raises(Exception):
            CompanyProfile(name="X", description="Y", stage="invalid")


# ── Storage unit tests ───────────────────────────────────────


class TestStorage:
    def test_save_and_load(self, _clean_data: Path):
        save_profile(SAMPLE_PROFILE)
        loaded = load_profile()
        assert loaded is not None
        assert loaded.name == "Acme GTM"
        assert loaded.key_features == ["AI demo rooms", "Automated outreach", "Lead scoring"]

    def test_save_creates_md(self, _clean_data: Path):
        md_path = save_profile(SAMPLE_PROFILE)
        assert md_path.exists()
        content = md_path.read_text()
        assert "# Acme GTM" in content

    def test_load_returns_none_when_missing(self, _clean_data: Path):
        assert load_profile() is None

    def test_delete(self, _clean_data: Path):
        save_profile(SAMPLE_PROFILE)
        assert delete_profile() is True
        assert load_profile() is None

    def test_delete_returns_false_when_missing(self, _clean_data: Path):
        assert delete_profile() is False

    def test_get_company_context(self, _clean_data: Path):
        assert get_company_context() is None
        save_profile(SAMPLE_PROFILE)
        ctx = get_company_context()
        assert ctx is not None
        assert "Acme GTM" in ctx


# ── API integration tests ────────────────────────────────────


@pytest.fixture()
def client(_clean_data: Path):
    app = create_app()
    return TestClient(app)


class TestCompanyAPI:
    def test_get_returns_404_when_empty(self, client: TestClient):
        resp = client.get("/api/v1/company")
        assert resp.status_code == 404

    def test_create_and_get(self, client: TestClient):
        resp = client.post("/api/v1/company", json=SAMPLE_PROFILE.model_dump())
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Acme GTM"

        resp = client.get("/api/v1/company")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Acme GTM"

    def test_update_overwrites(self, client: TestClient):
        client.post("/api/v1/company", json=SAMPLE_PROFILE.model_dump())
        updated = SAMPLE_PROFILE.model_dump()
        updated["name"] = "New Name"
        resp = client.post("/api/v1/company", json=updated)
        assert resp.status_code == 201

        resp = client.get("/api/v1/company")
        assert resp.json()["name"] == "New Name"

    def test_delete(self, client: TestClient):
        client.post("/api/v1/company", json=SAMPLE_PROFILE.model_dump())
        resp = client.delete("/api/v1/company")
        assert resp.status_code == 204

        resp = client.get("/api/v1/company")
        assert resp.status_code == 404

    def test_delete_returns_404_when_empty(self, client: TestClient):
        resp = client.delete("/api/v1/company")
        assert resp.status_code == 404

    def test_validation_rejects_empty_name(self, client: TestClient):
        resp = client.post(
            "/api/v1/company",
            json={"name": "", "description": "test"},
        )
        assert resp.status_code == 422


# ── Context injection tests ──────────────────────────────────


class TestContextInjection:
    def test_task_enriched_with_company_context(self, client: TestClient, _clean_data: Path):
        client.post("/api/v1/company", json=SAMPLE_PROFILE.model_dump())

        resp = client.post(
            "/api/v1/tasks",
            json={
                "prompt": "Create landing page copy",
                "context": {"task_type": "content"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["selected_agent"] == "content_generator"

    def test_task_works_without_company_context(self, client: TestClient, _clean_data: Path):
        resp = client.post(
            "/api/v1/tasks",
            json={
                "prompt": "Create landing page copy",
                "context": {"task_type": "content"},
            },
        )
        assert resp.status_code == 200

    def test_company_context_fills_startup_idea(self, _clean_data: Path):
        save_profile(SAMPLE_PROFILE)
        from app.agents.models import TaskRequest
        from app.api.routes.tasks import _enrich_with_company_context

        request = TaskRequest(
            prompt="Create content",
            context={"task_type": "content"},
        )
        enriched = _enrich_with_company_context(request)
        assert enriched.startup_idea is not None
        assert "Acme GTM" in enriched.startup_idea
        assert enriched.target_audience == "Solo founders and lean sales teams"
        assert "company_profile" in enriched.context
