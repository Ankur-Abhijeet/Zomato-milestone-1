"""Meta endpoint — static configuration exposed to the frontend (Phase 5a/5c).

GET /api/v1/meta
Returns budget band descriptions, defaults, and example locations so the
frontend can populate its form without hardcoding backend logic.

Phase 5c: budget band descriptions now come from budget_band_descriptions()
which reads live thresholds from Settings — single source of truth.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.deps import SettingsDep
from api.schemas.response import MetaResponse
from api.utils.budget import budget_band_descriptions

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get(
    "/meta",
    response_model=MetaResponse,
    summary="API metadata",
    description=(
        "Returns static configuration values: budget band descriptions, "
        "default parameters, and example city/area names."
    ),
)
async def get_meta(settings: SettingsDep) -> MetaResponse:
    return MetaResponse(
        budget_bands=budget_band_descriptions(settings),
        default_top_k=settings.recommendation_top_k,
        default_min_rating=settings.default_min_rating,
        default_budget=settings.default_budget,
    )
