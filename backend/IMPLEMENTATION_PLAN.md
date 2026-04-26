# AI GTM Demo Rooms Implementation Plan

## Product Direction

Build an AI GTM office for technical B2B founders. The first workflow turns cold outreach into personalized AI demo rooms that qualify prospects automatically.

The hackathon MVP should prove one complete loop:

1. A founder enters their product and a target prospect.
2. The system understands the product and creates an ICP.
3. The system researches or structures the prospect context.
4. The system writes personalized outreach.
5. The prospect opens a personalized AI demo room.
6. The demo agent answers questions in that prospect's context.
7. The system produces a lead score, CRM-style summary, objections, next steps, and follow-up email.

The main pitch is not "we built many agents." The pitch is:

> We turn cold outreach into instant personalized AI demo rooms, so technical founders can qualify prospects without a sales team.

## Current Product Understanding: AI-Led Product Demo Rooms

The product is not a generic browser automation agent and not primarily a
debugging demo for a fictional app. The product is an AI demo-room builder for
founders.

The founder should be able to provide product context, approved knowledge, and
a small set of demo pages or workflows. A prospect then enters a live AI demo
room where the agent:

1. Converses naturally with the prospect.
2. Shows the actual demo pages.
3. Moves a visible agent cursor over the page.
4. Highlights relevant UI.
5. Clicks or navigates only through page-local allowed actions.
6. Uses an overall product knowledge bank for answers and flow selection.
7. Records transcript, actions, objections, buying signals, and qualification.

The near-term prototype should therefore prioritize the visible demo experience:

```text
prospect message
  -> demo agent decides intent
  -> current page context exposes only local actions
  -> global demo knowledge can reveal/navigate to another flow
  -> frontend plays cursor/highlight/click/navigate events
  -> assistant narrates what changed and why it matters
```

Each page should carry page-local knowledge:

- what this page is showing
- what the agent is allowed to do on this page
- what selectors correspond to those actions
- what narration or objections are relevant here
- where each action can lead next

The agent should also have global knowledge:

- product description and positioning
- ICP and prospect context
- demo flows and route graph
- security/pricing/integration notes
- approved objection handling
- CTA and qualification rubric

This is simpler than a heavy upfront extractor architecture. Extractors can
come later to compile a founder's docs/pages into the same page/action
knowledge format, but the product experience should first be proven with a
direct visible browser demo.

## Browser Automation Direction

The first implementation added a bounded TracePilot -> Render demo controller.
That proved session state, action logs, route allowlisting, verification, and
qualification continuity, but it overfit to a fictional debugging scenario.

The corrected architecture should pivot to:

```text
DemoManifest
  globalKnowledge
  flows
  pages[]
    route
    pageKnowledge
    allowedActions[]
      selector
      event animation
      result route/page
```

The frontend should render the demo page and an agent cursor overlay. The
backend should return a sequence of visual events:

```json
[
  { "type": "say", "text": "Let me show how setup works." },
  { "type": "navigate", "route": "/sandbox/demeo/setup" },
  { "type": "cursor_move", "selector": "[data-demo-id='connect-docs']" },
  { "type": "highlight", "selector": "[data-demo-id='connect-docs']" },
  { "type": "click", "selector": "[data-demo-id='connect-docs']" }
]
```

Stagehand may help later as an optional discovery layer for real arbitrary
websites. It should not be the core product dependency for the first prototype.
The product needs deterministic, founder-approved demo behavior more than
open-ended AI clicking. Stagehand-style observe/act maps well to the page-local
action model, but raw Stagehand execution could make the product feel less
controlled unless its outputs are cached, reviewed, and converted into the
same bounded action format.

## Current Repo State

The backend has a focused GTM agent architecture:

- FastAPI app under `backend/app`
- `GET /` and `GET /api/v1/health`
- LangGraph campaign, demo chat, and qualification graphs
- reusable agent capabilities under `backend/app/agents/capabilities`
- mock LLM provider
- OpenAI provider boundary with mock fallback
- backend tests

The old generic `/tasks` starter route and content/review agents were removed to keep the backend focused on the AI GTM workflow.

Current important files:

- `backend/app/main.py`
- `backend/app/api/routes/campaigns.py`
- `backend/app/agents/campaign_models.py`
- `backend/app/agents/graphs/campaign.py`
- `backend/app/agents/graphs/demo.py`
- `backend/app/agents/capabilities/*.py`
- `backend/app/agents/llm.py`

