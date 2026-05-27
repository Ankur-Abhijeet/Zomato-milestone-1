"""User preference domain model (Phase 2)."""

from __future__ import annotations

import unicodedata
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

BudgetChoice = Literal["low", "medium", "high"]

BUDGET_VALUES = ("low", "medium", "high")


class UserPreferences(BaseModel):
    """
    Validated user preferences for filtering and LLM prompts.

    Hard filters use location, budget, cuisines, min_rating.
    Soft preferences use additional free text (Phase 4).
    """

    location: str = Field(..., description="City or area (required)")
    budget: BudgetChoice = Field(
        default="medium",
        description="Budget band: low, medium, or high",
    )
    cuisines: List[str] = Field(
        default_factory=list,
        description="Cuisine types; empty means any",
    )
    min_rating: float = Field(
        default=3.0,
        ge=0.0,
        le=5.0,
        description="Minimum restaurant rating (0–5)",
    )
    additional: Optional[str] = Field(
        default=None,
        description="Free-text soft preferences (family-friendly, quick service, …)",
    )

    model_config = {"str_strip_whitespace": True, "extra": "ignore"}

    @field_validator("location")
    @classmethod
    def _validate_location(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFC", value.strip())
        if not normalized:
            raise ValueError("location is required and cannot be blank")
        return normalized

    @field_validator("budget", mode="before")
    @classmethod
    def _normalize_budget(cls, value: object) -> object:
        if value is None:
            return "medium"
        if isinstance(value, str):
            key = value.strip().lower()
            if not key:
                return "medium"
            if key not in BUDGET_VALUES:
                raise ValueError(
                    f"budget must be one of: {', '.join(BUDGET_VALUES)}"
                )
            return key
        raise ValueError(
            f"budget must be one of: {', '.join(BUDGET_VALUES)}"
        )

    @field_validator("cuisines", mode="before")
    @classmethod
    def _normalize_cuisines(cls, value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            if not value.strip():
                return []
            parts = [p.strip() for p in value.split(",")]
            return [p for p in parts if p]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("cuisines must be a list or comma-separated string")

    @field_validator("min_rating", mode="before")
    @classmethod
    def _coerce_min_rating(cls, value: object) -> object:
        if value is None or value == "":
            return 3.0
        return value

    @field_validator("additional")
    @classmethod
    def _normalize_additional(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = value.strip()
        return text or None

    def cuisines_for_filter(self) -> Optional[List[str]]:
        """Return cuisines for repository filter, or None if any cuisine is OK."""
        return self.cuisines if self.cuisines else None
