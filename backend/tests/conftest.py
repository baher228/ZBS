import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def force_mock_llm_for_tests(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "llm_provider", "mock")
    monkeypatch.setattr(settings, "llm_api_key", None)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "pydantic_ai_gateway_api_key", None)
    monkeypatch.setattr(settings, "pydantic", None)
    monkeypatch.setattr(settings, "pydantic_ai_gateway_base_url", None)
    monkeypatch.setattr(settings, "fal_api_key", None)
    monkeypatch.setattr(settings, "agent_cache_enabled", True)
    monkeypatch.setattr("app.agents.result_cache.DATA_DIR", tmp_path)
    monkeypatch.setattr("app.agents.result_cache.CACHE_JSON", tmp_path / "agent_result_cache.json")
    monkeypatch.setattr(settings, "mubit_enabled", False)
    monkeypatch.setattr(settings, "mubit_api_key", None)
    monkeypatch.setattr(settings, "gemini_api_key", None)
