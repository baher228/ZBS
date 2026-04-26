import pytest

from app.agents.campaign_models import CampaignCreateRequest
from app.agents.llm import MockLLMProvider, ResilientLLMProvider, UnconfiguredLLMProvider
from app.agents.models import MarketingResearchMessage
from app.core.config import Settings


def test_unconfigured_provider_fails_for_campaign_methods() -> None:
    provider = UnconfiguredLLMProvider()
    request = CampaignCreateRequest(
        product_name="DemoRoom AI",
        product_description=(
            "AI demo rooms for technical B2B founders that turn cold outreach "
            "into qualified sales conversations."
        ),
        prospect_company="Pydantic",
    )

    with pytest.raises(RuntimeError, match="not configured"):
        provider.generate_product_strategy(request)


def test_resilient_provider_falls_back_to_mock_campaign_output() -> None:
    request = CampaignCreateRequest(
        product_name="DemoRoom AI",
        product_description=(
            "AI demo rooms for technical B2B founders that turn cold outreach "
            "into qualified sales conversations."
        ),
        prospect_company="Pydantic",
    )
    provider = ResilientLLMProvider(UnconfiguredLLMProvider(), MockLLMProvider())

    strategy = provider.generate_product_strategy(request)

    assert strategy.product_profile.name == "DemoRoom AI"
    assert provider.last_error == "generate_product_strategy: RuntimeError"


def test_settings_infer_gateway_provider_and_eu_base_url() -> None:
    settings = Settings(
        llm_provider="mock",
        pydantic="pylf_v2_eu_example_gateway_key",
    )

    assert settings.resolved_llm_provider == "gateway"
    assert settings.resolved_gateway_base_url == "https://gateway-eu.pydantic.dev/proxy/chat/"


def test_settings_enable_mubit_only_when_key_present() -> None:
    assert Settings(mubit_enabled=True, mubit_api_key=None).should_initialize_mubit is False
    assert Settings(mubit_enabled=False, mubit_api_key="mbt_test").should_initialize_mubit is False
    assert Settings(mubit_enabled=True, mubit_api_key="mbt_test").should_initialize_mubit is True


def test_resilient_provider_does_not_mock_marketing_research_chat() -> None:
    provider = ResilientLLMProvider(UnconfiguredLLMProvider(), MockLLMProvider())

    with pytest.raises(RuntimeError):
        provider.chat_marketing_research(
            [MarketingResearchMessage(role="user", content="Analyze competitors")],
            company_context="",
            workflow="competitor_analysis",
        )

    assert provider.last_error == "chat_marketing_research: RuntimeError"
