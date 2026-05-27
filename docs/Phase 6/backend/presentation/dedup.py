"""CLI-layer deduplication helper (Phase 5c).

Mirrors the API-layer _deduplicate() in api/schemas/response.py but operates
on the domain RecommendationResult model so the CLI and API produce
consistently deduplicated output without coupling to the API schemas.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from models.recommendation import RecommendationItem, RecommendationResult


def dedup_recommendation_result(
    result: RecommendationResult,
) -> Tuple[RecommendationResult, int]:
    """Collapse duplicate name+location outlets in a RecommendationResult.

    Returns
    -------
    (deduped_result, number_of_items_removed)
    The deduped result has ranks re-numbered 1…N.
    If nothing was removed, returns the original object unchanged (no copy).
    """
    items = result.recommendations
    seen: Dict[Tuple[str, str], bool] = {}
    kept: List[RecommendationItem] = []

    for item in items:
        key = (item.name.casefold().strip(), item.location.casefold().strip())
        if key in seen:
            continue
        seen[key] = True
        kept.append(item)

    removed = len(items) - len(kept)
    if removed == 0:
        return result, 0

    # Re-number ranks to be contiguous 1…N
    renumbered = [
        item.model_copy(update={"rank": new_rank})
        for new_rank, item in enumerate(kept, start=1)
    ]

    deduped = result.model_copy(update={"recommendations": renumbered})
    return deduped, removed
