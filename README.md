# Demeo

Demeo is an AI demo-room builder for technical B2B founders. A founder provides a product URL, a short walkthrough, approved answers, qualification goals, and safe demo context. Demeo turns that into a shareable buyer demo room with an AI guide inside it.

The demo guide can chat, speak through Gemini Live, move a visible agent cursor, highlight product UI, answer buyer questions, qualify the lead, and prepare follow-up for the founder.

## Current Demo

Run the backend and frontend, then open:

```text
http://127.0.0.1:5175/demo-room/live
```

From the landing page:

```text
http://127.0.0.1:5175/
```

Select `Demo Agent`, then click `Open Live Self-Demo`.

Try:

```text
Walk me through the app setup.
Show me what the agent demo room does.
What does the founder receive after the demo?
How does the agent know what it can click?
```

The full walkthrough follows the approved generated manifest flow:

```text
/onboarding -> /dashboard -> /agents -> /demo -> /crm
```

## Product Idea

Demeo is not just a demo agent. Demeo is the platform that creates demo rooms. The demo agent is one capability inside the created room.

Founder setup:

```text
product URL or staging URL
sandbox credentials if needed
target buyer/persona
demo goals
short founder walkthrough
approved Q&A
CTA
qualification questions
```

Prospect experience:

```text
open shared link
AI guide introduces the product
AI guide walks through the product UI
prospect asks questions by text or voice
agent navigates/highlights relevant areas
agent records objections, interest, urgency, and fit
founder receives CRM summary and follow-up draft
```

## How The Manifest Works

The manifest is the approved operating map for the AI demo guide.

It contains:

- product description and target persona
- approved knowledge and restricted claims
- pages the agent can show
- visible elements on each page
- safe page-local actions
- demo flows and step talk tracks
- CTA and qualification questions

The runtime does not let the model invent arbitrary pages, selectors, or actions. The LLM chooses from the manifest, and the backend validates the choice before the frontend plays any visual event.

Runtime shape:

```text
prospect message
-> observe current page/session state
-> use current-page actions + compact global product context
-> retrieve relevant flow/page/knowledge context when needed
-> LLM chooses answer, page, action IDs, or approved flow
-> backend validates against manifest
-> frontend plays navigation, cursor, highlight, narration, lead updates
```

For broad tour requests such as `walk me through`, `show me around`, or `full demo`, the approved generated flow wins before the LLM can collapse the request into a single-page answer. Specific questions still go through the planner so the agent can route to the relevant page.

## Founder Walkthrough

The founder walkthrough is a short human-written story of what the demo should show and why. It is not a word-for-word script.

Example:

```text
Start by showing how the founder enters company and product context.
Then show the prospect demo room where a buyer can ask questions.
Finally show the CRM summary and follow-up output that qualifies the lead.
```

URL crawling tells Demeo what exists in the product UI. The founder walkthrough tells Demeo what matters commercially. Approved Q&A tells Demeo what it is allowed to claim.

Together they produce:

```text
pages
elements
safe actions
demo flows
talk tracks
approved answers
restricted claims
```

## Voice And Interruption

Voice is handled through Gemini Live over a backend WebSocket.

Flow:

```text
browser mic audio
-> backend WebSocket
-> Gemini Live
-> Gemini calls safe demo tools
-> backend returns validated visual event timeline
-> frontend plays cursor/highlights/narration/audio
```

The voice agent does not directly click the page. It calls high-level tools such as:

```text
start_demo_flow
show_relevant_page
answer_with_visuals
pause_demo_flow
continue_demo_flow
get_demo_context
```

Interruption is supported by pausing the active flow. The backend keeps the current flow ID, step index, and step token. After answering an interrupting question, the user can resume and the agent continues from the stored checkpoint instead of restarting the whole tour.

## Architecture

```text
frontend/
  React + TanStack Router + Vite UI
  landing page, app routes, live demo room, cursor/highlight playback

backend/
  FastAPI API
  agent orchestration
  company/context storage
  generated demo manifest runtime
  Gemini Live voice bridge
  extraction benchmark harness
```

Important backend areas:

```text
backend/app/live_demo/
  models.py               manifest/session/event models
  extracted_manifest.py   converts extraction reports into runtime manifest
  runtime.py              text planner + validated visual events
  setup_store.py          approved setup/manifest store
  voice_bridge.py         Gemini Live WebSocket bridge

backend/tools/
  evaluate_demo_extraction.py
  extraction_reports/
  extraction_artifacts/

backend/app/demo_controller/
  bounded Playwright-style browser control prototype
```

Important frontend areas:

```text
frontend/src/routes/index.tsx              landing page
frontend/src/components/AgentsShowcase.tsx landing page agent cards
frontend/src/routes/agents.tsx             agent lab
frontend/src/routes/demo-room.live.tsx     live AI-guided demo room
frontend/src/lib/agentApi.ts               API client/types
frontend/src/components/CustomCursor.tsx   app cursor, disabled in demo room/embed
```

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example ../.env
python main.py
```

The backend runs on:

```text
http://127.0.0.1:8000
```

`backend/main.py` starts `uvicorn` using values from the environment:

```env
APP_HOST=127.0.0.1
APP_PORT=8000
APP_DEBUG=true
```

### Frontend

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5175
```

