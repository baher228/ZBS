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
- `POST /api/v1/campaigns` - creates a LangGraph-powered GTM campaign and personalized demo room
- `GET /api/v1/campaigns/{id}` - loads a campaign package
- `GET /api/v1/demo-rooms/{id}` - loads a prospect-facing demo room
- `POST /api/v1/demo-rooms/{id}/chat` - chats with the demo agent and stores transcript
- `POST /api/v1/demo-rooms/{id}/qualify` - creates lead score, CRM notes, objections, and follow-up

## Campaign Demo Room Flow

The main product slice uses LangGraph:

1. Orchestrator Agent initializes campaign state and routes the workflow.
2. Strategist Agent creates the product profile and ICP.
3. Research Agent creates the prospect profile.
4. Demo Brief step creates the prospect-specific demo narrative.
5. Demo Plan Agent creates guided demo steps, assets needed, talk tracks, and routing rules.
6. Outreach Agent writes the cold message with the demo room link.
7. Readiness step scores whether the room is specific enough to send.
8. Demo room is persisted in memory for chat and qualification.

Reusable AI capabilities live under `app/agents/capabilities`. Graphs live under
`app/agents/graphs` and compose those capabilities into workflows. This keeps the
agents reusable for future non-demo-room workflows such as ICP-only, outreach-only,
research-only, or post-campaign learning flows.

Seeded scenarios for testing and demos:

- `AI GTM Office` selling to `Mubit`
- `TracePilot` selling to `Render`
- `SecureShip` selling to `Linear`

Example campaign request:

```json
{
  "product_name": "DemoRoom AI",
  "product_description": "AI demo rooms for technical B2B founders that turn cold outreach into qualified sales conversations.",
  "target_audience": "technical B2B founders",
  "prospect_company": "Pydantic",
  "prospect_description": "Python data validation and agent reliability tooling company"
}
```

Use mock mode for deterministic local tests:

```bash
LLM_PROVIDER=mock pytest
```

To try OpenAI-backed generation, set `LLM_PROVIDER=openai` with `OPENAI_API_KEY` in the root `.env`.
