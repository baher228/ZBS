from abc import ABC, abstractmethod

from app.agents.campaign_models import (
    CampaignCreateRequest,
    DemoBrief,
    DemoRoom,
    FollowUpEmail,
    ICPProfile,
    OutreachDraft,
    ProductProfile,
    ProductStrategy,
    ProspectProfile,
    QualificationReport,
)
from app.agents.models import (
    AgentCapability,
    AgentRequest,
    AgentResponse,
    ContentPackage,
    DocumentReviewResult,
    LegalChatMessage,
    LegalChatMode,
    LegalChatResponse,
    LegalDocumentDraft,
    LegalIssueScan,
    LLMReviewEvaluation,
    SocialPost,
    SocialPostRequest,
    TaskClassification,
    TaskRequest,
)
from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        """Return GTM content sections for the generic tasks route."""

    @abstractmethod
    def revise_content_package(
        self,
        request: TaskRequest,
        original_output: dict[str, str],
        revision_instruction: str,
    ) -> dict[str, str]:
        """Revise a content package based on reviewer feedback."""

    @abstractmethod
    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        """Return product positioning and ICP for a campaign."""

    @abstractmethod
    def generate_prospect_profile(self, request: CampaignCreateRequest) -> ProspectProfile:
        """Return prospect context for a campaign."""

    @abstractmethod
    def generate_demo_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        """Return the prospect-facing demo narrative."""

    @abstractmethod
    def generate_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> dict[str, str]:
        """Return outreach copy with a demo-room link."""

    @abstractmethod
    def generate_demo_reply(self, demo_room: DemoRoom, message: str) -> str:
        """Return a demo-agent chat response."""

    @abstractmethod
    def generate_qualification(self, demo_room: DemoRoom) -> QualificationReport:
        """Return lead qualification from the demo-room transcript."""

    @abstractmethod
    def generate_legal_scan(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalIssueScan:
        """Return a source-grounded legal issue scan for founders."""

    @abstractmethod
    def review_agent_output(
        self,
        request: AgentRequest,
        response: AgentResponse,
    ) -> LLMReviewEvaluation:
        """Semantically evaluate agent output for quality."""

    @abstractmethod
    def classify_task(self, request: AgentRequest) -> TaskClassification:
        """Classify which agent should handle the request."""

    @abstractmethod
    def review_document(
        self,
        document_text: str,
        source_context: str,
        jurisdictions: list[str],
    ) -> DocumentReviewResult:
        """Review a user-uploaded document against regulatory sources."""

    @abstractmethod
    def generate_legal_draft(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalDocumentDraft:
        """Draft a legal document (ToS, privacy policy, NDA, etc.) for a startup."""

    @abstractmethod
    def chat_legal(
        self,
        messages: list[LegalChatMessage],
        mode: LegalChatMode,
        source_context: str,
        company_context: str,
        document_type: str | None = None,
    ) -> LegalChatResponse:
        """Handle a multi-turn legal chat conversation."""

    @abstractmethod
    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        """Generate a social media post tailored to a platform."""


class MockLLMProvider(LLMProvider):
    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        idea = request.startup_idea or "your product"
        audience = request.target_audience or "B2B buyers"
        goal = request.goal or "start qualified customer conversations"
        tone = request.tone or "clear and practical"
        channel = request.channel or "landing page and email"
        package = ContentPackage(
            positioning=(
                f"{idea} helps {audience} move from scattered GTM work to one clear system that can {goal}. "
                f"The tone should stay {tone} and tailored to {channel}."
            ),
            landing_copy=(
                f"Headline: Turn founder knowledge into pipeline.\n\n"
                f"Subhead: {idea} gives {audience} a faster path to {goal} with tailored outreach, AI demo rooms, "
                "and CRM-ready qualification."
            ),
            icp_notes=(
                f"Prioritize {audience} who already feel the pain of slow qualification, founder-led sales overload, "
                "or low-converting outbound. Look for urgency around proving relevance before a live call."
            ),
            launch_email=(
                f"Subject: A faster way for {audience} to qualify demand\n\n"
                f"Hi there,\n\n{idea} is built for teams that want to {goal} without adding manual GTM overhead. "
                "It turns outbound into a product-specific conversation and gives the founder a clean next step.\n\n"
                "Worth a quick look?"
            ),
            social_post=(
                f"Most teams do not need more outreach volume. They need a tighter path from first message to real buyer intent. "
                f"{idea} helps {audience} {goal} with personalized demo-room workflows instead of generic funnels."
            ),
        )
        return package.as_output_dict()

    def revise_content_package(
        self,
        request: TaskRequest,
        original_output: dict[str, str],
        revision_instruction: str,
    ) -> dict[str, str]:
        revised = dict(original_output)
        for key in revised:
            if not key.endswith("_image"):
                revised[key] = f"[REVISED] {revised[key]}"
        return revised

    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        audience = request.target_audience or "technical B2B founders and lean GTM teams"
        product_profile = ProductProfile(
            name=request.product_name,
            category="AI GTM workflow",
            one_liner=(
                f"{request.product_name} helps {audience} turn product context into "
                "qualified sales conversations."
            ),
            core_problem=(
                "Founders can explain their product, but cold prospects rarely commit "
                "time before they understand why it matters."
            ),
            key_value_props=[
                "Turns static outbound into an interactive product conversation.",
                "Personalizes the demo narrative to each prospect account.",
                "Produces CRM-ready qualification and follow-up automatically.",
            ],
            proof_points=[
                "Uses structured product, ICP, and prospect context.",
                "Captures objections and next steps from the conversation.",
            ],
            likely_objections=[
                "Will the demo agent understand our product accurately?",
                "Will prospects engage with an AI demo instead of a human?",
                "How much setup is required before a campaign can launch?",
            ],
        )
        icp = ICPProfile(
            primary_buyer=audience,
            ideal_company="B2B companies selling technical products that need explanation before purchase.",
            trigger_events=[
                "Launching a new product",
                "Founder-led sales is not scaling",
                "Outbound replies are low despite strong product fit",
            ],
            qualification_criteria=[
                "Has a technical or operational pain connected to the product",
                "Can evaluate a self-serve demo room",
                "Has urgency to improve GTM pipeline",
            ],
            disqualifiers=[
                "Pure consumer product",
                "No outbound motion",
                "No clear buyer pain",
            ],
        )
        return ProductStrategy(product_profile=product_profile, icp=icp)

    def generate_prospect_profile(self, request: CampaignCreateRequest) -> ProspectProfile:
        description = request.prospect_description or (
            f"{request.prospect_company} appears to be a target account that could benefit "
            f"from {request.product_name}."
        )
        return ProspectProfile(
            company_name=request.prospect_company,
            description=description,
            likely_pain_points=[
                "Needs to evaluate new tools without adding sales calls too early.",
                "Wants clearer context on how a product applies to its own workflow.",
                "May need evidence that the product can address account-specific needs.",
            ],
            relevance_angle=(
                f"Position {request.product_name} as a way for {request.prospect_company} "
                "to understand the product through a tailored conversation instead of a generic page."
            ),
            personalization_assumptions=[
                "The prospect is evaluating ways to improve pipeline quality.",
                "The prospect values concise, technical product explanations.",
            ],
        )

    def generate_demo_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        return DemoBrief(
            title=f"{product_profile.name} for {prospect_profile.company_name}",
            narrative=(
                f"Show {prospect_profile.company_name} how {product_profile.name} maps to "
                f"their likely pain: {prospect_profile.likely_pain_points[0]}"
            ),
            talking_points=[
                product_profile.key_value_props[0],
                product_profile.key_value_props[1],
                prospect_profile.relevance_angle,
            ],
            qualifying_questions=[
                "What outbound or demo workflow are you using today?",
                "Where do prospects usually drop off before a qualified conversation?",
                "What would make this valuable enough to try in the next campaign?",
            ],
            objection_handlers=[
                "If accuracy is the concern, explain that the demo room is grounded in the founder's docs and reviewed before launch.",
                "If adoption is the concern, emphasize that the prospect can explore asynchronously before booking time.",
            ],
        )

    def generate_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> dict[str, str]:
        return {
            "subject": f"Personalized {product_profile.name} demo for {prospect_profile.company_name}",
            "body": (
                f"Hi {prospect_profile.company_name} team,\n\n"
                f"I made a short AI demo room showing how {product_profile.name} could apply to "
                f"{prospect_profile.company_name}. It focuses on {prospect_profile.likely_pain_points[0].lower()}\n\n"
                f"You can explore it here: {demo_room_url}\n\n"
                "If it feels relevant, the room will summarize the conversation and suggest a next step."
            ),
            "channel": "email",
            "demo_room_url": demo_room_url,
        }

    def generate_demo_reply(self, demo_room: DemoRoom, message: str) -> str:
        lower_message = message.lower()
        if "price" in lower_message or "cost" in lower_message:
            return (
                "Pricing depends on campaign volume and the depth of product context, but the value case is "
                "reducing wasted founder calls by qualifying interest inside the demo room first."
            )
        if "how" in lower_message or "work" in lower_message:
            return (
                f"The room is built from the founder's product strategy and {demo_room.prospect_company}'s context. "
                "It explains the product, handles objections, asks qualifying questions, and turns this chat into CRM notes."
            )
        return (
            f"For {demo_room.prospect_company}, the main reason to care is this: "
            f"{demo_room.relevance_summary} A useful next question is: {demo_room.suggested_questions[0]}"
        )

    def generate_qualification(self, demo_room: DemoRoom) -> QualificationReport:
        transcript_text = " ".join(message.content for message in demo_room.transcript).lower()
        has_pricing = "price" in transcript_text or "cost" in transcript_text
        has_workflow = "how" in transcript_text or "work" in transcript_text
        score = 78 + (7 if has_workflow else 0) + (5 if has_pricing else 0)
        score = min(score, 92)
        return QualificationReport(
            demo_room_id=demo_room.id,
            lead_score=score,
            qualification_status="qualified" if score >= 80 else "nurture",
            pain_points=[
                "Needs prospects to understand the product before booking a call.",
                "Wants higher-quality sales conversations from outbound.",
            ],
            objections=[
                "Accuracy of AI-generated product explanations",
                "Whether prospects will engage asynchronously",
            ],
            buying_signals=[
                "Asked about workflow fit" if has_workflow else "Engaged with personalized demo room",
                "Asked about pricing" if has_pricing else "Reviewed relevance summary",
            ],
            urgency="Medium-high: interested enough to explore, but should be moved to a founder call quickly.",
            recommended_next_step="Send the conversation summary and offer a 20-minute founder walkthrough.",
            crm_note=(
                f"{demo_room.prospect_company} engaged with the personalized demo room. "
                "Main interest is improving outbound-to-demo conversion and qualifying prospects before calls."
            ),
            follow_up_email=FollowUpEmail(
                subject=f"Summary from your {demo_room.prospect_company} demo room",
                body=(
                    "Hi,\n\nThanks for exploring the demo room. Based on the conversation, the most relevant angle is "
                    "turning cold outreach into an instant product-specific conversation, then converting that into "
                    "CRM notes and follow-up.\n\nWould it be useful to do a short founder walkthrough this week?"
                ),
            ),
        )

    def generate_legal_scan(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalIssueScan:
        idea = request.startup_idea or request.prompt
        audience = request.target_audience or "US startup founders"
        return LegalIssueScan(
            important_notice=(
                "This is educational issue-spotting for founders, not legal advice. "
                "A qualified lawyer should review jurisdiction-specific decisions, filings, contracts, and regulated claims."
            ),
            jurisdiction_scope=(
                "Seed sources are currently United States-focused. Treat non-US launches, regulated industries, "
                "employment, securities, health, finance, and tax questions as counsel-required."
            ),
            relevant_sources=source_context,
            risk_summary=(
                f"Founders building {idea} for {audience} should review advertising substantiation, privacy obligations, "
                "entity formation, and any regulated claims before launching publicly."
            ),
            founder_checklist=(
                "1. Confirm the company formation path and founder ownership structure.\n"
                "2. List every public marketing claim and attach evidence before launch.\n"
                "3. Map what personal data is collected, why it is needed, where it is stored, and who receives it.\n"
                "4. Prepare customer-facing terms, privacy notice, and support/contact details before collecting users."
            ),
            questions_for_counsel=(
                "1. Which entity structure and state filing path best fits the founders' risk, tax, and fundraising plans?\n"
                "2. Are the landing page, outreach, pricing, endorsements, and claims substantiated and non-deceptive?\n"
                "3. What privacy notice, data-processing, security, and customer-contract terms are needed before launch?\n"
                "4. Are accessibility, industry-specific, international, or employment obligations triggered?"
            ),
            next_steps=(
                "Collect product claims, data flows, customer promises, planned jurisdictions, and launch channels. "
                "Use this packet for a legal review before publishing high-risk claims or collecting customer data."
            ),
        )

    def review_agent_output(
        self,
        request: AgentRequest,
        response: AgentResponse,
    ) -> LLMReviewEvaluation:
        output_text = " ".join(response.output.values())
        has_substance = len(output_text) > 100
        sections_filled = sum(1 for v in response.output.values() if v.strip())
        total_sections = max(1, len(response.output))
        completeness = round(sections_filled / total_sections, 2)
        relevance = 0.85 if has_substance else 0.3
        clarity = 0.85 if has_substance else 0.3
        actionability = 0.8 if has_substance else 0.3
        return LLMReviewEvaluation(
            relevance=relevance,
            completeness=completeness,
            clarity=clarity,
            actionability=actionability,
            feedback="Mock review: output meets structural requirements." if has_substance
            else "Mock review: output lacks substance.",
            revision_instruction="Add more specific, actionable content to each section." if not has_substance else None,
        )

    def classify_task(self, request: AgentRequest) -> TaskClassification:
        task_type = request.context.get("task_type", "").lower()
        if task_type == "legal":
            return TaskClassification(agent=AgentCapability.LEGAL, confidence=1.0, reasoning="Explicit legal task type.")
        if task_type == "content":
            return TaskClassification(
                agent=AgentCapability.CONTENT_GENERATOR, confidence=1.0, reasoning="Explicit content task type."
            )
        text = f"{request.prompt} {request.goal or ''} {request.channel or ''}".lower()
        if any(kw in text for kw in ("legal", "privacy", "compliance", "terms", "gdpr")):
            return TaskClassification(agent=AgentCapability.LEGAL, confidence=0.8, reasoning="Legal keywords detected.")
        if any(kw in text for kw in ("content", "marketing", "copy", "email", "social")):
            return TaskClassification(
                agent=AgentCapability.CONTENT_GENERATOR, confidence=0.8, reasoning="Content keywords detected."
            )
        if any(kw in text for kw in ("demo", "prototype", "presentation")):
            return TaskClassification(agent=AgentCapability.DEMO, confidence=0.8, reasoning="Demo keywords detected.")
        return TaskClassification(
            agent=AgentCapability.UNSUPPORTED, confidence=0.5, reasoning="No matching agent capability detected."
        )

    def review_document(
        self,
        document_text: str,
        source_context: str,
        jurisdictions: list[str],
    ) -> DocumentReviewResult:
        scope = ", ".join(jurisdictions) if jurisdictions else "US"
        return DocumentReviewResult(
            important_notice=(
                "This is an automated compliance review for educational purposes, not legal advice. "
                "Have a qualified attorney review any legal documents before use."
            ),
            document_summary=f"Mock review of uploaded document ({len(document_text)} chars) against {scope} regulations.",
            compliance_gaps="Mock: no specific gaps identified in this automated review.",
            risk_areas="Mock: general risk areas include missing privacy disclosures and vague data handling terms.",
            recommendations="Mock: consider adding explicit data retention policies and user consent mechanisms.",
            applicable_regulations=source_context[:500] if source_context else "No regulations loaded.",
            next_steps="Have a qualified attorney review the full document against applicable regulations.",
        )

    def generate_legal_draft(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalDocumentDraft:
        doc_type = request.document_type or "Terms of Service"
        idea = request.startup_idea or request.prompt
        scope = ", ".join(request.jurisdictions) if request.jurisdictions else "US"
        return LegalDocumentDraft(
            important_notice=(
                "This is a starter template for educational purposes only, not legal advice. "
                "A qualified attorney must review and customize this document before use."
            ),
            document_title=f"{doc_type} — {idea}",
            document_body=(
                f"DRAFT {doc_type.upper()}\n\n"
                f"This {doc_type} governs the use of {idea}.\n\n"
                f"1. ACCEPTANCE OF TERMS\nBy accessing or using {idea}, you agree to be bound by these terms.\n\n"
                f"2. DESCRIPTION OF SERVICE\n{idea} provides services as described on the platform.\n\n"
                "3. USER OBLIGATIONS\nYou agree to use the service in compliance with all applicable laws.\n\n"
                "4. INTELLECTUAL PROPERTY\nAll content and materials remain the property of the company.\n\n"
                "5. LIMITATION OF LIABILITY\nThe service is provided 'as is' without warranties of any kind.\n\n"
                "6. GOVERNING LAW\n"
                f"This agreement is governed by the laws of {scope}.\n\n"
                "7. MODIFICATIONS\nWe reserve the right to modify these terms at any time."
            ),
            key_provisions=(
                "1. Acceptance of terms and binding agreement\n"
                "2. Service description and scope\n"
                "3. User obligations and acceptable use\n"
                "4. Intellectual property rights\n"
                "5. Limitation of liability and disclaimers\n"
                "6. Governing law and dispute resolution\n"
                "7. Modification and termination clauses"
            ),
            customization_notes=(
                f"This template needs customization for {idea}. Key areas to address with counsel:\n"
                "- Specific service descriptions and features\n"
                "- Data handling and privacy provisions\n"
                "- Payment terms (if applicable)\n"
                "- Specific liability exclusions for your industry\n"
                "- Compliance requirements for your jurisdictions"
            ),
            jurisdiction_notes=f"Drafted for {scope}. Consult local counsel for jurisdiction-specific requirements.",
            next_steps=(
                "1. Review this draft with a qualified attorney\n"
                "2. Customize provisions for your specific product and business model\n"
                "3. Add industry-specific compliance clauses\n"
                "4. Ensure alignment with your privacy policy and other legal documents\n"
                "5. Have counsel approve before publishing"
            ),
        )

    def chat_legal(
        self,
        messages: list[LegalChatMessage],
        mode: LegalChatMode,
        source_context: str,
        company_context: str,
        document_type: str | None = None,
    ) -> LegalChatResponse:
        last_msg = messages[-1].content if messages else "general legal question"
        mode_labels = {
            LegalChatMode.LEGAL_ADVICE: "legal advice",
            LegalChatMode.TAX: "tax guidance",
            LegalChatMode.DOCUMENT_DRAFTING: "document drafting",
        }
        label = mode_labels.get(mode, "legal")

        reply = (
            f"[Mock {label} response] Based on your question about: {last_msg[:100]}. "
            "This is educational guidance, not legal advice. Consult a qualified attorney."
        )

        document = None
        if mode == LegalChatMode.DOCUMENT_DRAFTING and document_type:
            document = LegalDocumentDraft(
                important_notice="This is a starter template, not legal advice.",
                document_title=f"Draft {document_type}",
                document_body=f"DRAFT {document_type.upper()}\n\n1. TERMS\nStandard provisions apply.\n\n2. OBLIGATIONS\nParties agree to act in good faith.",
                key_provisions="1. Standard terms\n2. Obligations\n3. Liability",
                customization_notes="Customize with attorney review.",
                jurisdiction_notes="US law applies by default.",
                next_steps="1. Review with attorney\n2. Customize\n3. Execute",
            )

        return LegalChatResponse(
            reply=reply,
            document=document,
            follow_up_questions=["What jurisdictions do you operate in?", "Do you collect personal data?"],
            mode=mode,
            sources_used=["FTC Act", "CCPA Guidelines"],
        )

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        platform_limits = {"twitter": "280 chars", "linkedin": "3000 chars", "instagram": "2200 chars", "facebook": "no limit"}
        limit = platform_limits.get(request.platform, "no limit")
        return SocialPost(
            caption=f"Mock {request.platform} post ({limit}) about: {request.topic}. This is a placeholder for the real LLM-generated post.",
            hashtags="#startup #launch #product",
            call_to_action="Learn more at our website.",
        )


class OpenAILLMProvider(LLMProvider):
    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        from langchain_openai import ChatOpenAI

        self.model = ChatOpenAI(
            model=settings.resolved_llm_model,
            api_key=api_key or settings.resolved_llm_api_key,
            base_url=base_url,
            temperature=0.2,
            max_retries=0,
            timeout=10,
        )

    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        structured_model = self.model.with_structured_output(ContentPackage)

        company_context = request.context.get("company_profile", "")
        company_block = (
            f"\n\nCompany context (use this to ground ALL content):\n{company_context}"
            if company_context
            else ""
        )

        social_insights = request.context.get("social_insights", "")
        social_block = (
            f"\n\nInsights from the company's existing social media presence:\n{social_insights}"
            if social_insights
            else ""
        )

        additional_block = ""
        if request.additional_context:
            additional_block = (
                f"\n\nAdditional context from the founder:\n{request.additional_context}"
            )

        website_url = ""
        if company_context:
            for line in company_context.split("\n"):
                if line.startswith("Website:"):
                    website_url = line.split(":", 1)[1].strip()
                    break

        link_instruction = ""
        if website_url:
            link_instruction = (
                f"\n\nIMPORTANT: The company website is {website_url}. "
                "When content needs a link or CTA URL, use this actual URL instead of "
                "placeholders like '[paste the link]', '[your-url]', or '[website]'. "
                "Make links feel natural in context."
            )

        package = structured_model.invoke(
            [
                (
                    "system",
                    "You are a world-class creative director and GTM strategist for B2B startups. "
                    "Your content should be vivid, memorable, and impossible to ignore.\n\n"
                    "CRITICAL WRITING RULES (non-negotiable):\n"
                    "- NEVER use em dashes or long dashes. Use commas, periods, semicolons, or rewrite the sentence instead.\n"
                    "- NEVER use these overused AI emoji: rocket, lightbulb, fire, sparkles, brain, gem, star, target, megaphone, "
                    "pointing down, muscle, chart, check mark, crystal ball, trophy. "
                    "If you must use emoji, pick unusual ones that feel human and specific to the context.\n"
                    "- NEVER use phrases like 'game-changer', 'revolutionize', 'unlock', 'supercharge', 'turbocharge', "
                    "'harness the power', 'leverage', 'cutting-edge', 'seamless', 'robust', 'elevate', "
                    "'dive into', 'in today''s fast-paced world', 'imagine a world where', 'at the end of the day'. "
                    "These instantly signal AI-generated text.\n"
                    "- NEVER use placeholder links like '[paste the link]', '[your-url]', or '[website]'. "
                    "If the company website URL is available, use the actual URL. If not available, "
                    "write the CTA without a URL placeholder.\n"
                    "- Write in short, punchy sentences. Vary sentence length. Use fragments for emphasis.\n"
                    "- Sound like a sharp founder writing to a peer, not a marketing agency writing a brochure.\n\n"
                    "Creative principles:\n"
                    "- Lead with a story, insight, or provocative angle, not a generic claim\n"
                    "- Use concrete details: real numbers, specific scenarios, named pain points\n"
                    "- Write like a human who deeply understands the audience's daily frustrations\n"
                    "- Every sentence should earn its place. Cut anything that sounds like marketing filler.\n"
                    "- Use power words, rhythm, and surprise to make copy sticky\n\n"
                    "Section guidelines:\n"
                    "- positioning: a bold, memorable statement that reframes how the audience "
                    "thinks about the problem. Not 'we do X for Y' but a paradigm shift.\n"
                    "- landing_copy: headline that stops scrolling + subhead that explains the 'how' "
                    "+ 3 benefit bullets that paint a before/after picture\n"
                    "- icp_notes: vivid buyer persona with day-in-the-life details, emotional triggers, "
                    "budget authority signals, and 'hair on fire' moments\n"
                    "- launch_email: subject line that creates curiosity (not clickbait) + body "
                    "that tells a mini-story leading to a single clear CTA\n"
                    "- social_post: a hook that stops the scroll in the first line, followed by "
                    "a punchy insight or story, ending with engagement bait. NO rocket emoji.\n\n"
                    "If social media insights are provided, match the company's existing voice and "
                    "content themes while pushing for higher impact.\n"
                    "Reference actual product features, audience, and differentiators, not generic placeholders."
                    + company_block
                    + social_block
                    + link_instruction
                    + additional_block,
                ),
                ("human", request.model_dump_json()),
            ]
        )
        return package.as_output_dict()

    def revise_content_package(
        self,
        request: TaskRequest,
        original_output: dict[str, str],
        revision_instruction: str,
    ) -> dict[str, str]:
        structured_model = self.model.with_structured_output(ContentPackage)

        company_context = request.context.get("company_profile", "")
        company_block = (
            f"\n\nCompany context:\n{company_context}" if company_context else ""
        )

        original_text = "\n".join(f"[{k}]: {v}" for k, v in original_output.items() if not k.endswith("_image"))

        package = structured_model.invoke(
            [
                (
                    "system",
                    "You are a world-class creative director revising GTM content based on critic feedback. "
                    "You received a first draft and specific improvement instructions from a quality reviewer. "
                    "Your job is to SIGNIFICANTLY improve every section, not just tweak words.\n\n"
                    "CRITICAL WRITING RULES (non-negotiable):\n"
                    "- NEVER use em dashes or long dashes. Use commas, periods, semicolons, or rewrite instead.\n"
                    "- NEVER use these overused AI emoji: rocket, lightbulb, fire, sparkles, brain, gem, star, target, megaphone, "
                    "pointing down, muscle, chart, check mark, crystal ball, trophy.\n"
                    "- NEVER use phrases like 'game-changer', 'revolutionize', 'unlock', 'supercharge', 'turbocharge', "
                    "'harness the power', 'leverage', 'cutting-edge', 'seamless', 'robust', 'elevate', "
                    "'dive into', 'in today''s fast-paced world', 'imagine a world where'. "
                    "These instantly signal AI-generated text.\n"
                    "- Write short, punchy sentences. Vary length. Use fragments for emphasis.\n"
                    "- Sound like a sharp founder, not a marketing agency.\n\n"
                    "Revision rules:\n"
                    "- Address EVERY point in the revision instructions\n"
                    "- Make the content more specific, vivid, and actionable\n"
                    "- Replace generic language with concrete details from the company context\n"
                    "- Each section should feel like it was written by a human who deeply knows the product\n"
                    "- The revised version must be noticeably better than the original, not a minor edit"
                    + company_block,
                ),
                (
                    "human",
                    f"Original request:\n{request.model_dump_json()}\n\n"
                    f"First draft:\n{original_text}\n\n"
                    f"Reviewer feedback and revision instructions:\n{revision_instruction}\n\n"
                    "Now produce the improved version. Every section must be better.",
                ),
            ]
        )
        return package.as_output_dict()

    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        structured_model = self.model.with_structured_output(ProductStrategy)
        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a senior GTM strategist. Return precise structured strategy for a B2B founder.",
                ),
                ("human", request.model_dump_json()),
            ]
        )

    def generate_prospect_profile(self, request: CampaignCreateRequest) -> ProspectProfile:
        structured_model = self.model.with_structured_output(ProspectProfile)
        return structured_model.invoke(
            [
                (
                    "system",
                    "You research a prospect account for personalized founder-led outbound. Use only provided context and label assumptions.",
                ),
                ("human", request.model_dump_json()),
            ]
        )

    def generate_demo_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        structured_model = self.model.with_structured_output(DemoBrief)
        return structured_model.invoke(
            [
                (
                    "system",
                    "Create a concise personalized AI demo-room brief. It must be concrete and useful for a prospect-facing demo agent.",
                ),
                (
                    "human",
                    "\n".join(
                        [
                            request.model_dump_json(),
                            product_profile.model_dump_json(),
                            icp.model_dump_json(),
                            prospect_profile.model_dump_json(),
                        ]
                    ),
                ),
            ]
        )

    def generate_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> dict[str, str]:
        structured_model = self.model.with_structured_output(OutreachDraft)
        draft = structured_model.invoke(
            [
                (
                    "system",
                    "Write a short personalized cold email. Keep the body clean and do not include labels.",
                ),
                (
                    "human",
                    f"Product: {product_profile.model_dump_json()}\n"
                    f"Prospect: {prospect_profile.model_dump_json()}\n"
                    f"Demo brief: {demo_brief.model_dump_json()}\n"
                    f"Demo room URL: {demo_room_url}",
                ),
            ]
        )
        return {
            "subject": draft.subject,
            "body": f"{draft.body}\n\nDemo room: {demo_room_url}",
            "channel": draft.channel,
            "demo_room_url": demo_room_url,
        }

    def generate_demo_reply(self, demo_room: DemoRoom, message: str) -> str:
        response = self.model.invoke(
            [
                (
                    "system",
                    "You are a prospect-facing AI demo agent. Be specific, concise, and grounded in the demo room context.",
                ),
                ("human", f"Demo room: {demo_room.model_dump_json()}\nProspect message: {message}"),
            ]
        )
        return str(response.content)

    def generate_qualification(self, demo_room: DemoRoom) -> QualificationReport:
        structured_model = self.model.with_structured_output(QualificationReport)
        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a sales ops agent. Qualify the lead from the transcript and produce CRM-ready output.",
                ),
                ("human", demo_room.model_dump_json()),
            ]
        )

    def generate_legal_scan(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalIssueScan:
        structured_model = self.model.with_structured_output(LegalIssueScan)

        company_context = request.context.get("company_profile", "")

        if company_context:
            context_instruction = (
                f"\n\nCompany context (already provided — do NOT ask for info that is here):\n{company_context}\n\n"
                "IMPORTANT: The company profile above is already saved. Do NOT repeat or re-ask for information "
                "that is already provided (name, industry, audience, jurisdictions, product description, features). "
                "Instead, USE this context directly in your analysis.\n\n"
                "If you need ADDITIONAL information that is NOT in the company profile to give a more precise "
                "legal assessment, list those specific questions in the follow_up_needed field. "
                "Examples: 'Do you collect payment card data directly?', 'Will you process EU resident health records?', "
                "'Do you use third-party data processors?'. Only ask for what you genuinely need to refine the analysis."
            )
        else:
            context_instruction = (
                "\n\nNo company profile is available. Provide a general analysis based on the request. "
                "In follow_up_needed, list the key questions the founder should answer for a more tailored scan: "
                "company name, industry, product description, target audience, jurisdictions, data handling practices."
            )

        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a startup legal issue-spotter. You help founders identify regulatory, "
                    "compliance, and legal risks before launch. Your output is educational and "
                    "source-grounded — clearly NOT legal advice. Always cite the specific public "
                    "guidance documents provided. Be concrete and practical.\n\n"
                    "Rules:\n"
                    "- important_notice MUST state this is educational, not legal advice\n"
                    "- jurisdiction_scope MUST note the geographic scope of the sources\n"
                    "- relevant_sources MUST cite each source document with title and URL\n"
                    "- risk_summary should be specific to the founder's product and audience\n"
                    "- founder_checklist should be numbered, actionable steps\n"
                    "- questions_for_counsel should be specific enough to hand to a lawyer\n"
                    "- next_steps should tell the founder exactly what to collect before counsel review\n"
                    "- follow_up_needed: if you need more information from the founder to refine the analysis, "
                    "list specific questions here. Leave empty if the provided context is sufficient."
                    + context_instruction,
                ),
                (
                    "human",
                    f"Founder request:\n{request.model_dump_json()}\n\n"
                    f"Reference sources:\n{source_context}",
                ),
            ]
        )

    def review_agent_output(
        self,
        request: AgentRequest,
        response: AgentResponse,
    ) -> LLMReviewEvaluation:
        structured_model = self.model.with_structured_output(LLMReviewEvaluation)

        company_context = request.context.get("company_profile", "")
        company_block = (
            f"\n\nCompany context the output MUST reference:\n{company_context}"
            if company_context
            else ""
        )

        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a RUTHLESS quality-assurance critic for AI-generated GTM content. "
                    "Your job is to catch mediocre, generic, or lazy work. Never rubber-stamp. "
                    "You review output as if a paying customer will use it to launch their startup. "
                    "Score each dimension 0.0-1.0:\n\n"
                    "- relevance (0-1): Does EVERY section directly address the SPECIFIC company, product, "
                    "and audience? Deduct heavily if ANY section is generic boilerplate that could apply "
                    "to any SaaS company. Mentioning the company name alone is NOT enough: "
                    "the content must reference specific features, pain points, and differentiators. "
                    "Score above 0.8 only if the content could NOT have been written for a different company.\n"
                    "- completeness (0-1): Are ALL expected sections present with real substance? "
                    "One-liner sections, placeholder text, or vague overviews score below 0.5. "
                    "Each section must be copy-paste ready, not a summary.\n"
                    "- clarity (0-1): Is the output well-structured, concise, and free of filler? "
                    "Deduct for: buzzword salad ('leverage', 'empower', 'cutting-edge', 'innovative'), "
                    "repeating the same idea across sections, overly long sentences, passive voice, "
                    "or corporate jargon that obscures meaning.\n"
                    "  ALSO deduct for AI-sounding writing patterns:\n"
                    "  * Em dashes or long dashes (use commas or periods instead)\n"
                    "  * Overused AI emoji: rocket, lightbulb, fire, sparkles, brain, gem, star, target, megaphone\n"
                    "  * Cliche AI phrases: 'game-changer', 'revolutionize', 'unlock', 'supercharge', "
                    "'harness the power', 'seamless', 'robust', 'elevate', 'dive into'\n"
                    "  Flag these specifically in revision_instruction if found.\n"
                    "- actionability (0-1): Can a founder copy-paste this and USE it right now? "
                    "Specifically check:\n"
                    "  * Social post: Does it have a scroll-stopping hook in the first line?\n"
                    "  * Email: Does it have a compelling subject line AND a clear CTA?\n"
                    "  * Landing copy: Does it have a headline, subhead, AND concrete benefits?\n"
                    "  * ICP notes: Does it describe a specific person, not a vague segment?\n"
                    "  * Positioning: Does it reframe the problem, not just describe the product?\n\n"
                    "CALIBRATION: A typical AI first-draft should score 0.55-0.70. "
                    "Reserve scores above 0.80 for genuinely excellent, differentiated, ready-to-ship output. "
                    "Generic output MUST score below 0.55 on relevance. "
                    "NEVER give all four dimensions above 0.80 on a first draft.\n\n"
                    "ALWAYS provide a revision_instruction with 2-3 specific improvements. "
                    "Each instruction should cite the exact section and what to fix. "
                    "Example: 'In social_post, replace the generic opener with a specific pain point "
                    "about [X]. In launch_email, add a concrete metric or customer proof point.'\n\n"
                    "If company context is provided, verify the output uses specific product features, "
                    "named competitors, real audience pain points, not surface-level name-dropping."
                    + company_block,
                ),
                (
                    "human",
                    f"Original request:\n{request.model_dump_json()}\n\n"
                    f"Agent ({response.agent}) output:\n"
                    + "\n".join(f"[{k}]: {v}" for k, v in response.output.items()),
                ),
            ]
        )

    def classify_task(self, request: AgentRequest) -> TaskClassification:
        structured_model = self.model.with_structured_output(TaskClassification)
        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a task router for a GTM AI platform. Classify the user's request "
                    "into exactly one agent capability. Available agents:\n"
                    "- content_generator: GTM content like landing pages, emails, social posts, positioning\n"
                    "- legal: legal risk scanning, compliance, privacy, terms, entity formation\n"
                    "- demo: demo rooms, prototypes, presentations, pitch walkthroughs\n"
                    "- unsupported: anything that doesn't fit the above agents\n\n"
                    "Return the agent name, your confidence (0-1), and a brief reasoning.",
                ),
                ("human", request.model_dump_json()),
            ]
        )

    def review_document(
        self,
        document_text: str,
        source_context: str,
        jurisdictions: list[str],
    ) -> DocumentReviewResult:
        structured_model = self.model.with_structured_output(DocumentReviewResult)
        scope = ", ".join(jurisdictions) if jurisdictions else "US"
        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a regulatory compliance document reviewer for startups. "
                    "Review the uploaded document against the provided regulatory sources and flag "
                    "compliance gaps, risk areas, and recommendations.\n\n"
                    "Rules:\n"
                    "- important_notice MUST state this is educational, not legal advice\n"
                    "- document_summary should concisely describe the document's purpose and scope\n"
                    "- compliance_gaps should list specific missing or inadequate provisions\n"
                    "- risk_areas should highlight provisions that could create legal exposure\n"
                    "- recommendations should be numbered, actionable improvements\n"
                    "- applicable_regulations should cite the specific regulations that apply\n"
                    "- next_steps should tell the founder what to do with these findings\n\n"
                    f"Jurisdictions in scope: {scope}",
                ),
                (
                    "human",
                    f"Document to review:\n{document_text}\n\n"
                    f"Regulatory reference sources:\n{source_context}",
                ),
            ]
        )

    def generate_legal_draft(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalDocumentDraft:
        structured_model = self.model.with_structured_output(LegalDocumentDraft)

        company_context = request.context.get("company_profile", "")
        doc_type = request.document_type or "Terms of Service"

        additional_block = ""
        if request.additional_context:
            additional_block = (
                f"\n\nAdditional context from the founder:\n{request.additional_context}"
            )

        context_block = ""
        if company_context:
            context_block = (
                f"\n\nCompany context (use this to customize the document):\n{company_context}"
            )

        return structured_model.invoke(
            [
                (
                    "system",
                    f"You are a startup legal document drafter. You create starter templates "
                    f"for founders that are grounded in their company context and applicable regulations. "
                    f"Your output is educational and clearly NOT legal advice.\n\n"
                    f"You are drafting a: {doc_type}\n\n"
                    "Rules:\n"
                    "- important_notice MUST state this is a starter template, not legal advice\n"
                    "- document_title should be the formal document name\n"
                    "- document_body should be a complete, well-structured document with numbered sections. "
                    "Use the company's actual name, product description, and details throughout. "
                    "Include all standard clauses for this document type.\n"
                    "- key_provisions should list the major provisions with brief explanations\n"
                    "- customization_notes should flag areas that need attorney review or customization\n"
                    "- jurisdiction_notes should note jurisdiction-specific requirements\n"
                    "- next_steps should tell the founder what to do with this draft\n"
                    "- follow_up_needed: if you need more information to produce a better draft, "
                    "list specific questions. Leave empty if context is sufficient.\n\n"
                    "Write in plain, readable language. Avoid unnecessary legalese where possible "
                    "while maintaining legal precision where required."
                    + context_block
                    + additional_block,
                ),
                (
                    "human",
                    f"Draft a {doc_type} for this startup.\n\n"
                    f"Founder request:\n{request.model_dump_json()}\n\n"
                    f"Reference sources:\n{source_context}",
                ),
            ]
        )

    def chat_legal(
        self,
        messages: list[LegalChatMessage],
        mode: LegalChatMode,
        source_context: str,
        company_context: str,
        document_type: str | None = None,
    ) -> LegalChatResponse:
        structured_model = self.model.with_structured_output(LegalChatResponse)

        mode_instructions = {
            LegalChatMode.LEGAL_ADVICE: (
                "You are a startup legal advisor providing educational guidance. "
                "Help founders understand legal risks, compliance requirements, and regulatory obligations. "
                "Cover areas like: entity formation, IP protection, employment law, data privacy, "
                "contract essentials, securities compliance, and industry-specific regulations.\n\n"
                "Be specific and actionable. Reference the regulatory sources provided. "
                "When you identify areas that need more detail, include follow-up questions."
            ),
            LegalChatMode.TAX: (
                "You are a startup tax advisor providing educational guidance. "
                "Help founders understand tax obligations, planning strategies, and compliance requirements. "
                "Cover areas like: entity tax classification, sales tax/VAT, R&D tax credits, "
                "employee vs contractor tax implications, international tax, state tax nexus, "
                "and common founder tax mistakes.\n\n"
                "Be specific about which forms, deadlines, and thresholds apply. "
                "When you need more info about their situation, include follow-up questions."
            ),
            LegalChatMode.DOCUMENT_DRAFTING: (
                "You are a legal document drafter for startups. Help founders create well-structured "
                "legal documents. When the user asks for a document, generate it in the 'document' field "
                "as a LegalDocumentDraft with proper formatting.\n\n"
                "Documents should use clear markdown formatting:\n"
                "- Use ## for major section headings\n"
                "- Use ### for subsections\n"
                "- Use numbered lists (1., 2., etc.) for clauses\n"
                "- Use **bold** for defined terms and key phrases\n"
                "- Use proper paragraph spacing\n"
                "- Include the company's actual name and details throughout\n"
                "- Write in plain, readable language while maintaining legal precision\n\n"
                f"{'Document type requested: ' + document_type if document_type else 'Ask what type of document they need.'}\n\n"
                "If you need more information before drafting, ask specific questions in follow_up_questions. "
                "Only generate the document field when you have enough context to produce a quality draft."
            ),
        }

        system_prompt = (
            mode_instructions.get(mode, mode_instructions[LegalChatMode.LEGAL_ADVICE])
            + "\n\nCRITICAL RULES:\n"
            "- Your reply MUST state this is educational guidance, NOT legal advice\n"
            "- Cite specific sources when available\n"
            "- Be concrete and practical, not generic\n"
            "- Return follow_up_questions as a JSON array of strings for questions you need answered\n"
            "- Return sources_used as a JSON array of source names/URLs referenced\n"
            "- For document_drafting mode: set document field with a LegalDocumentDraft when generating a document. "
            "The document_body should be well-formatted with markdown headings, numbered clauses, and bold terms.\n"
        )

        if company_context:
            system_prompt += (
                f"\n\nCompany context (use to personalize your response):\n{company_context}\n\n"
                "Use the company details above in your response. Don't re-ask for info already provided."
            )

        if source_context:
            system_prompt += f"\n\nRegulatory reference sources:\n{source_context}"

        chat_messages: list[tuple[str, str]] = [("system", system_prompt)]
        for msg in messages:
            chat_messages.append((msg.role if msg.role == "user" else "assistant", msg.content))

        return structured_model.invoke(chat_messages)

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        structured_model = self.model.with_structured_output(SocialPost)

        platform_guidance = {
            "linkedin": (
                "LinkedIn best practices: 1000-1500 chars. "
                "Start with a bold hook line that makes people stop scrolling. "
                "Use short paragraphs (1-2 sentences each) with line breaks between them. "
                "Include a personal insight or contrarian take. 3-5 relevant hashtags at the end."
            ),
            "twitter": (
                "Twitter/X best practices: Max 280 chars. "
                "Punchy, provocative, or surprisingly insightful. "
                "Make people want to retweet. 1-2 hashtags max."
            ),
            "instagram": (
                "Instagram best practices: 500-1000 chars. "
                "Open with an emotional hook. Tell a micro-story. "
                "Use emoji strategically (not excessively). 10-15 hashtags."
            ),
            "facebook": (
                "Facebook best practices: 200-500 chars. "
                "Conversational and relatable. Ask a question or share a realization. 2-3 hashtags."
            ),
        }
        guidance = platform_guidance.get(request.platform, "Professional and engaging.")

        company_block = (
            f"\n\nCompany context (use this to ground the post):\n{company_context}"
            if company_context
            else ""
        )

        extra_block = (
            f"\n\nAdditional context from user:\n{request.extra_context}"
            if request.extra_context
            else ""
        )

        website_url = ""
        if company_context:
            for line in company_context.split("\n"):
                if line.startswith("Website:"):
                    website_url = line.split(":", 1)[1].strip()
                    break

        link_instruction = ""
        if website_url:
            link_instruction = (
                f"\n\nIMPORTANT: The company website is {website_url}. "
                "Use this actual URL in the call_to_action and anywhere a link is needed. "
                "NEVER use placeholders like '[paste the link]' or '[your-url]'."
            )

        return structured_model.invoke(
            [
                (
                    "system",
                    f"You are a top-tier social media strategist who writes posts that go viral. "
                    f"Generate a {request.platform} post that people actually want to engage with.\n\n"
                    f"Platform guidelines: {guidance}\n"
                    f"Tone: {request.tone}\n\n"
                    "CRITICAL WRITING RULES:\n"
                    "- NEVER use em dashes or long dashes. Use commas, periods, or rewrite.\n"
                    "- NEVER use these overused AI emoji: rocket, lightbulb, fire, sparkles, brain, gem, star, target, megaphone, "
                    "pointing down, muscle, chart, check mark, crystal ball, trophy.\n"
                    "- NEVER use phrases like 'game-changer', 'revolutionize', 'unlock', 'supercharge', 'seamless', "
                    "'cutting-edge', 'robust', 'elevate', 'dive into'. These scream AI.\n"
                    "- NEVER use placeholder links like '[paste the link]', '[your-url]', or '[website]'. "
                    "Use the actual company URL if available, or omit the link.\n"
                    "- Sound like a real person sharing a genuine insight, not a corporate bot.\n\n"
                    "Content rules:\n"
                    "- caption: Start with an irresistible hook (question, bold claim, or story opener). "
                    "The first line determines if anyone reads the rest. "
                    "Write like a founder sharing real experience, not a marketing bot. Ready to copy-paste.\n"
                    "- hashtags: relevant hashtags as a single string\n"
                    "- call_to_action: specific, compelling next step (not generic 'learn more'). "
                    "Include the actual website URL if available.\n"
                    "- follow_up_needed: if you need more info from the user to write a better post, "
                    "list specific questions here. Leave empty if context is sufficient."
                    + company_block
                    + extra_block
                    + link_instruction,
                ),
                (
                    "human",
                    f"Write a {request.platform} post about: {request.topic}",
                ),
            ]
        )


class ResilientLLMProvider(LLMProvider):
    def __init__(self, primary: LLMProvider, fallback: LLMProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.last_error: str | None = None

    def _try_primary(self, method_name: str, *args):
        try:
            return getattr(self.primary, method_name)(*args)
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            return getattr(self.fallback, method_name)(*args)

    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        return self._try_primary("generate_content_package", request)

    def revise_content_package(
        self,
        request: TaskRequest,
        original_output: dict[str, str],
        revision_instruction: str,
    ) -> dict[str, str]:
        return self._try_primary("revise_content_package", request, original_output, revision_instruction)

    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        return self._try_primary("generate_product_strategy", request)

    def generate_prospect_profile(self, request: CampaignCreateRequest) -> ProspectProfile:
        return self._try_primary("generate_prospect_profile", request)

    def generate_demo_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        return self._try_primary(
            "generate_demo_brief",
            request,
            product_profile,
            icp,
            prospect_profile,
        )

    def generate_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> dict[str, str]:
        return self._try_primary(
            "generate_outreach",
            request,
            product_profile,
            prospect_profile,
            demo_brief,
            demo_room_url,
        )

    def generate_demo_reply(self, demo_room: DemoRoom, message: str) -> str:
        return self._try_primary("generate_demo_reply", demo_room, message)

    def generate_qualification(self, demo_room: DemoRoom) -> QualificationReport:
        return self._try_primary("generate_qualification", demo_room)

    def generate_legal_scan(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalIssueScan:
        return self._try_primary("generate_legal_scan", request, source_context)

    def review_agent_output(
        self,
        request: AgentRequest,
        response: AgentResponse,
    ) -> LLMReviewEvaluation:
        return self._try_primary("review_agent_output", request, response)

    def classify_task(self, request: AgentRequest) -> TaskClassification:
        return self._try_primary("classify_task", request)

    def review_document(
        self,
        document_text: str,
        source_context: str,
        jurisdictions: list[str],
    ) -> DocumentReviewResult:
        return self._try_primary("review_document", document_text, source_context, jurisdictions)

    def generate_legal_draft(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalDocumentDraft:
        return self._try_primary("generate_legal_draft", request, source_context)

    def chat_legal(
        self,
        messages: list[LegalChatMessage],
        mode: LegalChatMode,
        source_context: str,
        company_context: str,
        document_type: str | None = None,
    ) -> LegalChatResponse:
        return self._try_primary("chat_legal", messages, mode, source_context, company_context, document_type)

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        return self._try_primary("generate_social_post", request, company_context)


class UnconfiguredLLMProvider(LLMProvider):
    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        self._raise_unconfigured()

    def revise_content_package(
        self,
        request: TaskRequest,
        original_output: dict[str, str],
        revision_instruction: str,
    ) -> dict[str, str]:
        self._raise_unconfigured()

    def _raise_unconfigured(self) -> None:
        raise RuntimeError(
            f"LLM provider '{settings.resolved_llm_provider}' is not configured. "
            "Set LLM_PROVIDER=mock, set LLM_PROVIDER=openai with OPENAI_API_KEY, "
            "or set PYDANTIC_AI_GATEWAY_API_KEY."
        )

    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        self._raise_unconfigured()

    def generate_prospect_profile(self, request: CampaignCreateRequest) -> ProspectProfile:
        self._raise_unconfigured()

    def generate_demo_brief(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        icp: ICPProfile,
        prospect_profile: ProspectProfile,
    ) -> DemoBrief:
        self._raise_unconfigured()

    def generate_outreach(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
        demo_room_url: str,
    ) -> dict[str, str]:
        self._raise_unconfigured()

    def generate_demo_reply(self, demo_room: DemoRoom, message: str) -> str:
        self._raise_unconfigured()

    def generate_qualification(self, demo_room: DemoRoom) -> QualificationReport:
        self._raise_unconfigured()

    def generate_legal_scan(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalIssueScan:
        self._raise_unconfigured()

    def review_agent_output(
        self,
        request: AgentRequest,
        response: AgentResponse,
    ) -> LLMReviewEvaluation:
        self._raise_unconfigured()

    def classify_task(self, request: AgentRequest) -> TaskClassification:
        self._raise_unconfigured()

    def review_document(
        self,
        document_text: str,
        source_context: str,
        jurisdictions: list[str],
    ) -> DocumentReviewResult:
        self._raise_unconfigured()

    def generate_legal_draft(
        self,
        request: AgentRequest,
        source_context: str,
    ) -> LegalDocumentDraft:
        self._raise_unconfigured()

    def chat_legal(
        self,
        messages: list[LegalChatMessage],
        mode: LegalChatMode,
        source_context: str,
        company_context: str,
        document_type: str | None = None,
    ) -> LegalChatResponse:
        self._raise_unconfigured()

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        self._raise_unconfigured()


def get_llm_provider() -> LLMProvider:
    provider = settings.resolved_llm_provider
    if provider == "gateway" and settings.resolved_gateway_api_key:
        return ResilientLLMProvider(
            OpenAILLMProvider(
                api_key=settings.resolved_gateway_api_key,
                base_url=settings.resolved_gateway_base_url,
            ),
            MockLLMProvider(),
        )
    if provider == "openai" and settings.resolved_llm_api_key:
        return ResilientLLMProvider(
            OpenAILLMProvider(api_key=settings.resolved_llm_api_key),
            MockLLMProvider(),
        )
    if provider == "mock":
        return MockLLMProvider()
    return UnconfiguredLLMProvider()
