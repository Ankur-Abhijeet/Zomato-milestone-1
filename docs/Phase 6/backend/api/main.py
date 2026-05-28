"""FastAPI application factory (Phase 5a / 6).

Lifecycle
---------
1. On startup:  RestaurantRepository.load() is called once.
                app.state.repository_ready is set to True when done.
                /ready returns 503 until this completes.
2. On shutdown: No special cleanup needed (in-memory repository).

Middleware (Phase 6)
--------------------
- RequestIDMiddleware: stamps every response with X-Request-ID + logs latency
- SlowAPI rate limiter: 30 req/min per IP on POST /recommendations (configurable)

CORS
----
Allows the Vite dev server (localhost:5173) and any origins listed in
ALLOWED_ORIGINS environment variable (comma-separated URLs, Phase 5b+).

Usage
-----
    python run_api.py                    # dev with reload
    uvicorn api.main:app --port 8000     # production
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from api.errors import register_error_handlers
from api.middleware.request_id import RequestIDMiddleware
from api.routes import health, meta, recommendations
from config.settings import get_settings
from data.repository import RestaurantRepository

logger = logging.getLogger(__name__)

# ── Rate limiter (shared across routes via app.state) ─────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[])


def _parse_allowed_origins() -> list[str]:
    """Build CORS origin list from defaults + ALLOWED_ORIGINS env var."""
    defaults = [
        "http://localhost:5173",  # Vite dev server (Phase 5b)
        "http://localhost:3000",  # CRA fallback
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    extra = os.getenv("ALLOWED_ORIGINS", "")
    if extra.strip():
        extras = [o.strip().rstrip("/") for o in extra.split(",") if o.strip()]
        defaults.extend(extras)
    return defaults


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load the restaurant dataset on startup; mark ready when done."""
    settings = get_settings()
    repo = RestaurantRepository(settings)
    app.state.repository = repo
    app.state.repository_ready = False

    try:
        logger.info("Loading restaurant dataset …")
        repo.load()
        app.state.repository_ready = True
        logger.info("Restaurant dataset loaded: %d records", len(repo.all()))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load dataset: %s", exc)
        # Keep repository_ready=False; /ready will return 503

    yield  # Application is running

    logger.info("API shutting down.")


def create_app() -> FastAPI:
    """Build and return the configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Zomato Restaurant Recommender API",
        description=(
            "AI-powered restaurant recommendation engine. "
            "Uses structured filters (location, budget, rating, cuisine) "
            "combined with Groq LLM ranking for personalised results."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Phase 6: Rate limiter ─────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(
        RateLimitExceeded,  # type: ignore[arg-type]
        _rate_limit_exceeded_handler,
    )

    # ── Phase 6: Request-ID + latency middleware ──────────────────────────────
    app.add_middleware(RequestIDMiddleware)

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins = _parse_allowed_origins()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(meta.router)
    app.include_router(recommendations.router)

    return app


# Module-level instance (used by uvicorn and imports)
app = create_app()
