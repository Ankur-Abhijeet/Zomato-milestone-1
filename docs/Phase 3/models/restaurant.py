from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

BudgetBand = Literal["low", "medium", "high"]


class Restaurant(BaseModel):
    """Normalized restaurant record for filtering and LLM prompts."""

    id: str
    name: str
    city: str
    area: Optional[str] = None
    address: Optional[str] = None
    cuisines: List[str] = Field(default_factory=list)
    cost_display: Optional[str] = None
    cost_inr: Optional[int] = None
    budget_band: Optional[BudgetBand] = None
    rating: Optional[float] = None
    votes: Optional[int] = None
    rest_type: Optional[str] = None
    dish_liked: Optional[str] = None
    online_order: Optional[bool] = None
    book_table: Optional[bool] = None
    url: Optional[str] = None
    extras: Dict[str, Any] = Field(default_factory=dict)

    @property
    def location_display(self) -> str:
        if self.area and self.city:
            return f"{self.area}, {self.city}"
        return self.city or self.area or "Unknown"

    @property
    def cuisine_display(self) -> str:
        return ", ".join(self.cuisines) if self.cuisines else "Unknown"
