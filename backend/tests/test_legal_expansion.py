"""Tests for legal expansion: jurisdictions, document review, knowledge base, and image gen."""

from unittest.mock import patch

from app.agents.content_generator import ContentGeneratorAgent
from app.agents.image_gen import GeneratedImage, generate_content_images
from app.agents.legal import LegalAgent
from app.agents.legal_knowledge import (
    ALL_DOCUMENTS,
    EU_DOCUMENTS,
    INDUSTRY_DOCUMENTS,
    LegalKnowledgeBase,
    UK_DOCUMENTS,
    US_DOCUMENTS,
)
from app.agents.llm import MockLLMProvider
from app.agents.models import AgentCapability, AgentRequest


def _mock_llm() -> MockLLMProvider:
    return MockLLMProvider()


# --- Knowledge Base Expansion ---


def test_knowledge_base_has_gdpr() -> None:
    ids = {doc.id for doc in ALL_DOCUMENTS}
    assert "gdpr-overview" in ids


def test_knowledge_base_has_ccpa() -> None:
    ids = {doc.id for doc in ALL_DOCUMENTS}
    assert "ccpa-overview" in ids


def test_knowledge_base_has_can_spam() -> None:
    ids = {doc.id for doc in ALL_DOCUMENTS}
    assert "ftc-can-spam" in ids


def test_knowledge_base_has_sec() -> None:
    ids = {doc.id for doc in ALL_DOCUMENTS}
    assert "sec-regulation-crowdfunding" in ids


def test_knowledge_base_has_soc2() -> None:
    ids = {doc.id for doc in ALL_DOCUMENTS}
    assert "aicpa-soc2-overview" in ids


def test_knowledge_base_has_fintech_docs() -> None:
    fintech_ids = {doc.id for doc in INDUSTRY_DOCUMENTS["fintech"]}
    assert "fintech-money-transmission" in fintech_ids
    assert "pci-dss-overview" in fintech_ids


def test_knowledge_base_has_healthtech_docs() -> None:
    healthtech_ids = {doc.id for doc in INDUSTRY_DOCUMENTS["healthtech"]}
    assert "hipaa-overview" in healthtech_ids
    assert "fda-digital-health" in healthtech_ids


def test_knowledge_base_has_edtech_docs() -> None:
    edtech_ids = {doc.id for doc in INDUSTRY_DOCUMENTS["edtech"]}
    assert "ferpa-overview" in edtech_ids
    assert "coppa-overview" in edtech_ids


def test_all_documents_count() -> None:
    assert len(ALL_DOCUMENTS) >= 17


# --- Jurisdiction Filtering ---


def test_for_jurisdictions_us_only() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=["US"])
    doc_ids = {doc.id for doc in kb.documents}
    assert "ftc-advertising-faq" in doc_ids
    assert "gdpr-overview" not in doc_ids
    assert "uk-gdpr-ico" not in doc_ids


def test_for_jurisdictions_eu() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=["EU"])
    doc_ids = {doc.id for doc in kb.documents}
    assert "gdpr-overview" in doc_ids
    assert "eu-ecommerce-directive" in doc_ids


def test_for_jurisdictions_uk() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=["UK"])
    doc_ids = {doc.id for doc in kb.documents}
    assert "uk-gdpr-ico" in doc_ids


def test_for_jurisdictions_multi() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=["US", "EU"])
    doc_ids = {doc.id for doc in kb.documents}
    assert "ftc-advertising-faq" in doc_ids
    assert "gdpr-overview" in doc_ids


def test_for_jurisdictions_with_industry() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(
        jurisdictions=["US"], industries=["fintech"]
    )
    doc_ids = {doc.id for doc in kb.documents}
    assert "ftc-advertising-faq" in doc_ids
    assert "fintech-money-transmission" in doc_ids
    assert "pci-dss-overview" in doc_ids


def test_for_jurisdictions_deduplicates() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(
        jurisdictions=["US", "US"]
    )
    seen = set()
    for doc in kb.documents:
        assert doc.id not in seen, f"Duplicate document: {doc.id}"
        seen.add(doc.id)


# --- Legal Agent with Jurisdictions ---


def test_legal_agent_uses_jurisdiction_from_request() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Check GDPR compliance for our SaaS product",
            jurisdictions=["EU"],
        )
    )
    assert response.agent == AgentCapability.LEGAL
    assert response.output["important_notice"]


def test_legal_agent_with_industry() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Check compliance for our fintech payment app",
            jurisdictions=["US"],
            industries=["fintech"],
        )
    )
    assert response.agent == AgentCapability.LEGAL


def test_legal_agent_fallback_with_jurisdictions() -> None:
    agent = LegalAgent(llm_provider=None)
    response = agent.run(
        AgentRequest(
            prompt="Check privacy compliance for our EU SaaS launch",
            jurisdictions=["US", "EU"],
        )
    )
    assert "US, EU" in response.output["jurisdiction_scope"]


# --- Document Review Mode ---