The frontend runs on:

```text
http://127.0.0.1:5175
```

If the API runs somewhere else:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Environment

Root `.env` and `backend/.env` are both supported.

Common variables:

```env
APP_ENV=development
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

LLM_PROVIDER=mock
LLM_MODEL=mock-gtm-v1
OPENAI_API_KEY=
LLM_API_KEY=
PYDANTIC_AI_GATEWAY_API_KEY=

GEMINI_API_KEY=
GEMINI_LIVE_MODEL=gemini-3.1-flash-live-preview
GEMINI_LIVE_VOICE=Zephyr
GEMINI_LIVE_ENABLED=true

FAL_API_KEY=
MUBIT_ENABLED=true
MUBIT_API_KEY=
MUBIT_AGENT_ID=zbs-agent
```

For deterministic local tests, keep `LLM_PROVIDER=mock`. For the live demo planner and extraction, provide an OpenAI key. For voice, provide `GEMINI_API_KEY`.

Do not commit real `.env` values.

## Extraction Pipeline

The current live demo uses a cached generated extraction report at:

```text
backend/tools/extraction_reports/summary.json
```

To rerun extraction against the local app:

```bash
cd backend
OPENAI_EXTRACTION_MODEL=gpt-5.4-mini \
OPENAI_PLANNER_MODEL=gpt-5.4-mini \
OPENAI_EXTRACTION_TIMEOUT=120 \
python tools/evaluate_demo_extraction.py \
  --base-url http://127.0.0.1:5175 \
  --conditions url_only url_walkthrough docs_only screenshot_assisted \
  --planner-models gpt-5.4-mini
```

The evaluator:

```text
crawls discoverable internal links from /
captures screenshots when requested
passes URL/docs/walkthrough/screenshot inputs to the LLM
generates a candidate manifest
benchmarks planner decisions against expected product questions
writes reports and screenshots under backend/tools/
```

Production setup should turn this script into setup APIs:

```text
founder submits URL + walkthrough + Q&A
backend crawls/screenshots
LLM drafts manifest
founder reviews/approves manifest
prospect demo room uses approved manifest
```

## Main API Routes

Health and product agents:

```text
GET  /api/v1/health
GET  /api/v1/health/provider
POST /api/v1/company
GET  /api/v1/company
POST /api/v1/tasks
POST /api/v1/content/chat
POST /api/v1/marketing-research/chat
POST /api/v1/legal/chat
POST /api/v1/campaigns
GET  /api/v1/demo-rooms/{id}
POST /api/v1/demo-rooms/{id}/chat
POST /api/v1/demo-rooms/{id}/qualify
```

Live manifest demo:

```text
POST /api/v1/live-demo/setups
GET  /api/v1/live-demo/setups/{startup_id}
POST /api/v1/live-demo/setups/{startup_id}/approve
GET  /api/v1/live-demo/manifest
POST /api/v1/live-demo/sessions
GET  /api/v1/live-demo/sessions/{session_id}
POST /api/v1/live-demo/sessions/{session_id}/message
WS   /api/v1/live-demo/sessions/{session_id}/voice
```

Bounded browser-control prototype:

```text
POST   /api/v1/demo-sessions
GET    /api/v1/demo-sessions/{session_id}
POST   /api/v1/demo-sessions/{session_id}/message
POST   /api/v1/demo-sessions/{session_id}/actions/approve
POST   /api/v1/demo-sessions/{session_id}/actions/reject
POST   /api/v1/demo-sessions/{session_id}/reset
POST   /api/v1/demo-sessions/{session_id}/verify
DELETE /api/v1/demo-sessions/{session_id}
```

## Testing

Backend:

```bash
cd backend
pytest
```

Focused live demo tests:

```bash
cd backend
pytest tests/test_live_demo_api.py tests/test_live_demo_voice_flow.py
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Current Limitations

- The live demo uses a cached generated extraction report, not a finished founder-facing setup UI.
- The extraction approval flow is in API shape, but not yet fully productized.
- The embedded iframe mode works well for same-origin/local app routes. Arbitrary third-party sites may block iframe embedding with security headers.
- For blocked external apps, the likely production renderer is a remote browser stream controlled by Playwright/Browserbase/Stagehand-style infrastructure, still bounded by the approved manifest.
- The text walkthrough currently plays a full event timeline. Voice mode is step-aware for interruption and resume.

## Deployment Notes

Backend command:

```bash
cd backend
APP_DEBUG=false python main.py
```

or:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend build:

```bash
cd frontend
npm ci
npm run build
```

Production environment:

```env
APP_ENV=production
APP_DEBUG=false
FRONTEND_BASE_URL=https://your-frontend-domain
CORS_ALLOW_ORIGINS=https://your-frontend-domain
VITE_API_BASE_URL=https://your-backend-domain
```

For a public voice demo, serve both frontend and backend over HTTPS so browser microphone permissions and WebSocket audio work reliably.

## More Docs

- `AI_DEMO_AGENT_ARCHITECTURE.md` - detailed product/runtime architecture notes
- `backend/README.md` - backend-specific notes
- `frontend/README.md` - frontend placeholder notes
- `backend/IMPLEMENTATION_PLAN.md` - older campaign/demo-room implementation plan
