# AI Demo-Room Understanding and Current State

## Date

2026-04-25

## What Was Built

The previous implementation added a bounded browser-demo prototype around a
fictional scenario:

```text
TracePilot selling to Render
Flow: dashboard -> trace timeline -> failed tool call -> state diff -> alerts
```

Backend additions:

- `backend/app/demo_controller/models.py`
- `backend/app/demo_controller/store.py`
- `backend/app/demo_controller/actions.py`
- `backend/app/demo_controller/playwright_controller.py`
- `backend/app/agents/graphs/browser_demo.py`
- `backend/app/api/routes/demo_sessions.py`
- tests in `backend/tests/test_demo_sessions_api.py`

Frontend additions:

- `frontend/src/components/sandbox/TracePilotSandbox.tsx`
- `/sandbox/tracepilot/render`
- `/sandbox/tracepilot/render/traces`
- `/sandbox/tracepilot/render/tool-call`
- `/sandbox/tracepilot/render/state-diff`
- `/sandbox/tracepilot/render/alerts`

The implementation proves:

- demo session state
- allowlisted routes/selectors
- action logs
- deterministic scripted demo planning
- transcript capture
- verification logs
- qualification continuity after browser-guided chat

It does not yet prove the intended visible AI demo-room experience.

## Product Understanding Correction

The product should be an AI demo-room builder for founders, not a generic
browser automation system and not a TracePilot debugging product.

The intended experience:

1. A founder provides product context, approved knowledge, and demo pages or
   workflows.
2. A prospect enters a personalized demo room.
3. The Demo Agent talks to the prospect.
4. The app visibly shows the relevant demo page.
5. An agent cursor moves over the page, highlights UI, and clicks approved
   controls.
6. The agent answers from a global knowledge bank and page-local knowledge.
7. The system records transcript, actions, buying signals, objections, and
   qualification.

## Better Architecture

Use a global knowledge bank plus current-page action context.

Global knowledge:

- product positioning
- target customer and prospect context
- demo flow graph
- pricing/security/integration notes
- approved objection handling
- qualification rubric and CTA

Current-page context:

- page id and route
- page-specific talk track
- visible UI targets
- allowed local actions
- selectors for each action
- result page/action after each interaction

The agent should only see or execute actions available on the current page,
plus global navigation/flow knowledge. If the user asks for a different topic,
the global flow graph can reveal the next page context.

## Recommended Next Build

Replace the TracePilot-first experience with a direct visible demo of this
product:

```text
/demo-room/live
  left/center: sandbox product pages
  overlay: animated agent cursor and highlights
  right: Demo Agent chat, current step, action log
```

Backend returns visual events:

```json
[
  { "type": "say", "text": "Let me show how setup works." },
  { "type": "navigate", "route": "/sandbox/demeo/setup" },
  { "type": "cursor_move", "selector": "[data-demo-id='connect-docs']" },
  { "type": "highlight", "selector": "[data-demo-id='connect-docs']" },
  { "type": "click", "selector": "[data-demo-id='connect-docs']" }
]
```

Frontend plays those events visually.

## Stagehand Position

Stagehand can help later as an optional discovery layer for arbitrary external
websites. Its `observe()` / `act()` model is conceptually aligned with
page-local actions.

For this product's first prototype, Stagehand could make the experience worse
if it becomes the primary click executor, because founders need predictable,
approved demo behavior. It is better to make the core product deterministic:

```text
approved page actions -> typed visual events -> cursor/highlight/click playback
```

Then later:

```text
Stagehand observe -> suggested actions -> founder review/cache -> approved manifest
```

## Open Questions

- Should the first visible demo show this product configuring itself, or a
  founder configuring a sample startup?
- Should demo pages be iframe-rendered routes, internal React components, or
  uploaded screenshots with hotspots for the MVP?
- Should the agent cursor execute real clicks immediately, or should the
  frontend animate clicks while backend state changes route/page?
