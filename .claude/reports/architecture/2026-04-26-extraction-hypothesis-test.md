# Extraction Hypothesis Test

## Date

2026-04-26

## Goal

Test how startup inputs should be converted into a `DemoManifest` that lets the
agent show the right page/action for prospect questions.

Tested target app:

```text
http://127.0.0.1:5175
```

Earlier manual routes crawled with Playwright MCP:

- `/onboarding`
- `/content`
- `/demo`
- `/crm`
- `/demo-room/live`

`/demo-room/live` was included because it is the newly created prototype surface
for Demeo's own AI demo-room experience. It was reached by direct URL, not by
following a production navigation link. This makes it useful for testing the
event-playback route, but it should not be counted as evidence that the
existing app naturally exposes that route in its current product navigation.

The later automated extraction test did **not** crawl `/demo-room/live`. It
started at `/` and followed discovered internal links only.

Screenshots captured:

- `extraction-onboarding.png`
- `extraction-content.png`
- `extraction-demo.png`
- `extraction-crm.png`
- `extraction-live-demo.png`

## Environment Limits

Earlier in the session, Python Playwright and outbound OpenAI calls were
blocked. After network and filesystem permissions changed, Chromium was
installed with `python -m playwright install chromium`, and the OpenAI-backed
extraction benchmark ran successfully.

## What Was Actually Tested Now

Completed:

- Link-based crawl from `/`, with no direct jump to `/demo-room/live`.
- Visible text, controls, selector hints, links, and screenshots were extracted.
- OpenAI generated manifests for:
  - `url_only`
  - `url_walkthrough`
  - `docs_only`
  - `screenshot_assisted`
- A separate OpenAI planner received each generated manifest and prospect
  questions, then returned event timelines.
- The scorer checked discovered page coverage, safe action count, invented
  pages/action refs, and question-to-event routing.

Still not completed:

- Credentialed crawling of a third-party app.
- Founder review UI for accepting/rejecting a generated manifest.
- Multi-start crawl from authenticated product states.

## Automated Crawl Result

The automated crawler discovered these routes from `/` through internal links:

- `/`
- `/onboarding`
- `/agents`
- `/dashboard`
- `/demo`
- `/crm`
- `/about`
- `/content`
- `/legal`

It did not discover `/demo-room/live`, which is correct because that route is
not linked from the main product navigation.

## What The Browser Crawl Showed

URL crawling is useful because it can see actual visible UI and controls.

Examples from the crawl:

- `/onboarding` exposed form fields for company name, description, industry,
  target audience, product/service description, website, stage, key features,
  differentiators, jurisdictions, and save buttons.
- `/content` exposed the content-agent page, prompt textarea, and `Generate
  Content` button.
- `/demo` exposed the prospect demo room, suggested questions, chat input, and
  CRM link.
- `/crm` exposed lead score, objections handled, next steps, follow-up email,
  and send/edit controls.

This confirms URL crawling can provide real selectors/control candidates.

## Benchmark Results

Success rule:

```text
MVP-usable means:
- at least 3/4 expected app areas discovered
- at least 6 safe/reviewable actions
- no invented manifest pages/action refs
- at least 3/4 prospect questions planned to the right page/action event
```

Results:

| Input condition | Pages discovered | Expected app areas | Actions | Planner score | MVP usable |
| --- | ---: | ---: | ---: | ---: | --- |
| URL only | 9 | 4/4 | 31 | 2/4 | No |
| URL + walkthrough + Q&A | 9 | 4/4 | 29 | 3/4 | Yes |
| Docs only | 9 crawl available, but manifest invented pages | 4/4 expected topics | 4 | 3/4 | No |
| URL + walkthrough + screenshots | 9 | 4/4 | 15 | 4/4 | Yes |

Important result: URL-only found the UI, but did not reliably infer the intended
demo story. Docs-only answered questions but invented pages and selectors. URL +
walkthrough/Q&A was usable. Adding screenshots improved the planner result.

## Hypothesis Comparison

### 1. URL + Sandbox Credentials + Walkthrough

Best MVP path.

Why:

- URL gives real pages, controls, labels, and selectors.
- Credentials unlock authenticated product surfaces.
- Walkthrough tells the system business intent and desired sequence.
- Together they can map "show setup" to specific pages/actions.

Weakness:

- Requires a safe sandbox account.
- Still needs founder review before the prospect-facing demo can run.

### 2. URL Only

Good for raw UI extraction, weak for intent.

Observed:

- The crawler could identify pages and controls.
- It can infer that `/onboarding` is setup, `/content` is content generation,
  `/demo` is the prospect room, and `/crm` is lead summary.

Weakness:

