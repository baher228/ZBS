# Startup Input and Runtime Agent Architecture

## Date

2026-04-25

## Product Definition

The product is for founders who want to create AI-led demo rooms for their
startup.

The founder provides product context, demo pages, workflows, and approved
answers. The prospect enters a demo room where the Demo Agent talks, shows the
product, moves a visible cursor, highlights UI, clicks approved controls,
answers questions, and qualifies the lead.

## MVP Startup Input

Do not require codebase access for the MVP. It creates trust friction and is
not necessary for a convincing demo room.

Required MVP inputs:

- Product/app URL or staging URL
- Sandbox credentials if the product is behind login
- Target customer/persona
- 1-3 demo goals
- Founder-written walkthrough in plain English
- 5-10 approved Q&A answers for sensitive/common questions
- CTA and qualification questions

Concise meaning of each required input:

- **Product/app URL or staging URL:** The product surface the agent will show.
  Prefer staging/sandbox over production.
- **Sandbox credentials:** A safe demo login with fake data, used when the app
  is behind authentication.
- **Target customer/persona:** Who the demo is for. This shapes examples,
  phrasing, objections, and qualification.
- **1-3 demo goals:** What the demo should prove, such as setup speed,
  workflow automation, ROI, or integration depth.
- **Founder-written walkthrough:** Plain-English steps for the ideal demo path.
  This is the seed before automated extraction improves it.
- **Approved Q&A:** Founder-approved answers for common/sensitive topics like
  pricing, security, roadmap, integrations, and claims.
- **CTA:** The desired next step after the demo, such as booking a call,
  starting a trial, or joining a pilot.
- **Qualification questions:** Questions the agent should naturally collect to
  score the lead, such as team size, current tool, urgency, and budget.

Strongly recommended:

- Screenshots of key pages as fallback
- Docs/help center links
- Pricing page
- Security/integration notes
- Short Loom or existing demo video

Optional later:

- Codebase
- Figma/design files
- API docs
- sales call transcripts
- pitch deck
- product analytics/session recordings

## Extraction Pipeline

Normalize all founder inputs into four artifacts:

1. Page knowledge
2. Action inventory
3. Demo flow graph
4. Approved answer bank

Pipeline:

```text
URL/app access
  -> crawl pages
  -> DOM snapshot + screenshot + visible text + controls
  -> page knowledge extraction
  -> action inventory extraction
  -> draft demo flow graph
  -> founder review/approval
  -> runtime demo manifest
```

Screenshots and videos should enrich the flow, not be the primary source of
truth when live app access is available.

Use deterministic extraction first:

- headings, buttons, links, forms, tabs from DOM
- screenshots and coordinates from browser automation
- OCR only when DOM is unavailable
- LLM for summarizing page purpose and mapping controls to business concepts

## Runtime Demo Manifest

The runtime should use a reviewed manifest, not arbitrary browser control.

```ts
type DemoManifest = {
  startupId: string;
  productName: string;
  globalKnowledge: KnowledgeBank;
  pages: DemoPageManifest[];
  flows: DemoFlow[];
  qualificationRules: QualificationRule[];
  restrictedClaims: RestrictedClaim[];
};
```

Each page exposes only local knowledge and local actions:

```ts
type DemoPageManifest = {
  pageId: string;
  route: string;
  title: string;
  summary: string;
  visibleConcepts: string[];
  elements: DemoElement[];
  allowedActions: PageAction[];
};
```

Actions use stable element IDs/selectors:

```ts
type DemoElement = {
  id: string;
  label: string;
  role: "button" | "link" | "tab" | "input" | "card" | "chart" | "section";
  description: string;
  selector: string;
  safeToClick: boolean;
  requiresApproval: boolean;
  destructive: boolean;
};
```

## Runtime Agent Loop

The agent should feel adaptive, but act through approved actions.

```text
observe current session/page
  -> interpret prospect intent
  -> retrieve from global knowledge and current page manifest
  -> choose goal
  -> propose answer/action/events
  -> safety validate
  -> emit visual event timeline
  -> update transcript, lead profile, and session state
```

