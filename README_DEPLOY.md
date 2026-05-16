# Orion deployment notes

This project is a FastAPI app that serves the frontend from `backend/app/static` and exposes the `/api/...` routes used by the simulation, Q&A bot, and advisor.

## Render settings

Use these values if creating a Render Web Service manually:

- Runtime: Python
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

The app has a Python fallback for the scoring engine if the local C++ executable is unavailable on the Linux host.

## Optional environment variables

- `OPENAI_API_KEY`: enables the LLM advisor. Without this, the app still works with the local fallback advisor.
- `OPENAI_ADVISOR_MODEL`: defaults to `gpt-4o-mini` in `render.yaml`.
