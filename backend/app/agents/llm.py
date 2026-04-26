import json
import logging
from abc import ABC, abstractmethod
from typing import Any

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
    ContentChatMessage,
    ContentChatResponse,
    ContentPackage,
    DocumentReviewResult,
    LegalChatMessage,
    LegalChatMode,
    LegalChatResponse,
    LegalDocumentDraft,
    LegalIssueScan,
    LegalOverviewResponse,
    LLMReviewEvaluation,
    MarketingResearchMessage,
    MarketingResearchResponse,
    SocialPost,
    SocialPostRequest,
    TaskClassification,
    TaskRequest,
)
from app.core.config import settings

logger = logging.getLogger(__name__)
_LAST_LLM_ERROR: str | None = None


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
    def generate_legal_overview(
        self,
        company_context: str,
        source_context: str,
    ) -> LegalOverviewResponse:
        """Generate a legal overview for a company, flagging potential issues."""

    @abstractmethod
    def chat_content(
        self,
        messages: list[ContentChatMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> ContentChatResponse:
        """Handle a multi-turn content creation chat conversation."""

    @abstractmethod
    def chat_marketing_research(
        self,
        messages: list[MarketingResearchMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> MarketingResearchResponse:
        """Handle a multi-turn marketing research chat conversation."""

    @abstractmethod
    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        """Generate a social media post tailored to a platform."""


def _format_content_follow_up_reply(questions: list[str]) -> str:
    trimmed = [q.strip() for q in questions if q.strip()][:4]
    if not trimmed:
        return ""

    lines = ["I need these exact details before I write it:"]
    lines.extend(f"- {question}" for question in trimmed)
    lines.append("Reply with those details in one message and I will draft the content.")
    return "\n".join(lines)


def _unpack_embedded_content_response(response: ContentChatResponse) -> ContentChatResponse:
    text = response.reply.strip()
    if not text.startswith("{"):
        return response

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return response

    if not isinstance(payload, dict):
        return response

    content_fields = {"reply", "generated_content", "follow_up_questions", "content_ready"}
    if not content_fields.intersection(payload):
        return response

    merged = response.model_dump()
    for field in content_fields:
        if field in payload:
            merged[field] = payload[field]

    try:
        return ContentChatResponse.model_validate(merged)
    except Exception:
        logger.warning("Failed to unpack embedded content response JSON", exc_info=True)
        return response


def _normalize_content_chat_response(response: ContentChatResponse) -> ContentChatResponse:
    response = _unpack_embedded_content_response(response)
    questions = [q.strip() for q in response.follow_up_questions if q.strip()][:4]
    if not questions:
        reply = response.reply
        if response.generated_content and reply.strip().startswith("{"):
            reply = "I drafted the content below."
        elif response.generated_content and not reply.strip():
            reply = "I drafted the content below."
        return ContentChatResponse(
            reply=reply,
            follow_up_questions=[],
            content_ready=response.content_ready,
            generated_content=response.generated_content,
        )

    return ContentChatResponse(
        reply=_format_content_follow_up_reply(questions),
        follow_up_questions=questions,
        content_ready=False,
        generated_content=None,
    )


def _use_short_dashes(text: str) -> str:
    cleaned = text.replace("—", " - ").replace("–", "-")
    while "  " in cleaned:
        cleaned = cleaned.replace("  ", " ")
    return cleaned


def _format_legal_follow_up_reply(questions: list[str]) -> str:
    trimmed = [_use_short_dashes(q.strip()) for q in questions if q.strip()][:4]
    if not trimmed:
        return ""

    lines = ["I need these exact details before I can draft this properly:"]
    lines.extend(f"- {question}" for question in trimmed)
    lines.append("Reply with those details in one message and I will produce the draft.")
    return "\n".join(lines)


def _unpack_embedded_legal_response(response: LegalChatResponse) -> LegalChatResponse:
    text = response.reply.strip()
    if not text.startswith("{"):
        return response

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return response

    if not isinstance(payload, dict):
        return response

    legal_fields = {"reply", "document", "follow_up_questions", "mode", "sources_used"}
    if not legal_fields.intersection(payload):
        return response

    merged = response.model_dump()
    for field in legal_fields:
        if field in payload:
            merged[field] = payload[field]

    try:
        return LegalChatResponse.model_validate(merged)
    except Exception:
        logger.warning("Failed to unpack embedded legal response JSON", exc_info=True)
        return response


def _normalize_legal_chat_response(response: LegalChatResponse) -> LegalChatResponse:
    response = _unpack_embedded_legal_response(response)
    questions = [_use_short_dashes(q.strip()) for q in response.follow_up_questions if q.strip()][:4]
    reply = _use_short_dashes(response.reply)
    document = response.document

    if document is not None:
        document = LegalDocumentDraft.model_validate(
            {key: _use_short_dashes(value) if isinstance(value, str) else value for key, value in document.model_dump().items()}
        )
        document.important_notice = ""
        if reply.strip().startswith("{"):
            reply = ""

    if questions:
        reply = _format_legal_follow_up_reply(questions)
        document = None
    elif document is not None and not reply.strip():
        reply = "I drafted the document below."

    return LegalChatResponse(
        reply=reply,
        document=document,
        follow_up_questions=[],
        mode=response.mode,
        sources_used=[_use_short_dashes(source) for source in response.sources_used],
    )


def _json_objects_in_text(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    return objects


def _format_research_value(value: Any, level: int = 0) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return _use_short_dashes(value)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list):
        lines: list[str] = []
        for item in value:
            if isinstance(item, dict):
                lines.append(_format_research_value(item, level + 1))
            else:
                lines.append(f"- {_format_research_value(item, level + 1)}")
        return "\n".join(line for line in lines if line.strip())
    if isinstance(value, dict):
        lines = []
        for key, nested in value.items():
            label = str(key).replace("_", " ").title()
            formatted = _format_research_value(nested, level + 1)
            if not formatted:
                continue
            if isinstance(nested, list | dict):
                lines.append(f"### {label}\n{formatted}" if level == 0 else f"**{label}**\n{formatted}")
            else:
                lines.append(f"**{label}:** {formatted}")
        return "\n\n".join(lines)
    return _use_short_dashes(str(value))


def _normalize_research_data(data: dict[str, Any] | None) -> dict[str, str] | None:
    if not data:
        return None

    normalized: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, str) and "see embedded JSON above" in value:
            continue
        formatted = _format_research_value(value).strip()
        if formatted:
            normalized[str(key)] = formatted

    return normalized or None


def _normalize_marketing_research_response(response: MarketingResearchResponse) -> MarketingResearchResponse:
    reply = _use_short_dashes(response.reply)
    data: dict[str, Any] | None = dict(response.research_data) if response.research_data else None

    embedded_candidates = _json_objects_in_text(reply)
    for candidate in embedded_candidates:
        if isinstance(candidate.get("research_data"), dict):
            data = candidate["research_data"]
            break
        research_keys = {
            "competitor_analysis",
            "competitor_matrix",
            "positioning_opportunities",
            "go_to_market_implications",
            "market_size",
            "audience_research",
            "trend_analysis",
        }
        if research_keys.intersection(candidate):
            data = candidate

    for marker in ("research_ready=true", "research_ready = true", "research_data"):
        marker_index = reply.find(marker)
        if marker_index != -1:
            reply = reply[:marker_index].strip()
            break

    return MarketingResearchResponse(
        reply=reply or "Here is the research breakdown.",
        follow_up_questions=[_use_short_dashes(q.strip()) for q in response.follow_up_questions if q.strip()][:4],
        research_ready=response.research_ready or bool(data),
        research_data=_normalize_research_data(data),
    )


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
                "This is a legal risk scan for founders. "
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
                "This is an automated compliance review. "
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
            important_notice="",
            document_title=f"{doc_type} - {idea}",
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
                f"Areas to customize for {idea}:\n"
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
            "Consult a qualified attorney for specific advice."
        )

        document = None
        if mode == LegalChatMode.DOCUMENT_DRAFTING and document_type:
            document = LegalDocumentDraft(
                important_notice="",
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

    def generate_legal_overview(
        self,
        company_context: str,
        source_context: str,
    ) -> LegalOverviewResponse:
        from app.agents.models import LegalOverviewIssue

        return LegalOverviewResponse(
            summary="[Mock Overview] Based on your company profile, here is a legal overview. "
            "Consult a qualified attorney for specific advice.",
            potential_issues=[
                LegalOverviewIssue(
                    title="Privacy Policy Required",
                    severity="high",
                    description="Your product likely collects user data, requiring a privacy policy under GDPR/CCPA.",
                    recommendation="Draft a privacy policy covering data collection, usage, and user rights.",
                ),
                LegalOverviewIssue(
                    title="Terms of Service",
                    severity="high",
                    description="A Terms of Service agreement is essential to limit liability.",
                    recommendation="Create ToS covering user responsibilities, limitations, and dispute resolution.",
                ),
                LegalOverviewIssue(
                    title="Intellectual Property Protection",
                    severity="medium",
                    description="Consider protecting your IP through trademarks and patents.",
                    recommendation="Consult an IP attorney to evaluate trademark and patent opportunities.",
                ),
            ],
            recommended_documents=[
                "Privacy Policy",
                "Terms of Service",
                "Non-Disclosure Agreement",
                "Employee/Contractor Agreement",
                "Cookie Policy",
            ],
            missing_info=[
                "What personal data do you collect from users?",
                "Do you have employees or only contractors?",
                "Are you handling payment processing directly?",
            ],
            compliance_areas=["Data Privacy (GDPR/CCPA)", "Consumer Protection", "Employment Law"],
        )

    def chat_content(
        self,
        messages: list[ContentChatMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> ContentChatResponse:
        last_msg = messages[-1].content if messages else "content creation"
        workflow_label = f" [{workflow}]" if workflow else ""
        if "launch" in last_msg.lower() and not company_context:
            questions = [
                "Product name and one-line description.",
                "Target audience and the main pain point.",
                "Primary call to action and link.",
            ]
            return ContentChatResponse(
                reply=_format_content_follow_up_reply(questions),
                follow_up_questions=questions,
                content_ready=False,
                generated_content=None,
            )
        return ContentChatResponse(
            reply=(
                f"[Mock content response{workflow_label}] Here is the content for: {last_msg[:100]}."
            ),
            follow_up_questions=[],
            content_ready=True,
            generated_content={"draft": f"Mock generated content for: {last_msg[:100]}"},
        )

    def chat_marketing_research(
        self,
        messages: list[MarketingResearchMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> MarketingResearchResponse:
        last_msg = messages[-1].content if messages else "market research"
        workflow_label = f" [{workflow}]" if workflow else ""
        return MarketingResearchResponse(
            reply=(
                f"[Mock research response{workflow_label}] Here is the research for: {last_msg[:100]}."
            ),
            follow_up_questions=[],
            research_ready=True,
            research_data=(
                {
                    "competitor_matrix": (
                        "| Competitor | Positioning | Strengths | Weaknesses | Opportunity |\n"
                        "| --- | --- | --- | --- | --- |\n"
                        "| Established suite | Broad all-in-one platform | Brand trust, large feature set | Expensive, slow setup | Win with sharper onboarding and faster time to value |\n"
                        "| AI-first startup | Automated workflows for modern teams | Strong messaging, modern UX | Narrow integrations | Differentiate with better data depth and proof points |\n"
                        "| Manual services | Human-led consulting | High-touch support | Hard to scale, costly | Position as software speed with expert-grade outputs |"
                    ),
                    "analysis": f"Mock market research for: {last_msg[:100]}",
                }
                if workflow == "competitor_analysis"
                else {"analysis": f"Mock market research for: {last_msg[:100]}"}
            ),
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

        from app.agents.mubit_integration import initialize_mubit_learning

        initialize_mubit_learning()

        resolved_key = api_key or settings.resolved_llm_api_key

        self.model = ChatOpenAI(
            model=settings.resolved_llm_model,
            api_key=resolved_key,
            base_url=base_url,
            max_retries=settings.llm_max_retries,
            timeout=settings.llm_timeout_seconds,
        )

        self.content_model = ChatOpenAI(
            model=settings.resolved_llm_model,
            api_key=resolved_key,
            base_url=base_url,
            temperature=1.1,
            max_retries=settings.llm_max_retries,
            timeout=settings.llm_content_timeout_seconds,
        )

    def generate_content_package(self, request: TaskRequest) -> dict[str, str]:
        structured_model = self.content_model.with_structured_output(ContentPackage)

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
                    "You are a creative content writer for startups. Write with a distinctive "
                    "human voice. You decide the tone, style, and approach.\n\n"
                    "Write content that sounds like a real person, not a corporate bot. "
                    "Use the company's actual website URL for links. Never use placeholder links.\n\n"
                    "Sections: positioning, landing_copy, icp_notes, launch_email, social_post. "
                    "Each should be ready to use as-is."
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

        if company_context:
            context_instruction = (
                f"\n\nCompany context (already provided - do NOT ask for info that is here):\n{company_context}\n\n"
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
                    "compliance, and legal risks before launch. Your output is "
                    "source-grounded. Always cite the specific public "
                    "guidance documents provided. Be concrete and practical.\n\n"
                    "Rules:\n"
                    "- important_notice MUST include a notice that a qualified attorney should review\n"
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
                    f"You are a startup legal document drafter. You create formal documents "
                    f"for founders that are grounded in their company context and applicable regulations.\n\n"
                    f"You are drafting a: {doc_type}\n\n"
                    "Rules:\n"
                    "- important_notice MUST be an empty string.\n"
                    "- document_title should be the formal document name only, in title case.\n"
                    "- document_body should read like real paperwork, not an explanatory answer. "
                    "Use formal document formatting inspired by public examples such as GOV.UK employment particulars, "
                    "ICO privacy notices, commercial terms, and YC financing forms.\n"
                    "- For contracts and agreements, use this layout where relevant: document title, effective date, parties, "
                    "background/recitals, definitions, numbered operative clauses, boilerplate clauses, schedules/annexes, "
                    "and signature blocks.\n"
                    "- For policies and privacy notices, use this layout where relevant: title, last updated date, who we are, "
                    "scope, what data/information is covered, purposes, lawful basis where applicable, sharing, retention, "
                    "rights, security, contact details, and changes to this notice.\n"
                    "- Use numbered clauses like '1. Appointment', '1.1 Duties', '1.2 Standard of Performance'. "
                    "Use schedules for role details, fees, services, or processing details.\n"
                    "- Use bracketed placeholders only for genuinely missing legal facts, for example [Start Date]. "
                    "Do not insert disclaimers, advisory notices, or 'for review only' language.\n"
                    "- key_provisions should list the major provisions with brief explanations.\n"
                    "- customization_notes should list missing facts or choices the founder may still need to fill in, without legal disclaimers.\n"
                    "- jurisdiction_notes should note jurisdiction-specific requirements.\n"
                    "- next_steps should be practical completion steps, such as fill placeholders, confirm party details, and collect signatures.\n"
                    "- follow_up_needed: if you need more information to produce a better draft, "
                    "list specific questions. Leave empty if context is sufficient.\n\n"
                    "Style:\n"
                    "- Use the same formal paperwork tone and layout seen in real contracts, policies, notices, and standard forms.\n"
                    "- Keep clauses concise, precise, and copy-paste ready.\n"
                    "- Do not use em dashes or en dashes. Use short hyphens (-), commas, periods, or semicolons instead."
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
                "You are a startup legal advisor. "
                "Help founders understand legal risks, compliance requirements, and regulatory obligations. "
                "Cover areas like: entity formation, IP protection, employment law, data privacy, "
                "contract essentials, securities compliance, and industry-specific regulations.\n\n"
                "Be specific and actionable. Reference the regulatory sources provided. "
                "When you identify areas that need more detail, include follow-up questions."
            ),
            LegalChatMode.TAX: (
                "You are a startup tax advisor. "
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
                "- important_notice must be an empty string\n"
                "- Do not include disclaimers, advisory notices, or 'for review only' language\n"
                "- Use ## for major document sections\n"
                "- Use ### for subsections and numbered clauses\n"
                "- Use numbered clauses with legal-document style labels, for example '1. Appointment' and '1.1 Duties'\n"
                "- For contracts, include title, effective date, parties, background/recitals, definitions, operative clauses, schedules where useful, and signature blocks\n"
                "- For policies/privacy notices, include title, last updated date, who we are, scope, purposes, lawful basis where applicable, retention, rights, contact details, and changes\n"
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
            "- Be specific and actionable in your guidance\n"
            "- Cite specific sources when available\n"
            "- Be concrete and practical, not generic\n"
            "- Do not use em dashes or en dashes. Use short hyphens (-), commas, periods, or semicolons instead.\n"
            "- Ask follow-up questions only when missing facts would make the answer or draft inaccurate.\n"
            "- If follow-up questions are needed, ask them yourself in one structured reply. "
            "Make them exact, practical, and cap them at 4 total.\n"
            "- Return follow_up_questions as a JSON array only for the exact questions you already asked in the reply. "
            "Do not create clickable suggested prompts for the user.\n"
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

        return _normalize_legal_chat_response(structured_model.invoke(chat_messages))

    def generate_legal_overview(
        self,
        company_context: str,
        source_context: str,
    ) -> LegalOverviewResponse:
        structured_model = self.model.with_structured_output(LegalOverviewResponse)

        system_prompt = (
            "You are a startup legal analyst. Given a company's profile, generate a comprehensive "
            "legal overview that identifies potential legal issues, recommends documents to prepare, "
            "and flags compliance areas.\n\n"
            "Do not use em dashes or en dashes. Use short hyphens (-), commas, periods, or semicolons instead.\n\n"
            "For each potential issue, assess severity (high/medium/low) based on:\n"
            "- high: immediate legal risk or regulatory requirement\n"
            "- medium: important but not immediately critical\n"
            "- low: good practice but not urgent\n\n"
            "In 'missing_info', list specific questions about information you'd need from the founder "
            "to give more targeted advice. These should be practical questions about their business "
            "operations, data practices, team structure, etc.\n\n"
            "In 'recommended_documents', list legal documents this company should have.\n"
            "In 'compliance_areas', list regulatory areas relevant to their business.\n\n"
            "Provide actionable, specific guidance grounded in the company context."
        )

        human_msg = "Generate a legal overview for this company."
        if company_context:
            human_msg += f"\n\nCompany context:\n{company_context}"
        if source_context:
            human_msg += f"\n\nRegulatory reference sources:\n{source_context}"

        overview = structured_model.invoke([("system", system_prompt), ("human", human_msg)])
        overview.summary = _use_short_dashes(overview.summary)
        overview.recommended_documents = [_use_short_dashes(item) for item in overview.recommended_documents]
        overview.missing_info = [_use_short_dashes(item) for item in overview.missing_info]
        overview.compliance_areas = [_use_short_dashes(item) for item in overview.compliance_areas]
        for issue in overview.potential_issues:
            issue.title = _use_short_dashes(issue.title)
            issue.description = _use_short_dashes(issue.description)
            issue.recommendation = _use_short_dashes(issue.recommendation)
        return overview

    def chat_content(
        self,
        messages: list[ContentChatMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> ContentChatResponse:
        structured_model = self.content_model.with_structured_output(ContentChatResponse)

        workflow_hint = ""
        if workflow:
            workflow_hint = f"\nThe user selected the '{workflow.replace('_', ' ')}' workflow."

        system_prompt = (
            "You are a creative content writer with a distinctive human voice. "
            "Write like a real person - not a corporate marketing bot.\n\n"
            "Rules:\n"
            "- Generate content immediately when the request has enough concrete context. "
            "Set content_ready=true and put output in generated_content.\n"
            "- You decide the tone, style, platform specifics, and structure. "
            "Only follow specific constraints if the user explicitly asks for them.\n"
            "- Write with personality, opinion, and edge. Avoid generic marketing speak.\n"
            "- Do not use em dashes or en dashes. Use short hyphens (-), commas, periods, or semicolons instead.\n"
            "- Use the company's real website URL if available. Never use placeholder links.\n"
            "- Ask follow-up questions only when a missing detail would force you to invent core facts "
            "such as product name, audience, offer, launch timing, CTA, link, or required assets.\n"
            "- If follow-up questions are needed, set content_ready=false, set generated_content=null, "
            "and put every question in follow_up_questions. Do not generate a draft in the same response.\n"
            "- Follow-up questions must be exact, practical, and capped at 4 total. "
            "Ask for multiple details inside one question when they belong together.\n"
            "- The reply must be one structured assistant message that asks for what you need. "
            "Do not make the user click suggested prompts or ask questions on your behalf.\n"
            "- generated_content keys should be descriptive (e.g. 'linkedin_post', 'email_draft')."
            + workflow_hint
        )

        if company_context:
            system_prompt += (
                f"\n\nCompany context (use to personalize):\n{company_context}\n\n"
                "Use these details in your suggestions. Don't re-ask for info already provided."
            )

        chat_messages: list[tuple[str, str]] = [("system", system_prompt)]
        for msg in messages:
            chat_messages.append((msg.role if msg.role == "user" else "assistant", msg.content))

        return _normalize_content_chat_response(structured_model.invoke(chat_messages))

    def chat_marketing_research(
        self,
        messages: list[MarketingResearchMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> MarketingResearchResponse:
        structured_model = self.model.with_structured_output(MarketingResearchResponse)

        workflow_hint = ""
        if workflow:
            workflow_hint = f"\nThe user selected the '{workflow.replace('_', ' ')}' workflow."

        system_prompt = (
            "You are an expert marketing research analyst. "
            "Provide data-driven, actionable market intelligence.\n\n"
            "Rules:\n"
            "- Deliver research immediately. Set research_ready=true and put findings in research_data.\n"
            "- Use specific numbers, percentages, and data points wherever possible.\n"
            "- Cite real market trends, competitor names, and industry benchmarks.\n"
            "- Do not print JSON, research_ready flags, or research_data inside reply. "
            "Reply should be a clean human-readable summary only.\n"
            "- research_data must be a flat object where every value is a string. "
            "Do not put nested objects, arrays, booleans, or numbers inside research_data values. "
            "If a finding has bullets or nested details, write them as markdown inside one string.\n"
            "- research_data keys should be descriptive (e.g. 'competitor_analysis', 'market_size', 'positioning_map').\n"
            "- Only ask follow-up questions if you need critical missing info about their product or market."
            + workflow_hint
        )

        if workflow == "competitor_analysis":
            system_prompt += (
                "\n- For competitor analysis, include a research_data.competitor_matrix value as a markdown table. "
                "Use these columns: Competitor, Positioning, Strengths, Weaknesses, Pricing/Market signal, Opportunity. "
                "Keep cells concise and specific so the UI can render a clean comparison table. "
                "Put positioning opportunities in research_data.positioning_opportunities as a markdown string, not an object."
            )

        if company_context:
            system_prompt += (
                f"\n\nCompany context (use to ground research):\n{company_context}\n\n"
                "Use these details to personalize all research. Don't re-ask for info already provided."
            )

        chat_messages: list[tuple[str, str]] = [("system", system_prompt)]
        for msg in messages:
            chat_messages.append((msg.role if msg.role == "user" else "assistant", msg.content))

        return _normalize_marketing_research_response(structured_model.invoke(chat_messages))

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        structured_model = self.content_model.with_structured_output(SocialPost)

        company_block = (
            f"\n\nCompany context:\n{company_context}"
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
                f"\n\nThe company website is {website_url}. "
                "Use this actual URL where a link is needed. Never use placeholder links."
            )

        return structured_model.invoke(
            [
                (
                    "system",
                    f"You are a creative social media writer. Write a {request.platform} post "
                    "that sounds like a real human wrote it. You decide the tone, style, and structure. "
                    "Write with personality and edge.\n\n"
                    "Output:\n"
                    "- caption: the post text, ready to copy-paste\n"
                    "- hashtags: relevant hashtags\n"
                    "- call_to_action: a natural next step for the reader\n"
                    "- follow_up_needed: leave empty unless you need specific info"
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
        global _LAST_LLM_ERROR
        try:
            _LAST_LLM_ERROR = None
            return getattr(self.primary, method_name)(*args)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "Primary LLM failed for %s: %s: %s — falling back to mock",
                method_name, exc.__class__.__name__, exc,
            )
            self.last_error = f"{method_name}: {exc.__class__.__name__}"
            _LAST_LLM_ERROR = self.last_error
            logger.exception("LLM provider failed in %s; using fallback provider", method_name)
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
        try:
            return self.primary.chat_legal(messages, mode, source_context, company_context, document_type)
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            logger.exception("LLM provider failed in chat_legal")
            raise

    def generate_legal_overview(
        self,
        company_context: str,
        source_context: str,
    ) -> LegalOverviewResponse:
        try:
            return self.primary.generate_legal_overview(company_context, source_context)
        except Exception as exc:
            self.last_error = exc.__class__.__name__
            logger.exception("LLM provider failed in generate_legal_overview")
            raise

    def chat_content(
        self,
        messages: list[ContentChatMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> ContentChatResponse:
        return self._try_primary("chat_content", messages, company_context, workflow)

    def chat_marketing_research(
        self,
        messages: list[MarketingResearchMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> MarketingResearchResponse:
        try:
            global _LAST_LLM_ERROR
            _LAST_LLM_ERROR = None
            return self.primary.chat_marketing_research(messages, company_context, workflow)
        except Exception as exc:
            self.last_error = f"chat_marketing_research: {exc.__class__.__name__}"
            _LAST_LLM_ERROR = self.last_error
            logger.exception("LLM provider failed in chat_marketing_research")
            raise

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

    def generate_legal_overview(
        self,
        company_context: str,
        source_context: str,
    ) -> LegalOverviewResponse:
        self._raise_unconfigured()

    def chat_content(
        self,
        messages: list[ContentChatMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> ContentChatResponse:
        self._raise_unconfigured()

    def chat_marketing_research(
        self,
        messages: list[MarketingResearchMessage],
        company_context: str,
        workflow: str | None = None,
    ) -> MarketingResearchResponse:
        self._raise_unconfigured()

    def generate_social_post(
        self,
        request: SocialPostRequest,
        company_context: str,
    ) -> SocialPost:
        self._raise_unconfigured()


def get_last_llm_error() -> str | None:
    return _LAST_LLM_ERROR


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
