"""Meta endpoint — static configuration exposed to the frontend (Phase 5a/5c).

GET /api/v1/meta
Returns budget band descriptions, defaults, and example locations so the
frontend can populate its form without hardcoding backend logic.

Phase 5c: budget band descriptions now come from budget_band_descriptions()
which reads live thresholds from Settings — single source of truth.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.deps import RepoDep, SettingsDep
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
async def get_meta(settings: SettingsDep, repo: RepoDep) -> MetaResponse:
    MACRO_REGIONS = [
        "Koramangala",
        "Indiranagar",
        "Whitefield",
        "Marathahalli",
        "HSR Layout",
        "Jayanagar",
        "JP Nagar"
    ]
    
    counts = {region: 0 for region in MACRO_REGIONS}
    other_blr_count = 0
    other_india_count = 0
    
    for r in repo.all():
        city_lower = r.city.lower() if r.city else ""
        area_lower = r.area.lower() if r.area else ""
        if "bangalore" in city_lower or "bengaluru" in city_lower or "bangalore" in area_lower:
            matched_macro = False
            for region in MACRO_REGIONS:
                if region.lower() in area_lower or region.lower() in city_lower:
                    counts[region] += 1
                    matched_macro = True
                    break
            if not matched_macro:
                other_blr_count += 1
        else:
            other_india_count += 1
            
    location_categories = []
    for region in MACRO_REGIONS:
        location_categories.append({"label": region, "query": region, "count": counts[region]})
    
    location_categories.append({"label": "Anywhere else in Bangalore", "query": "__other_bangalore__", "count": other_blr_count})
    location_categories.append({"label": "Rest of India", "query": "__other_india__", "count": other_india_count})

    return MetaResponse(
        budget_bands=budget_band_descriptions(settings),
        default_top_k=settings.recommendation_top_k,
        default_min_rating=settings.default_min_rating,
        default_budget=settings.default_budget,
        location_categories=location_categories,
    )
