from __future__ import annotations

from app.live_demo.models import (
    DemoElement,
    DemoFlow,
    DemoFlowStep,
    DemoManifest,
    DemoPageManifest,
    KnowledgeRecord,
    PageAction,
)


def build_demeo_manifest() -> DemoManifest:
    pages = [
        DemoPageManifest(
            page_id="setup",
            route="/demo-room/live",
            title="Founder setup",
            summary="Collects the product URL, target persona, walkthrough, Q&A, CTA, and qualification questions.",
            visible_concepts=["startup input", "sandbox URL", "persona", "walkthrough"],
            elements=[
                DemoElement(
                    id="product-url",
                    label="Product URL",
                    role="input",
                    description="The sandbox or staging product URL the demo agent will show.",
                    selector="[data-demo-id='product-url']",
                ),
                DemoElement(
                    id="persona-card",
                    label="Target persona",
                    role="card",
                    description="Defines who this demo room is personalized for.",
                    selector="[data-demo-id='persona-card']",
                ),
                DemoElement(
                    id="walkthrough-card",
                    label="Founder walkthrough",
                    role="card",
                    description="Plain-English path the founder wants the agent to demonstrate.",
                    selector="[data-demo-id='walkthrough-card']",
                ),
                DemoElement(
                    id="build-manifest",
                    label="Build demo manifest",
                    role="button",
                    description="Compiles inputs into page knowledge, actions, flow graph, and answers.",
                    selector="[data-demo-id='build-manifest']",
                    safe_to_click=True,
                    requires_approval=True,
                ),
            ],
            allowed_actions=[
                PageAction(
                    id="show_setup_inputs",
                    type="highlight",
                    label="Show founder inputs",
                    element_id="product-url",
                    intent="explain_startup_inputs",
                ),
                PageAction(
                    id="open_knowledge",
                    type="navigate",
                    label="Open knowledge bank",
                    target_page_id="knowledge",
                    intent="explain_approved_knowledge",
                ),
                PageAction(
                    id="open_flow",
                    type="navigate",
                    label="Open flow builder",
                    target_page_id="flow",
                    intent="explain_demo_actions",
                ),
            ],
        ),
        DemoPageManifest(
            page_id="knowledge",
            route="/demo-room/live",
            title="Knowledge bank",
            summary="Approved product facts, sensitive answers, restricted claims, and qualification prompts.",
            visible_concepts=["approved Q&A", "pricing", "security", "restricted claims"],
            elements=[
                DemoElement(
                    id="approved-qna",
                    label="Approved Q&A",
                    role="panel",
                    description="Answers the agent can safely use during the demo.",
                    selector="[data-demo-id='approved-qna']",
                ),
                DemoElement(
                    id="restricted-claims",
                    label="Restricted claims",
                    role="panel",
                    description="Topics the agent must avoid or qualify carefully.",
                    selector="[data-demo-id='restricted-claims']",
                ),
                DemoElement(
                    id="qualification-rules",
                    label="Qualification rules",
                    role="panel",
                    description="Signals the agent tracks while talking to the prospect.",
                    selector="[data-demo-id='qualification-rules']",
                ),
            ],
            allowed_actions=[
                PageAction(
                    id="show_approved_answers",
                    type="highlight",
                    label="Show approved answers",
                    element_id="approved-qna",
                    intent="answer_sensitive_questions",
                ),
                PageAction(
                    id="open_live_room",
                    type="navigate",
                    label="Open live demo room",
                    target_page_id="live_room",
                    intent="show_prospect_experience",
                ),
            ],
        ),
        DemoPageManifest(
            page_id="flow",
            route="/demo-room/live",
            title="Flow graph",
            summary="The approved path the agent can adapt from, with page-local actions and safe click rules.",
            visible_concepts=["page-local actions", "flow graph", "safety gate", "cursor events"],
            elements=[
                DemoElement(
                    id="flow-graph",
                    label="Demo flow graph",
                    role="section",
                    description="Maps prospect intents to demo pages and allowed actions.",
                    selector="[data-demo-id='flow-graph']",
                ),
                DemoElement(
                    id="page-actions",
                    label="Page-local actions",
                    role="panel",
                    description="Only actions available on the current page are exposed to the agent.",
                    selector="[data-demo-id='page-actions']",
                ),
                DemoElement(
                    id="safety-gate",
                    label="Safety gate",
                    role="panel",
                    description="Validates every proposed click, highlight, and navigation.",
                    selector="[data-demo-id='safety-gate']",
                ),
            ],
            allowed_actions=[
                PageAction(
                    id="show_page_actions",
                    type="highlight",
                    label="Show page-local actions",
                    element_id="page-actions",
                    intent="explain_safe_actions",
                ),
                PageAction(
                    id="show_safety_gate",
                    type="highlight",
                    label="Show safety gate",
                    element_id="safety-gate",
                    intent="explain_safety",
                ),
                PageAction(
                    id="open_live_room_from_flow",
                    type="navigate",
                    label="Preview live room",
                    target_page_id="live_room",
                    intent="show_prospect_experience",
                ),
            ],
        ),
        DemoPageManifest(
            page_id="live_room",
            route="/demo-room/live",
            title="Prospect demo room",
            summary="The prospect-facing room where the agent chats, narrates, moves the cursor, and shows the product.",
            visible_concepts=["agent cursor", "voice", "chat", "visual events"],
            elements=[
                DemoElement(
                    id="agent-cursor-preview",
                    label="Agent cursor",
                    role="section",
                    description="The visible cursor that moves over the product while the agent explains.",
                    selector="[data-demo-id='agent-cursor-preview']",
                ),
                DemoElement(
                    id="voice-control",
                    label="Voice control",
                    role="button",
                    description="Realtime voice can plug into the same event loop through Gemini Live.",
                    selector="[data-demo-id='voice-control']",
                    safe_to_click=True,
                ),
                DemoElement(
                    id="event-stream",
                    label="Event stream",
                    role="panel",
                    description="Shows the live timeline of say, navigate, cursor, highlight, and lead events.",
                    selector="[data-demo-id='event-stream']",
                ),
            ],
            allowed_actions=[
                PageAction(
                    id="show_agent_cursor",
                    type="highlight",
                    label="Show agent cursor",
                    element_id="agent-cursor-preview",
                    intent="explain_visual_demo",
                ),
                PageAction(
                    id="show_voice_control",
                    type="highlight",
                    label="Show voice control",
                    element_id="voice-control",
                    intent="explain_voice",
                ),
                PageAction(
                    id="open_summary",
                    type="navigate",
                    label="Open lead summary",
                    target_page_id="summary",
                    intent="explain_qualification",
                ),
            ],
        ),
        DemoPageManifest(
            page_id="summary",
            route="/demo-room/live",
            title="Qualification summary",
            summary="Lead score, buying signals, objections, and follow-up after the agent-led demo.",
            visible_concepts=["lead score", "CRM note", "follow-up email", "objections"],
            elements=[
                DemoElement(
                    id="lead-score",
                    label="Lead score",
                    role="chart",
                    description="Live score based on use case, urgency, fit, and buying signals.",
                    selector="[data-demo-id='lead-score']",
                ),
                DemoElement(
                    id="crm-summary",
                    label="CRM summary",
                    role="panel",
                    description="Structured summary for the founder's CRM.",
                    selector="[data-demo-id='crm-summary']",
                ),
                DemoElement(
                    id="follow-up",
                    label="Follow-up email",
                    role="panel",
                    description="Drafted follow-up based on the actual demo conversation.",
                    selector="[data-demo-id='follow-up']",
                ),
            ],
            allowed_actions=[
                PageAction(
                    id="show_lead_score",
                    type="highlight",
                    label="Show lead score",
                    element_id="lead-score",
                    intent="explain_qualification",
                ),
                PageAction(
                    id="show_crm_summary",
                    type="highlight",
                    label="Show CRM summary",
                    element_id="crm-summary",
                    intent="explain_follow_up",
                ),
            ],
        ),
    ]
    return DemoManifest(
        startup_id="demeo",
        product_name="Demeo",
        product_description=(
            "Demeo helps technical B2B founders turn their product into a guided "
            "buyer demo. A prospect receives a link to an AI-led experience that "
            "explains the product, answers questions, qualifies the opportunity, "
            "and prepares follow-up for the founder."
        ),
        target_persona="Technical B2B founder selling to qualified prospects without a sales team",
        cta="Book a setup call to connect your first product demo room.",
        pages=pages,
        flows=[
            DemoFlow(
                id="founder_setup_to_qualified_lead",
                name="Founder setup to qualified lead",
                goal="Show how a founder creates an agent-led demo room and receives qualification output.",
                entry_page_id="setup",
                steps=[
                    DemoFlowStep(
                        id="setup_inputs",
                        page_id="setup",
                        objective="Explain what the founder provides.",
                        talk_track="The founder starts with a product URL, persona, walkthrough, approved Q&A, CTA, and qualification questions.",
                        recommended_action_ids=["show_setup_inputs"],
                    ),
                    DemoFlowStep(
                        id="knowledge_guardrails",
                        page_id="knowledge",
                        objective="Explain approved knowledge and restricted claims.",
                        talk_track="The agent can answer from approved knowledge and avoids unsupported claims.",
                        recommended_action_ids=["show_approved_answers"],
                    ),
                    DemoFlowStep(
                        id="safe_actions",
                        page_id="flow",
                        objective="Show page-local actions and safety validation.",
                        talk_track="The agent adapts, but only through allowed actions on the current page.",
                        recommended_action_ids=["show_page_actions", "show_safety_gate"],
                    ),
                    DemoFlowStep(
                        id="prospect_room",
                        page_id="live_room",
                        objective="Preview cursor, voice, and event playback.",
                        talk_track="The prospect sees a live guided demo with cursor movement, highlights, and narration.",
                        recommended_action_ids=["show_agent_cursor"],
                    ),
                    DemoFlowStep(
                        id="qualified_output",
                        page_id="summary",
                        objective="Show the CRM-ready output after the demo.",
                        talk_track="The founder gets lead score, objections, buying signals, and follow-up.",
                        recommended_action_ids=["show_lead_score", "show_crm_summary"],
                    ),
                ],
            )
        ],
        knowledge=[
            KnowledgeRecord(
                id="input_model",
                topic="startup inputs",
                content="MVP input is product URL, sandbox credentials, target persona, demo goals, founder walkthrough, approved Q&A, CTA, and qualification questions.",
                tags=["inputs", "setup"],
            ),
            KnowledgeRecord(
                id="voice_strategy",
                topic="voice",
                content="Gemini Live can plug in as realtime voice, but it should call safe demo tools rather than directly controlling the browser.",
                tags=["voice", "gemini", "runtime"],
            ),
            KnowledgeRecord(
                id="safety_model",
                topic="safety",
                content="The agent is adaptive in goals and narration, but all UI actions are validated against page-local allowed actions.",
                tags=["actions", "safety"],
            ),
            KnowledgeRecord(
                id="cta",
                topic="cta",
                content="The desired next step is a setup call to connect the first product demo room.",
                tags=["cta", "sales"],
            ),
        ],
        qualification_questions=[
            "What product workflow would you want the agent to demo first?",
            "Who is the target buyer for that demo?",
            "Do you have a sandbox account or screenshots ready?",
        ],
        restricted_claims=[
            "Do not claim arbitrary production control.",
            "Do not promise unsupported security or compliance certifications.",
            "Do not say codebase access is required for MVP.",
        ],
    )


DEMO_MANIFEST = build_demeo_manifest()