- It does not reliably know which workflow matters most.
- It may confuse navigation controls with product-specific demo actions.
- It may not know why a field/button matters to the buyer.

### 3. Docs Only

Good for answers, poor for UI actions.

Expected:

- Strong for approved Q&A, security, pricing, positioning, objections, and CTA.
- Weak for cursor movement and click/highlight targets because docs do not
  provide selectors or page state.

Use docs as the knowledge bank, not the interaction map.

### 4. Screenshots Only

Good for visual understanding, poor for reliable interaction.

Observed screenshots are useful for explaining layout and confirming page
purpose. But screenshots alone do not give reliable selectors or post-click
state.

Use screenshots as fallback/enrichment when the app cannot be crawled, or for
visual verification.

### 5. Codebase

Not tested per instruction.

Likely benefit:

- Better route/component semantics.

Likely downside:

- High trust and setup friction.
- Too slow for MVP onboarding.

## Best Setup

Use:

```text
URL + sandbox credentials + short founder walkthrough + approved Q&A
```

Add screenshots automatically during extraction. Add docs/security/pricing pages
when available.

Do not require codebase access.

## How Walkthrough Works With Extraction

The walkthrough is the intent layer.

Example founder walkthrough:

```text
Start on company setup, show product context, open content generation, then show
the prospect demo room and CRM summary.
```

Extraction maps this onto crawled UI:

```text
"company setup" -> /onboarding
"product context" -> company/product fields
"content generation" -> /content + Generate Content
"prospect demo room" -> /demo
"CRM summary" -> /crm
```

Without the walkthrough, URL crawling sees controls but may not know the best
story.

## Runtime Agent Test

`/api/v1/live-demo` now has an opt-in LLM planner:

```text
LIVE_DEMO_PLANNER=openai
LIVE_DEMO_PLANNER_MODEL=gpt-4.1-mini
```

The LLM receives:

- current page
- visible element IDs
- lead profile
- recent transcript
- full approved manifest
- knowledge bank
- restricted claims

The LLM returns a page, element IDs, narration, state, and lead-profile patch.
The backend validates page and element IDs against the manifest before creating
frontend events.

Smoke test results:

- "What does the founder need to provide?" -> `setup`, highlights
  `product-url`, `persona-card`, `walkthrough-card`.
- "Can this use Gemini realtime voice?" -> `live_room`, highlights
  `voice-control`.
- "How does it qualify the lead?" -> `summary`, highlights `lead-score` and
  `crm-summary`.

Focused backend tests still pass:

```text
cd backend && pytest tests/test_live_demo_api.py
5 passed
```

## Production Architecture Implication

Use two modes:

1. **Setup/extraction mode**
   - Playwright logs into a sandbox account.
   - Crawler extracts routes, DOM text, controls, screenshots.
   - LLM maps founder walkthrough/docs to page actions.
   - Founder approves the manifest.

2. **Prospect runtime mode**
   - Prospect opens a link.
   - React event playback uses approved manifest actions.
   - Voice agent calls safe tools like `show_page`, `highlight_element`,
     `move_cursor`, and `propose_click`.

Do not use live arbitrary browser automation as the default prospect runtime.

There are also two product deployment options:

1. **Embedded sandbox / demo copy**
   - The founder gives a safe staging/demo account or we recreate the important
     screens.
   - The prospect runtime uses the approved manifest and event playback.
   - This is the recommended MVP because it is reliable and safe.

2. **Live website/app control**
   - The prospect room embeds or opens the startup's real app/site and controls
     it through approved selectors, routes, and tool calls.
   - This is more realistic, but brittle: auth, layout changes, destructive
     buttons, latency, and cross-origin restrictions make it harder to guarantee.
   - It should be a later capability, not the default first runtime.

## Next Verification Steps

1. Add a founder review UI for generated manifests.
2. Convert the extraction harness into backend setup endpoints.
3. Add credentialed crawling for safe sandbox/staging accounts.
4. Store generated screenshots and selector snapshots as extraction artifacts.
5. Add multi-event runtime planning to the production API response shape, not
   only the extraction evaluator.
6. Add Gemini Live / LiveKit so voice calls the same safe demo tools as text.

## Voice / LiveKit Note

LiveKit is a reasonable layer for realtime voice rooms. LiveKit Agents can join
rooms as realtime participants, and LiveKit has a Gemini Live plugin for low
latency voice conversations. Gemini Live should call approved demo tools; it
should not directly control arbitrary DOM.

Recommended voice shape:

```text
LiveKit room
  prospect audio/video participant
  AI agent participant using Gemini Live
  web app participant rendering demo events
```

The voice tool calls still go through the same manifest safety gate.
