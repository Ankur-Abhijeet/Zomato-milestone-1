"""Template-based recommendations when the LLM is unavailable."""

from __future__ import annotations

from typing import List, Optional

from models.recommendation import RecommendationItem, RecommendationResult
from models.restaurant import Restaurant
from models.user_preferences import UserPreferences
from services.candidate_selector import select_candidates


def build_fallback_result(
    candidates: List[Restaurant],
    preferences: UserPreferences,
    *,
    top_k: int,
    reason: str,
) -> RecommendationResult:
    """Return filter-sorted top-N with template explanations (not AI-generated)."""
    ranked = select_candidates(candidates, cap=top_k)
    items: List[RecommendationItem] = []

    for rank, restaurant in enumerate(ranked[:top_k], start=1):
        items.append(
            RecommendationItem(
                rank=rank,
                restaurant_id=restaurant.id,
                name=restaurant.name,
                cuisine=restaurant.cuisine_display,
                rating=restaurant.rating,
                estimated_cost=_cost_label(restaurant),
                location=restaurant.location_display,
                explanation=_template_explanation(restaurant, preferences),
                is_ai_generated=False,
            )
        )

    summary = (
        f"Showing top {len(items)} matches by rating (AI unavailable: {reason})."
        if items
        else None
    )

    return RecommendationResult(
        summary=summary,
        recommendations=items,
        used_fallback=True,
        fallback_reason=reason,
        top_k=top_k,
    )


def _template_explanation(restaurant: Restaurant, preferences: UserPreferences) -> str:
    rating_part = (
        f"rated {restaurant.rating:.1f}/5"
        if restaurant.rating is not None
        else "rated well"
    )
    cost_part = _cost_label(restaurant) or "unknown cost"
    cuisine_part = restaurant.cuisine_display
    location_part = restaurant.location_display

    parts = [
        f"{restaurant.name} ({cuisine_part}) in {location_part} is {rating_part}",
        f"with estimated cost {cost_part} for two",
        f"— fits your {preferences.budget} budget in {preferences.location}",
    ]
    if preferences.cuisines:
        parts.append(f"and matches cuisine interest: {', '.join(preferences.cuisines)}")
    if preferences.additional:
        parts.append(
            f"(Note: could not evaluate soft preference '{preferences.additional}' without AI)"
        )
    return ". ".join(parts) + "."


def _cost_label(restaurant: Restaurant) -> Optional[str]:
    if restaurant.cost_display:
        return restaurant.cost_display
    if restaurant.cost_inr is not None:
        return f"₹{restaurant.cost_inr}"
    return None
