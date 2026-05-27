"""Sort and cap filtered restaurants for LLM context."""

from __future__ import annotations

from typing import List

from config.settings import Settings, get_settings
from models.restaurant import Restaurant


def select_candidates(
    restaurants: List[Restaurant],
    *,
    cap: int | None = None,
    settings: Settings | None = None,
) -> List[Restaurant]:
    """
    Return top-N candidates sorted by rating, votes, then name (stable, reproducible).
    """
    settings = settings or get_settings()
    limit = cap if cap is not None else settings.candidate_cap
    limit = min(max(1, limit), settings.candidate_cap_max)

    sorted_rows = sorted(
        restaurants,
        key=lambda r: (
            -(r.rating or 0.0),
            -(r.votes or 0),
            r.name.lower(),
            r.id,
        ),
    )
    return sorted_rows[:limit]
