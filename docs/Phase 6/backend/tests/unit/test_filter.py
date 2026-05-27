"""Unit tests for HardConstraintFilter step counts — Phase 6.

These tests run against the real Parquet cache (~51 k rows) so they verify
the filter pipeline produces sensible step counts without needing Groq.
"""

from __future__ import annotations

import pytest

from config.settings import get_settings
from data.repository import RestaurantRepository
from models.user_preferences import UserPreferences
from services.filter import HardConstraintFilter


@pytest.fixture(scope="module")
def restaurants():
    r = RestaurantRepository(get_settings())
    r.load()
    return r.all()


@pytest.fixture()
def filt() -> HardConstraintFilter:
    return HardConstraintFilter()


class TestFilterStepCounts:
    def test_initial_count_matches_total(self, restaurants, filt):
        prefs = UserPreferences(location="Koramangala", budget="medium", min_rating=3.0)
        result = filt.filter(restaurants, prefs)
        assert result.step_counts.initial == len(restaurants)

    def test_after_location_less_than_initial(self, restaurants, filt):
        prefs = UserPreferences(location="Koramangala", budget="medium", min_rating=3.0)
        result = filt.filter(restaurants, prefs)
        assert result.step_counts.after_location < result.step_counts.initial
        assert result.step_counts.after_location > 0

    def test_after_rating_lte_after_location(self, restaurants, filt):
        prefs = UserPreferences(location="Koramangala", budget="medium", min_rating=4.0)
        result = filt.filter(restaurants, prefs)
        assert result.step_counts.after_rating <= result.step_counts.after_location

    def test_high_rating_reduces_candidates(self, restaurants, filt):
        prefs_low  = UserPreferences(location="Bangalore", budget="medium", min_rating=2.0)
        prefs_high = UserPreferences(location="Bangalore", budget="medium", min_rating=4.5)
        r_low  = filt.filter(restaurants, prefs_low)
        r_high = filt.filter(restaurants, prefs_high)
        assert r_high.step_counts.after_rating < r_low.step_counts.after_rating

    def test_unknown_location_gives_zero(self, restaurants, filt):
        prefs = UserPreferences(
            location="ZZZNonExistentCity9999", budget="medium", min_rating=3.0
        )
        result = filt.filter(restaurants, prefs)
        assert result.step_counts.after_location == 0
        assert len(result.candidates) == 0

    def test_cuisine_filter_narrows_results(self, restaurants, filt):
        prefs_any   = UserPreferences(location="Koramangala", budget="medium", min_rating=3.0)
        prefs_pizza = UserPreferences(
            location="Koramangala", budget="medium", min_rating=3.0, cuisines=["Pizza"]
        )
        r_any   = filt.filter(restaurants, prefs_any)
        r_pizza = filt.filter(restaurants, prefs_pizza)
        assert r_pizza.step_counts.after_cuisine <= r_any.step_counts.after_cuisine
