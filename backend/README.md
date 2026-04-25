# FastAPI Backend

Classic FastAPI starter for the `backend` workspace folder.

## Quickstart

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy environment file:
   ```bash
   copy .env.example .env
   ```
4. Run the API:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

## Routes

- `GET /` - basic service metadata
- `GET /api/v1/health` - health check
- `POST /api/v1/tasks` - routes a founder task through the MVP orchestrator, content agent, and review agent

## MVP Agent Flow

The first GTM AI Office slice is backend-only and stateless:

1. The Orchestrator picks an agent with deterministic routing.
2. Content tasks go to the Content Generator Agent.
3. Demo tasks return an unavailable response until the Demo Agent is added.
4. Unsupported tasks return a clear unsupported response.
5. The Review Agent scores completed work and the Orchestrator returns the final decision.

Example request:

```json
{
  "prompt": "Create launch content for my GTM AI office",
  "startup_idea": "AI office for founders starting and maintaining business ideas",
  "target_audience": "solo founders",
  "goal": "get first customer conversations",
  "tone": "practical",
  "channel": "landing page and email"
}
```
