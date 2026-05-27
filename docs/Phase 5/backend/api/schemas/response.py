"""API response schemas (Phase 5a/5c).

These DTOs are the stable JSON contract between backend and frontend.
They mirror internal domain models but are decoupled so the domain can
evolve without breaking the API surface.

Phase 5c additions
------------------
- `RecommendResponse.dedup_removed` — count of duplicate name+location items
  collapsed by `_deduplicate()` before the response is serialised.
- `_deduplicate()` — keeps the highest-ranked (lowest rank number) item
  when multiple outlets share the same (name, location) pair, then
  re-numbers ranks 1…N so the response is always contiguous.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from models.integration import FilterResult, IntegrationResult
from models.recommendation import RecommendationResult

logger = logging.getLogger(__name__)


class FilterStatsDTO(BaseModel):
    """Counts at each filter step — useful for frontend diagnostics."""

    initial: int = 0
    after_location: int = 0
    after_rating: int = 0
    after_budget: int = 0
    after_cuisine: int = 0
    capped_for_llm: int = 0


class RecommendationItemDTO(BaseModel):
    """A single ranked restaurant recommendation."""

    rank: int
    id: str = Field(description="Unique restaurant identifier")
    name: str
    cuisine: str
    rating: Optional[float] = None
    estimated_cost: Optional[str] = None
    location: str
    explanation: str
    is_ai_generated: bool = True


class RecommendResponse(BaseModel):
    """Full response for POST /api/v1/recommendations."""

    summary: Optional[str] = None
    used_fallback: bool = False
    skip_llm: bool = False
    message: Optional[str] = Field(
        default=None,
        description="Human-readable message when no candidates match filters",
    )
    filter_stats: Optional[FilterStatsDTO] = None
    recommendations: List[RecommendationItemDTO] = Field(default_factory=list)
    dedup_removed: int = Field(
        default=0,
        description=(
            "Number of duplicate name+location outlets removed from the response. "
            "When > 0 the frontend can surface a hint like '2 duplicate outlets hidden'."
        ),
    )

    # ── Factory helpers ───────────────────────────────────────────────────────

    @classmethod
    def from_domain(
        cls,
        result: RecommendationResult,
        filter_result: FilterResult,
        capped_for_llm: int,
    ) -> "RecommendResponse":
        """Build a response DTO from domain objects, deduplicating by name+location."""
        counts = filter_result.step_counts
        stats = FilterStatsDTO(
            initial=counts.initial,
            after_location=counts.after_location,
            after_rating=counts.after_rating,
            after_budget=counts.after_budget,
            after_cuisine=counts.after_cuisine,
            capped_for_llm=capped_for_llm,
        )

        raw_items = [
            RecommendationItemDTO(
                rank=item.rank,
                id=item.restaurant_id,
                name=item.name,
                cuisine=item.cuisine,
                rating=item.rating,
                estimated_cost=item.estimated_cost,
                location=item.location,
                explanation=item.explanation,
                is_ai_generated=item.is_ai_generated,
            )
            for item in result.recommendations
        ]

        deduped, removed = _deduplicate(raw_items)

        if removed:
            logger.info(
                "Deduplication removed %d duplicate outlet(s) from response", removed
            )

        return cls(
            summary=result.summary,
            used_fallback=result.used_fallback,
            skip_llm=False,
            filter_stats=stats,
            recommendations=deduped,
            dedup_removed=removed,
        )

    @classmethod
    def from_empty(cls, integration: IntegrationResult) -> "RecommendResponse":
        """Build a response DTO when no candidates passed the filters."""
        counts = integration.filter_result.step_counts
        stats = FilterStatsDTO(
            initial=counts.initial,
            after_location=counts.after_location,
            after_rating=counts.after_rating,
            after_budget=counts.after_budget,
            after_cuisine=counts.after_cuisine,
            capped_for_llm=0,
        )
        return cls(
            summary=None,
            used_fallback=False,
            skip_llm=True,
            message=integration.user_message,
            filter_stats=stats,
            recommendations=[],
            dedup_removed=0,
        )


class MetaResponse(BaseModel):
    """Response for GET /api/v1/meta."""

    budget_bands: dict = Field(
        default_factory=lambda: {
            "low":    "≤ ₹500 per person",
            "medium": "≤ ₹1,500 per person",
            "high":   "> ₹1,500 per person",
        }
    )
    default_top_k: int = 5
    default_min_rating: float = 3.0
    default_budget: str = "medium"
    example_locations: List[str] = Field(
        default_factory=lambda: [
            "Bellandur",
            "Koramangala",
            "Indiranagar",
            "Whitefield",
            "HSR Layout",
            "BTM Layout",
            "Jayanagar",
            "Marathahalli",
        ]
    )


# ── Deduplication helper ──────────────────────────────────────────────────────

def _deduplicate(
    items: List[RecommendationItemDTO],
) -> Tuple[List[RecommendationItemDTO], int]:
    """Collapse duplicate name+location outlets, keeping the highest-ranked item.

    Algorithm
    ---------
    1. Iterate items in rank order (already sorted by LLM/fallback).
    2. Build a key = (name.casefold().strip(), location.casefold().strip()).
    3. Keep the first occurrence of each key; discard subsequent duplicates.
    4. Re-number kept items 1…N so ranks are always contiguous in the response.

    Returns
    -------
    (deduped_list, number_of_items_removed)
    """
    seen: Dict[Tuple[str, str], bool] = {}
    kept: List[RecommendationItemDTO] = []

    for item in items:
        key = (item.name.casefold().strip(), item.location.casefold().strip())
        if key in seen:
            continue
        seen[key] = True
        kept.append(item)

    # Re-number ranks so they are always 1-based and contiguous
    renumbered = [
        item.model_copy(update={"rank": new_rank})
        for new_rank, item in enumerate(kept, start=1)
    ]

    removed = len(items) - len(renumbered)
    return renumbered, removed
