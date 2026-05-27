"""Shared dependency-injection helpers (Phase 5a).

FastAPI injects these via `Depends(...)`.  The RestaurantRepository singleton
is stored on `app.state` during the lifespan and retrieved here so all routes
share a single loaded copy of the dataset.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from config.settings import Settings
from config.settings import get_settings as _get_settings
from data.repository import RestaurantRepository
from services.recommendation_engine import RecommendationEngine


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_settings() -> Settings:
    return _get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

def get_repository(request: Request) -> RestaurantRepository:
    """Return the shared RestaurantRepository or raise 503 if not ready."""
    repo: RestaurantRepository | None = getattr(request.app.state, "repository", None)
    if repo is None or not getattr(request.app.state, "repository_ready", False):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "service_unavailable",
                "message": "Dataset is still loading. Please retry in a moment.",
            },
        )
    return repo


RepoDep = Annotated[RestaurantRepository, Depends(get_repository)]


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

def get_recommendation_engine(settings: SettingsDep) -> RecommendationEngine:
    return RecommendationEngine(settings)


EngineDep = Annotated[RecommendationEngine, Depends(get_recommendation_engine)]
