"""Budget band utility helpers (Phase 5c).

Pure functions — no I/O, no side effects — safe to call from API routes,
CLI commands, or the frontend (via /meta endpoint).
"""

from __future__ import annotations

from typing import Literal

from config.settings import Settings, get_settings

BudgetBand = Literal["low", "medium", "high"]

# Canonical descriptions kept in sync with Settings defaults and frontend copy.
_BAND_LABELS: dict[BudgetBand, str] = {
    "low":    "low",
    "medium": "medium",
    "high":   "high",
}


def cost_inr_to_budget_hint(cost_inr: int, settings: Settings | None = None) -> str:
    """Return a human-readable budget-band hint for a given per-person cost.

    Examples
    --------
    >>> cost_inr_to_budget_hint(400)   # "~₹400 → low budget (≤ ₹500)"
    >>> cost_inr_to_budget_hint(1200)  # "~₹1,200 → medium budget (≤ ₹1,500)"
    >>> cost_inr_to_budget_hint(2000)  # "~₹2,000 → high budget (> ₹1,500)"
    """
    cfg = settings or get_settings()
    band = cfg.cost_to_budget_band(cost_inr)
    if band is None:
        return f"~₹{cost_inr:,} — band undetermined"

    if band == "low":
        threshold = f"≤ ₹{cfg.budget_low_max:,}"
    elif band == "medium":
        threshold = f"≤ ₹{cfg.budget_medium_max:,}"
    else:
        threshold = f"> ₹{cfg.budget_medium_max:,}"

    return f"~₹{cost_inr:,} → {band} budget ({threshold} per person)"


def budget_band_descriptions(settings: Settings | None = None) -> dict[BudgetBand, str]:
    """Return the canonical band → description mapping used by the meta endpoint.

    Reads thresholds from Settings so they stay in sync with filter logic.
    """
    cfg = settings or get_settings()
    return {
        "low":    f"≤ ₹{cfg.budget_low_max:,} per person",
        "medium": f"≤ ₹{cfg.budget_medium_max:,} per person",
        "high":   f"> ₹{cfg.budget_medium_max:,} per person",
    }
