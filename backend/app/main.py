"""
Jamiiz AI Demo Lab — FastAPI application entry point.

Three assistants, one backend:
  POST /chat              — all assistants (website, property, document)
  POST /documents/upload  — ingest a file into a Pinecone namespace
  POST /documents/text    — ingest raw text
  GET  /documents/status/{namespace}
  POST /leads             — capture prospect details
  GET  /health            — service health check
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router
from app.api.routes_leads import router as leads_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.lead_service import init_db

# ── Logging ───────────────────────────────────────────────────────────
setup_logging()
logger = logging.getLogger("jamiiz")


# ── App factory ───────────────────────────────────────────────────────
def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Jamiiz AI Demo Lab",
        description=(
            "Custom AI assistants trained on your business content. "
            "Three demos: Website Assistant, Property/Guest Assistant, Document Assistant."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    # CORS — allow the frontend dev server and production domain
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Startup ───────────────────────────────────────────────────────
    @app.on_event("startup")
    async def startup():
        logger.info("Starting Jamiiz AI Demo Lab (env=%s)", settings.app_env)
        init_db()
        logger.info("Ready. Docs at /docs")

    # ── Routes ────────────────────────────────────────────────────────
    app.include_router(chat_router)
    app.include_router(documents_router)
    app.include_router(leads_router)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "service": "jamiiz-ai-demos"}

    return app


app = create_app()


# ── Dev entrypoint ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
