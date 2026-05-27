"""Phase 4 recommendation result models."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from models.restaurant import Restaurant


class RecommendationItem(BaseModel):
    """A ranked recommendation merged with structured restaurant data."""

    rank: int
    restaurant_id: str
    name: str
    cuisine: str
    rating: Optional[float] = None
    estimated_cost: Optional[str] = None
    location: str
    explanation: str
    is_ai_generated: bool = True


class RecommendationResult(BaseModel):
    """Ordered top-N recommendations from the LLM (or fallback)."""

    summary: Optional[str] = None
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    used_fallback: bool = False
    fallback_reason: Optional[str] = None
    top_k: int = 5

    @property
    def is_empty(self) -> bool:
        return len(self.recommendations) == 0

    @classmethod
    def from_message(cls, message: str) -> "RecommendationResult":
        return cls(recommendations=[], summary=message)