def test_legal_agent_document_review_mode_with_llm() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Review my privacy policy",
            review_mode=True,
            uploaded_doc_text="Our privacy policy: we collect user data for analytics. We may share data with partners.",
            jurisdictions=["US", "EU"],
        )
    )
    assert response.title == "Document Compliance Review"
    assert response.output["important_notice"]
    assert response.output["compliance_gaps"]
    assert response.output["recommendations"]


def test_legal_agent_review_mode_without_doc_falls_back_to_scan() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Review legal risks",
            review_mode=True,
            jurisdictions=["US"],
        )
    )
    assert response.title == "Founder Legal Issue Scan"


def test_legal_agent_uploaded_doc_added_to_context() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Check legal risks for our terms of service",
            uploaded_doc_text="Terms of Service: Users agree to arbitration.",
            jurisdictions=["US"],
        )
    )
    assert response.agent == AgentCapability.LEGAL
    assert response.title == "Founder Legal Issue Scan"


def test_legal_agent_startup_url_included_in_context() -> None:
    llm = _mock_llm()
    agent = LegalAgent(llm_provider=llm)
    response = agent.run(
        AgentRequest(
            prompt="Check legal risks",
            startup_url="https://example.com",
            jurisdictions=["US"],
        )
    )
    assert response.agent == AgentCapability.LEGAL


# --- Mock LLM: review_document ---


def test_mock_llm_review_document() -> None:
    llm = _mock_llm()
    result = llm.review_document(
        document_text="Privacy Policy: We collect user emails for marketing.",
        source_context="GDPR Overview: ...",
        jurisdictions=["US", "EU"],
    )
    assert result.important_notice
    assert result.document_summary
    assert result.compliance_gaps
    assert result.recommendations


# --- Expanded Checklist ---


def test_fallback_checklist_includes_gdpr_items() -> None:
    agent = LegalAgent(llm_provider=None)
    response = agent.run(
        AgentRequest(
            prompt="Check GDPR compliance for our EU SaaS",
            jurisdictions=["EU"],
        )
    )
    checklist = response.output["founder_checklist"].lower()
    assert "gdpr" in checklist


def test_fallback_checklist_includes_email_items() -> None:
    agent = LegalAgent(llm_provider=None)
    response = agent.run(
        AgentRequest(
            prompt="Check compliance for our email newsletter outreach",
            jurisdictions=["US"],
        )
    )
    checklist = response.output["founder_checklist"].lower()
    assert "can-spam" in checklist


def test_fallback_checklist_includes_fintech_items() -> None:
    agent = LegalAgent(llm_provider=None)
    response = agent.run(
        AgentRequest(
            prompt="Check compliance for our fintech payment app",
            jurisdictions=["US"],
            industries=["fintech"],
        )
    )
    checklist = response.output["founder_checklist"].lower()
    assert "money transmission" in checklist or "pci" in checklist


# --- Image Generation (unit, mocked fal) ---


def test_generate_content_images_no_api_key() -> None:
    with patch("app.agents.image_gen.settings") as mock_settings:
        mock_settings.fal_api_key = None
        result = generate_content_images("AI sales platform")
        assert result == {}


def test_content_generator_without_fal_key() -> None:
    llm = _mock_llm()
    agent = ContentGeneratorAgent(llm)
    with patch("app.agents.image_gen.settings") as mock_settings:
        mock_settings.fal_api_key = None
        response = agent.run(
            AgentRequest(
                prompt="Create content for my AI sales platform",
                startup_idea="AI sales platform",
            )
        )
    assert response.agent == AgentCapability.CONTENT_GENERATOR
    image_keys = [k for k in response.output if k.endswith("_image")]
    assert len(image_keys) == 0


def test_content_generator_with_mocked_fal() -> None:
    llm = _mock_llm()
    agent = ContentGeneratorAgent(llm)
    fake_image = GeneratedImage(
        url="https://fal.ai/test-image.jpg",
        content_type="image/jpeg",
        prompt="test prompt",
        section="positioning",
    )
    with patch(
        "app.agents.content_generator.generate_content_images",
        return_value={"positioning": fake_image},
    ):
        response = agent.run(
            AgentRequest(
                prompt="Create content",
                startup_idea="AI platform",
            )
        )
    assert response.output.get("positioning_image") == "https://fal.ai/test-image.jpg"


# --- Knowledge Base Retrieval ---


def test_retrieve_gdpr_related_query() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(jurisdictions=["EU"])
    docs = kb.retrieve("GDPR data protection compliance EU")
    doc_ids = {doc.id for doc in docs}
    assert "gdpr-overview" in doc_ids


def test_retrieve_fintech_query() -> None:
    kb = LegalKnowledgeBase.for_jurisdictions(
        jurisdictions=["US"], industries=["fintech"]
    )
    docs = kb.retrieve("payment processing money transmission AML")
    doc_ids = {doc.id for doc in docs}
    assert "fintech-money-transmission" in doc_ids