## Architecture Decision

Use LangGraph as the agent orchestration runtime.

The long-term architecture should be a stateful graph, not a flat FastAPI service that manually calls helper functions. The existing FastAPI app remains the API layer, but campaign creation, demo chat, and qualification should run through compiled LangGraph graphs.

LangGraph is the right fit because this product needs:

- explicit orchestration across multiple GTM agents
- typed state shared across steps
- conditional routing from an orchestrator
- durable execution and checkpointing later
- streaming step updates for the founder cockpit later
- inspectable traces through LangSmith/Studio later

Visible product agents:

- Orchestrator Agent: owns graph routing, state transitions, and workflow completion.
- Strategist Agent: understands product, ICP, value props, objections, and demo narrative.
- Research Agent: structures prospect context and likely pains.
- Outreach Agent: writes personalized outreach with the demo-room link.
- Demo Agent: runs the personalized conversation using the product strategy and prospect context.
- Sales Ops Agent: creates qualification, CRM notes, objections, next steps, and follow-up.

Implementation should keep reusable AI capabilities separate from graph orchestration. A capability can be a single LangGraph node today, or grow into multiple nodes/subgraphs later.

Current modular target:

```text
app/agents/capabilities/
  strategist.py
  research.py
  demo_brief.py
  demo_plan.py
  outreach.py
  readiness.py
  demo.py
  sales_ops.py

app/agents/graphs/
  campaign.py
  demo.py
```

Graph files compose capabilities into workflows. Capability files own reusable AI behavior.

Implementation should start as one LangGraph `StateGraph` for campaign creation, then add a second graph or subgraph for demo-room chat and qualification.

Initial campaign graph:

```text
START
  -> orchestrator
  -> strategist
  -> research
  -> demo_brief
  -> demo_plan
  -> outreach
  -> readiness
  -> persist_demo_room
  -> END
```

Initial demo-room graph:

```text
START
  -> load_demo_room
  -> demo_agent
  -> update_transcript
  -> END
```

Initial qualification graph:

```text
START
  -> load_transcript
  -> sales_ops
  -> persist_qualification
  -> END
```

Do not build "fake agents" that are only labels in a response. Each core agent should be a graph node with testable inputs, outputs, and state updates.

## First Implementation Milestone

Create a tested LangGraph campaign workflow.

Add dependencies:

```text
langgraph
langchain-openai
```

Keep mock mode available, but add a real OpenAI-backed provider using the root `.env` `OPENAI_API_KEY`. Do not print or log the key.

Add a new endpoint:

```text
POST /api/v1/campaigns
```

Input:

```json
{
  "product_name": "string",
  "product_description": "string",
  "product_url": "string | null",
  "target_audience": "string | null",
  "prospect_company": "string",
  "prospect_description": "string | null",
  "prospect_url": "string | null"
}
```

Output:

```json
{
  "campaign_id": "string",
  "product_profile": {},
  "icp": {},
  "prospect_profile": {},
  "demo_brief": {},
  "outreach_message": {},
  "demo_room": {},
  "readiness_score": {},
  "workflow_steps": []
}
```

Use in-memory storage for the first version. Persistence can wait until the graph works.

The endpoint must invoke the compiled LangGraph campaign graph. It should not manually call the agent steps in route code.

## Pydantic Models To Add

Add structured models in `backend/app/agents/models.py` or split into a dedicated campaign schema module if the file becomes too large.

Required models:

- `CampaignCreateRequest`
- `CampaignResponse`
- `ProductProfile`
- `ICPProfile`
- `ProspectProfile`
- `DemoBrief`
- `OutreachMessage`
- `DemoRoom`
- `ReadinessScore`
- `WorkflowStep`
- `ChatRequest`
- `ChatResponse`
- `QualificationReport`
- `FollowUpEmail`
- `CampaignGraphState`
- `DemoChatGraphState`
- `QualificationGraphState`

Keep fields practical and demo-friendly. Do not over-model CRM systems or external integrations yet.

## Backend Build Order

