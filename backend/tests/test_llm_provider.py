import pytest

from app.agents.campaign_models import CampaignCreateRequest
from app.agents.llm import MockLLMProvider, ResilientLLMProvider, UnconfiguredLLMProvider


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
    assert provider.last_error == "RuntimeError"
