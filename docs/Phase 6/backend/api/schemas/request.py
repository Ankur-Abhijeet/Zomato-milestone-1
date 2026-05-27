"""API request schemas (Phase 5a).

Mirrors UserPreferences with the additional `top_k` field for the endpoint.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

BudgetChoice = Literal["low", "medium", "high"]


class RecommendRequest(BaseModel):
    """Body for POST /api/v1/recommendations."""

    location: str = Field(
        ...,
        description="City or area (required)",
        examples=["Bellandur", "Koramangala"],
    )
    budget: BudgetChoice = Field(
        default="medium",
        description="Budget band: low (≤ ₹500), medium (≤ ₹1500), high (> ₹1500)",
    )
    cuisines: List[str] = Field(
        default_factory=list,
        description="Cuisine types to filter by; empty list means any cuisine",
        examples=[["Italian", "Chinese"]],
    )
    min_rating: float = Field(
        default=3.0,
        ge=0.0,
        le=5.0,
        description="Minimum restaurant rating (0–5)",
    )
    additional: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Free-text soft preferences passed to the LLM (e.g. 'family-friendly, outdoor seating')",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of recommendations to return (1–10)",
    )

    model_config = {"str_strip_whitespace": True, "extra": "ignore"}