1. Fix test ergonomics so `pytest` works from `backend/` without needing `PYTHONPATH=.`.
2. Add LangGraph and OpenAI integration dependencies.
3. Add campaign Pydantic models and graph state models.
4. Build `campaign_graph` with testable nodes:
   - orchestrator
   - strategist
   - research
   - demo brief
   - outreach
   - readiness
   - persist demo room
5. Add `backend/app/api/routes/campaigns.py`.
6. Register the campaigns router in `backend/app/main.py`.
7. Add in-memory storage for campaigns and demo rooms.
8. Add tests for graph nodes and `POST /api/v1/campaigns`.
9. Add demo-room retrieval:

   ```text
   GET /api/v1/demo-rooms/{demo_room_id}
   ```

10. Add `demo_chat_graph`:

   ```text
   POST /api/v1/demo-rooms/{demo_room_id}/chat
   ```

11. Add `qualification_graph`:

   ```text
   POST /api/v1/demo-rooms/{demo_room_id}/qualify
   ```

12. Add tests for demo-room retrieval, chat, and qualification.

## LLM Strategy

Keep the existing `MockLLMProvider` for deterministic tests and demo fallback.

Add an OpenAI-backed provider for real agent behavior. The root `.env` has `OPENAI_API_KEY`; read it through settings, never print it, and keep mock mode selectable.

Mock mode should generate strong, realistic demo outputs from the request fields. This protects the live hackathon demo from API failures.

The provider interface should support:

- product strategy generation
- prospect profile generation
- outreach generation
- demo chat response
- qualification generation

Test policy:

- unit tests use mock provider only
- one optional smoke test or script can use OpenAI if `OPENAI_API_KEY` is present
- API tests should not require network access

## Demo Agent Behavior

The Demo Agent should not invent the sales narrative from scratch.

It should use:

- product profile from the Strategist step
- ICP from the Strategist step
- prospect profile from the Research step
- demo brief
- previous chat messages

The demo room should feel personalized, not like a generic chatbot. It should include:

- personalized headline
- why this product is relevant to the prospect
- suggested questions
- chat interface
- CTA such as "Send me summary" or "Book founder call"

## Sales Ops Output

After a demo-room conversation, generate:

- lead score from 0 to 100
- qualification status
- pain points
- objections
- urgency
- buying signals
- recommended next step
- CRM note
- follow-up email

This can initially be generated from the stored transcript using mock logic.

## Frontend Plan

Once the backend flow works, build two frontend surfaces:

1. Founder Cockpit
   - product and prospect input
   - generated ICP
   - prospect brief
   - outreach message
   - demo room link
   - lead qualification result

2. Prospect Demo Room
   - personalized header
   - relevance summary
   - suggested questions
   - chat with Demo Agent
   - CTA

Do not build a landing page first. The first screen should be the usable founder workflow.

## Testing Plan

Backend tests should cover:

- plain `pytest` works from `backend/`
- health route still works
- no legacy `/api/v1/tasks` route is required
- campaign graph invokes each required node in order
- campaign graph returns valid structured Pydantic outputs
- campaign creation returns all required structured sections
- campaign creation returns a demo room ID
- demo room retrieval works by ID
- demo chat graph loads room state and writes transcript state
- chat endpoint returns contextual response and appends transcript messages
- qualification graph reads transcript and writes sales ops output
- qualification endpoint returns lead score, CRM note, objections, next step, and follow-up email
- missing required campaign fields return validation errors

Run tests from the backend directory:

```bash
pytest
```

## Suggested First PR

The first PR should be backend-only and should include:

- pytest config/import path fix
- LangGraph dependency
- campaign models
- campaign graph with mock and OpenAI-capable provider boundary
- `/api/v1/campaigns`
- `/api/v1/demo-rooms/{demo_room_id}`
- tests for graph node execution, campaign creation, and demo-room retrieval
- README update with example requests

Do not include frontend, real web research, auth, billing, or CRM integrations in the first PR.

## Later Enhancements

Add only after the core loop works:

- real LLM provider
- URL ingestion for product/prospect pages
- generated unique public demo-room links
- SQLite persistence
- Logfire or tracing dashboard
- CSV prospect import
- campaign learning snapshot
- CRM export

## Key Implementation Principle

Build one impressive path end to end before expanding the agent system.

The hackathon demo should show:

```text
product + prospect input
  -> personalized outreach
  -> personalized demo room
  -> prospect chat
  -> qualified lead summary and follow-up
```

Everything else is secondary.
