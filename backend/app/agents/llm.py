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
from app.agents.models import ContentPackage, TaskRequest
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
        package = structured_model.invoke(
            [
                (
                    "system",
                    "You are a senior GTM content strategist. Return launch-ready structured content that is specific, practical, and concise.",
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
