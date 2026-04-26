# ZBS

ZBS is an AI go-to-market workspace for early-stage B2B founders. It turns company context, website data, and founder chat history into practical GTM outputs: positioning, landing page copy, campaign research, legal guidance, outreach, personalized demo rooms, and lead qualification.

## What It Does

- Generates startup GTM assets such as positioning, landing copy, launch emails, social posts, ICP notes, and market research.
- Builds AI demo-room campaigns for specific prospects, including product strategy, prospect context, demo plans, outreach, and readiness scoring.
- Lets prospects chat with a demo agent, then summarizes qualification, objections, buying signals, CRM notes, and follow-up email copy.
- Stores company profile, website context, chat-derived facts, and cached agent results under `backend/data`.
- Supports optional MuBit learning instrumentation and fal.ai image generation.

## Project Structure

```text
backend/   FastAPI API, LangGraph agent workflows, LLM providers, storage, tests
frontend/  TanStack/React/Vite app for the product UI
```

## Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API runs at:

```text
http://127.0.0.1:8000
```

Run backend tests:

```bash
cd backend
pytest
```

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend usually runs at:

```text
http://localhost:5173
```

If the backend is not on `http://127.0.0.1:8000`, set:

```env
VITE_API_BASE_URL=http://your-api-host
```

## Environment

Start from `backend/.env.example`. Important backend variables:

```env
APP_ENV=development
APP_DEBUG=true
LLM_PROVIDER=mock
LLM_MODEL=mock-gtm-v1
AGENT_CACHE_ENABLED=true
AGENT_CACHE_MAX_ENTRIES=500
PYDANTIC_AI_GATEWAY_API_KEY=
OPENAI_API_KEY=
FAL_API_KEY=
MUBIT_ENABLED=true
MUBIT_API_KEY=
MUBIT_AGENT_ID=zbs-agent
```

Use `LLM_PROVIDER=mock` for deterministic local development and tests. Use `gateway` or `openai` for real LLM-backed generation.

Do not commit `.env` files or anything under `backend/data`; both can contain private company data or API keys.

## Main API Routes

- `GET /api/v1/health` - health check
- `GET /api/v1/health/provider` - provider status
- `POST /api/v1/company` - save company profile
- `GET /api/v1/company` - load company profile
- `POST /api/v1/tasks` - route a generic content/legal task through the orchestrator
- `POST /api/v1/content/chat` - content creation chat
- `POST /api/v1/marketing-research/chat` - marketing research chat
- `POST /api/v1/legal/chat` - legal chat and drafting
- `POST /api/v1/campaigns` - create a prospect campaign and demo room
- `GET /api/v1/demo-rooms/{id}` - load a demo room
- `POST /api/v1/demo-rooms/{id}/chat` - chat with a demo-room agent
- `POST /api/v1/demo-rooms/{id}/qualify` - generate lead qualification

## Caching

Main agent results are cached in:

```text
backend/data/agent_result_cache.json
```

This covers repeated stateless agent requests such as tasks, content chat, marketing research, legal chat, legal overview, social post generation, and campaign creation. Live demo routes and stateful demo-room chat/qualification are not cached.

Disable caching with:

```env
AGENT_CACHE_ENABLED=false
```

## Deployment Notes

Backend start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend build command:

```bash
npm ci && npm run build
```

For production, set:

```env
APP_ENV=production
APP_DEBUG=false
FRONTEND_BASE_URL=https://your-frontend-domain
CORS_ALLOW_ORIGINS=https://your-frontend-domain
```

If deploying on a VPS, run backend and frontend behind a reverse proxy such as Caddy or Nginx. Persist `backend/data` if you want company context, chat-derived facts, and cached agent results to survive redeploys.

## More Docs

- Backend details: `backend/README.md`
- Frontend details: `frontend/README.md`