Agentic behavior comes from:

- intent detection
- goal stack
- current-page awareness
- retrieval from approved knowledge
- nonlinear flow selection
- memory of what the prospect said
- lead qualification updates

It should not come from unrestricted clicking.

## Event Timeline Contract

The backend should return structured visual events. The frontend owns playback.

```ts
type DemoEvent =
  | { type: "say"; text: string; audioUrl?: string; durationMs?: number }
  | { type: "navigate"; pageId: string; route: string }
  | { type: "cursor.move"; elementId: string; durationMs: number }
  | { type: "cursor.click"; elementId: string }
  | { type: "highlight.show"; elementId: string; label?: string }
  | { type: "highlight.hide"; elementId?: string }
  | { type: "wait"; durationMs: number }
  | { type: "lead.profile.updated"; patch: Record<string, unknown> };
```

Frontend components:

- `DemoEventRunner`
- `DemoCursorLayer`
- `HighlightLayer`
- `TargetRegistry`
- `NarrationPlayer`
- `VoiceInputButton`
- `DemoChatPanel`
- `ActionLogPanel`

## Voice Plan

The final product should support realtime voice. Gemini Live is a strong
candidate because it supports low-latency bidirectional audio, voice activity
detection, interruption handling, transcription, and function calling over
WebSockets.

Implementation should still keep the demo-agent event loop separate from the
voice transport. Voice is how the prospect talks to the agent; the event
timeline is how the agent controls the visible demo.

Push-to-talk fallback:

```text
record audio in browser
  -> backend transcription
  -> agent returns event timeline
  -> optional TTS per `say` segment
  -> frontend plays narration and cursor/highlight events
```

Gemini Live path:

```text
Gemini Live WebSocket session
  -> live mic audio/text into model
  -> model calls approved demo tools
  -> backend validates tool call
  -> frontend receives visual events
  -> Gemini streams spoken response
```

Gemini Live should not directly control the browser. It should call tools like
`show_page`, `highlight_element`, `move_cursor`, `propose_click`, and
`answer_from_knowledge`. The backend remains the safety gate.

Use Gemini Live early if the demo needs the voice wow factor. Keep a text or
push-to-talk fallback because realtime voice adds WebSocket session management,
audio format handling, interruption behavior, and synchronization complexity.

## Stagehand Position

Stagehand can help later as an optional extraction/discovery layer:

```text
Stagehand observe page
  -> suggested actions/selectors
  -> founder review
  -> cached approved manifest
```

It should not be the core runtime executor in the MVP. Runtime should use
approved page actions so demos are reliable, reviewable, and safe.

## Recommended MVP Build Order

1. Define `DemoManifest`, `KnowledgeBank`, `DemoPageManifest`, `PageAction`,
   and `DemoEvent`.
2. Build a founder setup screen that accepts URL, persona, walkthrough,
   approved Q&A, and CTA.
3. Build a manual manifest for this product's own demo first.
4. Build `/demo-room/live` with chat, demo surface, cursor overlay, highlights,
   and action log.
5. Implement text runtime agent that returns event timelines.
6. Add page navigation and highlights.
7. Add cosmetic cursor movement.
8. Add approval-gated clicks.
9. Add qualification summary.
10. Add push-to-talk voice and TTS.
11. Add URL crawler/extractor to draft page manifests.
12. Add founder review/approval for extracted actions and answers.

## Current Code Reality

The existing TracePilot implementation contains a thin deterministic planner
inside `BrowserDemoGraphRunner`. It is technically an orchestration layer, but
it is not the intended agentic product experience because:

- it is hardcoded to one fictional scenario
- it has no visible cursor playback
- it does not use LLM planning yet
- it does not expose founder setup
- it does not compile startup inputs into a manifest

Keep the useful pieces:

- session state
- action logs
- bounded action validation
- verification logs
- transcript and qualification continuity

Replace the scenario-specific layer with the product demo-room manifest and
event timeline architecture above.

## Implemented Live Event Loop

Added a first working live demo-room slice:

