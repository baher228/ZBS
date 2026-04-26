from app.agents.legal import LegalAgent
from app.agents.models import AgentCapability, AgentRequest, LegalDocumentDraft


def test_legal_agent_drafts_document_with_document_type() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Draft a Terms of Service for my startup.",
            document_type="Terms of Service",
            startup_idea="AI GTM office for founders",
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert "Draft" in response.title
    assert "Terms of Service" in response.title
    assert "not legal advice" in response.output["important_notice"].lower()
    assert response.output["document_body"]
    assert response.output["key_provisions"]
    assert response.output["next_steps"]


def test_legal_agent_drafts_nda() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Draft an NDA for my startup.",
            document_type="NDA",
            jurisdictions=["US", "EU"],
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert "NDA" in response.title
    assert response.output["document_body"]
    assert "US, EU" in response.output["jurisdiction_notes"]


def test_legal_agent_uses_additional_context() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Check legal risks for my SaaS launch.",
            additional_context="We process health data under HIPAA.",
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert response.output["important_notice"]


def test_legal_agent_falls_back_to_scan_without_document_type() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Check legal risks for my startup.",
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert "Founder Legal Issue Scan" in response.title
    assert response.output["risk_summary"]


def test_legal_document_draft_model() -> None:
    draft = LegalDocumentDraft(
        important_notice="Educational only.",
        document_title="Terms of Service",
        document_body="Full document body here.",
        key_provisions="1. Terms",
        customization_notes="Needs review.",
        jurisdiction_notes="US only.",
        next_steps="Get a lawyer.",
    )
    output = draft.as_output_dict()
    assert output["document_title"] == "Terms of Service"
    assert "follow_up_needed" not in output


def test_legal_document_draft_with_company_context() -> None:
    response = LegalAgent().run(
        AgentRequest(
            prompt="Draft a Privacy Policy.",
            document_type="Privacy Policy",
            context={
                "company_profile": (
                    "Company: TestCo\n"
                    "Industry: HealthTech\n"
                    "Jurisdictions: US, EU\n"
                    "Website: https://testco.com"
                ),
            },
        )
    )

    assert response.agent == AgentCapability.LEGAL
    assert "Privacy Policy" in response.title
    assert response.output["document_body"]
