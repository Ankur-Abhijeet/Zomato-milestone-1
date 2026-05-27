"""Phase 3 integration models: filter results and LLM prompt payload."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from models.restaurant import Restaurant
from models.user_preferences import UserPreferences


class FilterStepCounts(BaseModel):
    initial: int = 0
    after_location: int = 0
    after_rating: int = 0
    after_budget: int = 0
    after_cuisine: int = 0


class FilterResult(BaseModel):
    candidates: List[Restaurant] = Field(default_factory=list)
    step_counts: FilterStepCounts = Field(default_factory=FilterStepCounts)
    preferences: UserPreferences

    @property
    def is_empty(self) -> bool:
        return len(self.candidates) == 0

    def relaxation_hints(self) -> List[str]:
        """Suggest which constraints to relax when the filter returns nothing."""
        hints: List[str] = []
        counts = self.step_counts
        prefs = self.preferences

        if counts.after_location == 0:
            hints.append(
                f'No restaurants found for location "{prefs.location}". '
                "Try a nearby city (e.g. Bengaluru for Bangalore) or a broader area."
            )
        elif counts.after_rating == 0:
            hints.append(
                f"No restaurants rated >= {prefs.min_rating}. "
                "Try lowering --min-rating."
            )
        elif counts.after_budget == 0:
            hints.append(
                f'No restaurants in budget band "{prefs.budget}". '
                "Try a different --budget (low, medium, high)."
            )
        elif counts.after_cuisine == 0:
            cuisine_label = ", ".join(prefs.cuisines)
            hints.append(
                f'No restaurants matching cuisine(s): {cuisine_label}. '
                "Try fewer or broader cuisine types."
            )
        return hints


class PromptPayload(BaseModel):
    """LLM-ready messages and structured candidate data (Phase 4 input)."""

    system_message: str
    user_message: str
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    top_k: int
    preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntegrationResult(BaseModel):
    """Output of the full Phase 3 pipeline."""

    filter_result: FilterResult
    capped_candidates: List[Restaurant] = Field(default_factory=list)
    prompt_payload: Optional[PromptPayload] = None
    skip_llm: bool = False
    user_message: Optional[str] = None
