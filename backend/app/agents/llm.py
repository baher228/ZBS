from abc import ABC, abstractmethod

from app.agents.campaign_models import (
    CampaignCreateRequest,
    DemoBrief,
    DemoPlan,
    DemoStep,
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
    LegalIssueScan,
    LLMReviewEvaluation,
    TaskClassification,
    TaskRequest,
)
from app.core.config import settings


class LLMProvider(ABC):
    @abstractmethod
    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        """Return GTM content sections for the generic tasks route."""

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
    def generate_demo_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
        """Return guided demo steps and talk tracks for the demo room."""

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

    def _product_theme(self, request: CampaignCreateRequest) -> dict[str, str | list[str]]:
        text = f"{request.product_name} {request.product_description}".lower()
        if "security" in text or "questionnaire" in text or "soc" in text:
            return {
                "category": "security review automation",
                "core_problem": (
                    "Enterprise security reviews slow down sales because teams repeatedly answer "
                    "long questionnaires with fragmented, manually verified information."
                ),
                "value_props": [
                    "Turns approved security knowledge into faster questionnaire responses.",
                    "Keeps answers consistent across enterprise sales cycles.",
                    "Reduces founder and engineering time spent on repetitive security reviews.",
                ],
                "proof_points": [
                    "Uses approved company knowledge instead of ad hoc answers.",
                    "Creates a repeatable security review workflow for sales teams.",
                ],
                "objections": [
                    "Can it stay accurate as policies and infrastructure change?",
                    "How does it avoid sharing sensitive security information?",
                    "Will enterprise buyers trust AI-assisted questionnaire answers?",
                ],
                "pain_points": [
                    "Enterprise security questionnaires create sales-cycle drag.",
                    "Security answers need to be accurate, approved, and consistent.",
                    "Product and engineering teams lose time to repetitive buyer diligence.",
                ],
                "asset": "Example security questionnaire workflow, approved answer library, and review/approval screen.",
            }
        if "observability" in text or "trace" in text or "agent" in text:
            return {
                "category": "AI observability",
                "core_problem": (
                    "AI engineering teams struggle to understand failures because agent runs span "
                    "prompts, tools, state transitions, and user-facing outputs."
                ),
                "value_props": [
                    "Shows agent traces, tool calls, and state transitions in one place.",
                    "Helps teams diagnose failed or low-quality agent runs faster.",
                    "Creates a clearer debugging workflow for production AI systems.",
                ],
                "proof_points": [
                    "Captures trace-level context across an agent run.",
                    "Connects failures to concrete tool calls and state changes.",
                ],
                "objections": [
                    "How much instrumentation is required?",
                    "Will this work with our existing AI stack?",
                    "Can it protect sensitive prompt and user data?",
                ],
                "pain_points": [
                    "Agent failures are hard to reproduce and explain.",
                    "Tool calls and state transitions are scattered across logs.",
                    "Engineering teams need faster incident debugging for AI workflows.",
                ],
                "asset": "Trace timeline, failed tool-call detail view, and alert/integration screen.",
            }
        return {
            "category": "B2B workflow automation",
            "core_problem": (
                "Teams have a high-friction workflow that is currently handled with manual effort, "
                "generic tools, or disconnected processes."
            ),
            "value_props": [
                f"Explains how {request.product_name} applies to the prospect's workflow.",
                "Reduces manual work in a high-friction business process.",
                "Creates a clearer path from evaluation to next action.",
            ],
            "proof_points": [
                "Uses structured product and prospect context.",
                "Turns product claims into a concrete workflow narrative.",
            ],
            "objections": [
                "How much setup is required?",
                "How does it integrate with the existing workflow?",
                "What proof is needed before adoption?",
            ],
            "pain_points": [
                "Needs clearer context on how a product applies to its own workflow.",
                "Wants to evaluate value before booking a live sales call.",
                "May need evidence that the product can address account-specific needs.",
            ],
            "asset": "Core product workflow screenshot or sandbox view.",
        }

    def generate_product_strategy(self, request: CampaignCreateRequest) -> ProductStrategy:
        audience = request.target_audience or "technical B2B founders and lean GTM teams"
        theme = self._product_theme(request)
        product_profile = ProductProfile(
            name=request.product_name,
            category=str(theme["category"]),
            one_liner=(
                f"{request.product_name} helps {audience} by solving this problem: "
                f"{request.product_description}"
            ),
            core_problem=str(theme["core_problem"]),
            key_value_props=list(theme["value_props"]),
            proof_points=list(theme["proof_points"]),
            likely_objections=list(theme["objections"]),
        )
        icp = ICPProfile(
            primary_buyer=audience,
            ideal_company=(
                "B2B companies with a concrete operational workflow where the product's value "
                "needs explanation before a buyer will commit to a call."
            ),
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
        theme = self._product_theme(request)
        description = request.prospect_description or (
            f"{request.prospect_company} appears to be a target account that could benefit "
            f"from {request.product_name}."
        )
        return ProspectProfile(
            company_name=request.prospect_company,
            description=description,
            likely_pain_points=list(theme["pain_points"]),
            relevance_angle=(
                f"Show {request.prospect_company} how {request.product_name} could help with "
                f"{list(theme['pain_points'])[0].lower()}"
            ),
            personalization_assumptions=[
                f"{request.prospect_company} has a workflow connected to {str(theme['category'])}.",
                "The prospect values concise, specific product explanations before booking time.",
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

    def generate_demo_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
        return DemoPlan(
            title=f"{product_profile.name} guided demo for {prospect_profile.company_name}",
            overview=(
                f"Guide {prospect_profile.company_name} through a concise demo focused on "
                f"{prospect_profile.likely_pain_points[0].lower()}"
            ),
            steps=[
                DemoStep(
                    id="relevance",
                    title=f"Why this matters for {prospect_profile.company_name}",
                    objective="Make the account-specific reason for the demo obvious.",
                    asset_type="docs",
                    asset_needed="Product positioning summary and prospect research brief.",
                    talk_track=prospect_profile.relevance_angle,
                    qualification_question="Is this the kind of workflow problem your team is trying to solve now?",
                    success_signal="Prospect confirms the pain or explains a related current workflow.",
                ),
                DemoStep(
                    id="core_workflow",
                    title=f"Show the core {product_profile.name} workflow",
                    objective="Demonstrate the product's main value in a concrete sequence.",
                    asset_type="screenshot",
                    asset_needed=str(self._product_theme(request)["asset"]),
                    talk_track=demo_brief.talking_points[0],
                    qualification_question="Where would this fit into your current process?",
                    success_signal="Prospect asks about implementation, integrations, or team usage.",
                ),
                DemoStep(
                    id="proof_and_objections",
                    title="Handle risk, proof, and next steps",
                    objective="Address credibility concerns and move toward a qualified next action.",
                    asset_type="docs",
                    asset_needed="Proof points, security notes, pricing notes, and objection handlers.",
                    talk_track=demo_brief.objection_handlers[0] if demo_brief.objection_handlers else product_profile.proof_points[0],
                    qualification_question="What would you need to see before trying this with a real campaign?",
                    success_signal="Prospect names a concrete requirement, blocker, or next stakeholder.",
                ),
            ],
            step_selection_rules=[
                "If the prospect asks why this is relevant, start with the relevance step.",
                "If the prospect asks how it works, move to the core workflow step.",
                "If the prospect asks about trust, pricing, or risk, move to proof and objections.",
            ],
            fallback_response=(
                "If the question does not map to a step, answer from the product and prospect context, "
                "then suggest the most relevant next demo step."
            ),
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
        if demo_room.demo_plan and any(term in lower_message for term in ["show", "demo", "walk", "step"]):
            step = demo_room.demo_plan.steps[0]
            return (
                f"I would start with '{step.title}'. {step.talk_track} "
                f"The key question for your team is: {step.qualification_question}"
            )
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

        package = structured_model.invoke(
            [
                (
                    "system",
                    "You are a senior GTM content strategist for B2B startups. "
                    "Generate launch-ready, structured content that is specific, practical, and concise.\n\n"
                    "Guidelines:\n"
                    "- positioning: one clear sentence on what the product does and for whom\n"
                    "- landing_copy: headline + subhead + 2-3 bullet points, ready to paste\n"
                    "- icp_notes: describe the ideal buyer profile with trigger events and disqualifiers\n"
                    "- launch_email: subject line + short body, personalized to the audience\n"
                    "- social_post: one punchy post under 280 chars, no hashtags unless requested\n\n"
                    "If company context is provided, use it to make every section specific to that company. "
                    "Reference actual product features, audience, and differentiators — not generic placeholders.\n"
                    "Tailor the tone, channel focus, and language to the user's inputs. "
                    "Avoid generic filler. Every sentence should be usable as-is."
                    + company_block,
                ),
                ("human", request.model_dump_json()),
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

    def generate_demo_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
        structured_model = self.model.with_structured_output(DemoPlan)
        return structured_model.invoke(
            [
                (
                    "system",
                    "Create a guided product demo plan. Include 3-5 steps, assets needed, talk tracks, qualification questions, and routing rules.",
                ),
                (
                    "human",
                    "\n".join(
                        [
                            request.model_dump_json(),
                            product_profile.model_dump_json(),
                            prospect_profile.model_dump_json(),
                            demo_brief.model_dump_json(),
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
        company_block = (
            f"\n\nCompany context (tailor ALL analysis to this company):\n{company_context}"
            if company_context
            else ""
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
                    "- next_steps should tell the founder exactly what to collect before counsel review\n\n"
                    "If company context is provided, tailor the risk summary, checklist, and counsel questions "
                    "to the specific product, industry, and audience described."
                    + company_block,
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
        return structured_model.invoke(
            [
                (
                    "system",
                    "You are a quality-assurance reviewer for AI agent output. Evaluate the agent's "
                    "response against the original request. Score each dimension 0-1:\n"
                    "- relevance: does the output address the user's specific request?\n"
                    "- completeness: are all expected sections present and substantive?\n"
                    "- clarity: is the output well-structured, concise, and free of filler?\n"
                    "- actionability: can the founder act on this output immediately?\n\n"
                    "Provide concrete feedback. If revision is needed, give a specific instruction.",
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

    def generate_demo_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
        return self._try_primary(
            "generate_demo_plan",
            request,
            product_profile,
            prospect_profile,
            demo_brief,
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


class UnconfiguredLLMProvider(LLMProvider):
    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
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

    def generate_demo_plan(
        self,
        request: CampaignCreateRequest,
        product_profile: ProductProfile,
        prospect_profile: ProspectProfile,
        demo_brief: DemoBrief,
    ) -> DemoPlan:
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