- Backend manifest/runtime under `backend/app/live_demo/`
- API routes in `backend/app/api/routes/live_demo.py`
- Frontend route `frontend/src/routes/demo-room.live.tsx`
- API client additions in `frontend/src/lib/agentApi.ts`

Available endpoint shape:

```text
GET  /api/v1/live-demo/manifest
POST /api/v1/live-demo/sessions
GET  /api/v1/live-demo/sessions/{session_id}
POST /api/v1/live-demo/sessions/{session_id}/message
```

The frontend at `/demo-room/live` now:

- creates a live demo session
- sends page-aware prospect messages to the backend
- receives one decision object containing `reply`, `events`, and updated
  session state
- plays `navigate`, `cursor.move`, `highlight.show`, `highlight.hide`, `wait`,
  and `lead.profile.updated` events
- renders a visible synthetic agent cursor
- renders highlighted UI targets using `data-demo-id`
- logs the event stream
- updates lead score/interest state

Manual smoke test:

```text
Backend: http://127.0.0.1:8000
Frontend: http://127.0.0.1:5175/demo-room/live

Prompt: "What does the founder need to provide?"
Result: Agent explains required inputs, highlights setup page targets, logs
cursor/highlight/lead events.

Prompt: "Can this use Gemini realtime voice?"
Result: Agent navigates to Prospect room, highlights voice/event-stream
concepts, and explains Gemini Live as a voice layer over safe demo tools.
```

Validation:

```text
backend pytest: 112 passed
frontend focused eslint: clean for demo-room.live.tsx and agentApi.ts
frontend build: completed; Wrangler emitted a log-write EPERM warning for
~/Library/Preferences but generated client/server assets successfully.
```

Important clarification:

- The current live runtime does **not** call an LLM yet.
- It uses deterministic intent matching over a manual manifest.
- This proves the UI/event contract, but not final agent reasoning.

The intended LLM context for the next runtime version:

```text
system: demo-agent policy and action rules
global knowledge: product facts, approved Q&A, CTA, qualification rubric
flow graph: allowed demo paths and goals
current session: transcript, lead profile, current page, active goal
current page manifest: visible concepts, elements, allowed local actions
frontend telemetry: visible element IDs and current route
user message: latest prospect question
```

The LLM should return a typed decision:

```json
{
  "reply": "natural language answer",
  "goal": "demonstrate_feature | answer_question | qualify_lead",
  "target_page_id": "flow",
  "events": [
    { "type": "navigate", "page_id": "flow" },
    { "type": "cursor.move", "element_id": "page-actions" },
    { "type": "highlight.show", "element_id": "page-actions" }
  ],
  "lead_patch": { "interested_features": ["safe guided actions"] }
}
```

The backend validates the typed decision against the manifest before the
frontend plays it.

## Extraction Hypotheses To Test

Before committing to one onboarding mode, test several input strategies against
the same target app and score the generated manifest quality.

Hypotheses:

1. **URL + credentials + founder walkthrough** is the best MVP setup.
2. **Docs-only** is good for answers but weak for knowing where to click.
3. **Screenshots-only** is good for visual explanation but weak for reliable
   selectors and real interactions.
4. **URL-only** can discover controls, but often lacks business intent.
5. **Codebase ingestion** can improve semantics, but is too high-friction for
   first-run onboarding.

Recommended test harness:

```text
input bundle
  -> extractor creates draft DemoManifest
  -> evaluator scores:
       page coverage
       selector validity
       action safety
       flow correctness
       answer accuracy
       founder effort
       time to usable demo
```

Use Playwright first for extraction:

- login with sandbox credentials
- crawl founder-approved routes
- collect DOM text, headings, links, buttons, forms, roles, and screenshots
- validate selectors by resolving them in the browser
- optionally run candidate flows in a sandbox account

Use LLM summarization for:

- page purpose
- element business meaning
- matching founder walkthrough steps to UI controls
- drafting talk tracks and Q&A

Use Stagehand optionally for:

- discovering actions when deterministic DOM extraction is insufficient
- exploring unfamiliar pages
- suggesting selectors/actions for founder review

Do not use Stagehand as the live prospect runtime until actions are reviewed
and cached into the manifest.
