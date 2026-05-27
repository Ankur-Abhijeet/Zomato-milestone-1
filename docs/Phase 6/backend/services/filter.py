"""Hard-constraint filter with architecture-defined pipeline order."""

from __future__ import annotations

import logging
from typing import List

from data.matching import cuisines_overlap, matches_location
from models.integration import FilterResult, FilterStepCounts
from models.restaurant import Restaurant
from models.user_preferences import UserPreferences

logger = logging.getLogger(__name__)


class HardConstraintFilter:
    """
    Apply hard filters in order: location → rating → budget → cuisine.

    Order matters; step counts support empty-result diagnostics.
    """

    def filter(
        self,
        restaurants: List[Restaurant],
        preferences: UserPreferences,
    ) -> FilterResult:
        counts = FilterStepCounts(initial=len(restaurants))
        results = list(restaurants)

        results = [
            r for r in results if matches_location(r, preferences.location)
        ]
        counts.after_location = len(results)
        logger.debug("After location filter: %d", len(results))

        results = [
            r
            for r in results
            if r.rating is not None and r.rating >= preferences.min_rating
        ]
        counts.after_rating = len(results)
        logger.debug("After rating filter: %d", len(results))

        results = [
            r
            for r in results
            if r.budget_band is not None and r.budget_band == preferences.budget
        ]
        counts.after_budget = len(results)
        logger.debug("After budget filter: %d", len(results))

        cuisine_filter = preferences.cuisines_for_filter()
        if cuisine_filter:
            results = [
                r
                for r in results
                if cuisines_overlap(r.cuisines, cuisine_filter)
            ]
        counts.after_cuisine = len(results)
        logger.debug("After cuisine filter: %d", len(results))

        return FilterResult(
            candidates=results,
            step_counts=counts,
            preferences=preferences,
        )
