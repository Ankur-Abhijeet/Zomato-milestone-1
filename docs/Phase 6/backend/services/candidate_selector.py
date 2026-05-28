"""Sort and cap filtered restaurants for LLM context."""

from __future__ import annotations

import random
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
    Return a random sample of candidates to give the AI a diverse selection.
    """
    settings = settings or get_settings()
    limit = cap if cap is not None else settings.candidate_cap
    limit = min(max(1, limit), settings.candidate_cap_max)

    if len(restaurants) <= limit:
        # Shuffle them anyway so the AI doesn't see the exact same order
        shuffled = list(restaurants)
        random.shuffle(shuffled)
        return shuffled

    return random.sample(restaurants, limit)
