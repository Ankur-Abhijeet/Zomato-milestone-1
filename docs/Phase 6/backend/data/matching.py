"""Shared location and cuisine matching for filters."""

from __future__ import annotations

from data.preprocessor import normalize_city_key, resolve_city_alias
from models.restaurant import Restaurant


def matches_location(restaurant: Restaurant, query: str) -> bool:
    q = query.strip().lower()
    if not q:
        return True

    # ── Handle macro-region special queries ───────────────────────────────────
    if q == "__others__":
        city_lower = restaurant.city.lower() if restaurant.city else ""
        area_lower = restaurant.area.lower() if restaurant.area else ""
        MACRO_REGIONS = [
            "koramangala", "indiranagar", "whitefield", "marathahalli", "hsr layout", 
            "jayanagar", "jp nagar", "btm", "electronic city", "bellandur"
        ]
        for region in MACRO_REGIONS:
            if region in area_lower or region in city_lower:
                return False
        return True

    canonical = resolve_city_alias(query)
    city_key = normalize_city_key(restaurant.city)
    if canonical and (canonical in city_key or city_key in canonical):
        return True

    if restaurant.area and q in restaurant.area.lower():
        return True

    if restaurant.address and q in restaurant.address.lower():
        return True

    return q in restaurant.city.lower()


def cuisines_overlap(restaurant_cuisines: list[str], requested: list[str]) -> bool:
    """True if any requested cuisine overlaps a restaurant cuisine (substring, case-insensitive)."""
    wanted = {c.strip().lower() for c in requested if c.strip()}
    if not wanted:
        return True
    for cuisine in restaurant_cuisines:
        cuisine_lower = cuisine.lower()
        for item in wanted:
            if item in cuisine_lower or cuisine_lower in item:
                return True
    return False
