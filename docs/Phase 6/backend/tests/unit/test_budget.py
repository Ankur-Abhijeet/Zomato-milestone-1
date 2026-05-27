"""Unit tests for budget helpers — Phase 6."""

from __future__ import annotations

import pytest

from api.utils.budget import budget_band_descriptions, cost_inr_to_budget_hint
from config.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings(GROQ_API_KEY="test", BUDGET_LOW_MAX=500, BUDGET_MEDIUM_MAX=1500)


class TestCostInrToBudgetHint:
    def test_low_boundary(self, settings):
        hint = cost_inr_to_budget_hint(500, settings)
        assert "low" in hint
        assert "₹500" in hint

    def test_low_below_boundary(self, settings):
        assert "low" in cost_inr_to_budget_hint(200, settings)

    def test_medium(self, settings):
        assert "medium" in cost_inr_to_budget_hint(800, settings)

    def test_medium_boundary(self, settings):
        assert "medium" in cost_inr_to_budget_hint(1500, settings)

    def test_high(self, settings):
        assert "high" in cost_inr_to_budget_hint(2000, settings)

    def test_hint_contains_formatted_amount(self, settings):
        hint = cost_inr_to_budget_hint(2000, settings)
        assert "₹2,000" in hint

    def test_hint_contains_threshold(self, settings):
        hint = cost_inr_to_budget_hint(800, settings)
        assert "₹1,500" in hint  # medium threshold shown in hint


class TestBudgetBandDescriptions:
    def test_all_three_keys(self, settings):
        desc = budget_band_descriptions(settings)
        assert set(desc.keys()) == {"low", "medium", "high"}

    def test_low_description(self, settings):
        assert "₹500" in budget_band_descriptions(settings)["low"]

    def test_high_description(self, settings):
        assert "₹1,500" in budget_band_descriptions(settings)["high"]

    def test_uses_settings_values(self):
        """Custom thresholds are reflected in descriptions."""
        custom = Settings(GROQ_API_KEY="test", BUDGET_LOW_MAX=300, BUDGET_MEDIUM_MAX=900)
        desc = budget_band_descriptions(custom)
        assert "₹300" in desc["low"]
        assert "₹900" in desc["medium"]
        assert "₹900" in desc["high"]
