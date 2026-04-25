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
