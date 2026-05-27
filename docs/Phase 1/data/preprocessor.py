"""Normalize raw Hugging Face rows into Restaurant records."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from config.settings import Settings
from models.restaurant import BudgetBand, Restaurant

# City aliases -> canonical lowercase key used for matching
CITY_ALIASES: dict[str, str] = {
    "bangalore": "bangalore",
    "bangalore.": "bangalore",
    "bengaluru": "bangalore",
    "banglore": "bangalore",
    "bengalore": "bangalore",
    "btm bangalore": "bangalore",
    "delhi": "delhi",
    "new delhi": "delhi",
    "ncr": "delhi",
    "gurgaon": "gurgaon",
    "gurugram": "gurgaon",
    "noida": "noida",
    "mumbai": "mumbai",
    "bombay": "mumbai",
    "hyderabad": "hyderabad",
    "chennai": "chennai",
    "madras": "chennai",
    "kolkata": "kolkata",
    "calcutta": "kolkata",
    "pune": "pune",
}

COST_COLUMN = "approx_cost(for two people)"
REQUIRED_RAW_COLUMNS = ("name", "address", "cuisines")

_RATING_PATTERN = re.compile(r"(\d+(?:\.\d+)?)")
_COST_DIGITS = re.compile(r"\d+")
_CUISINE_SPLIT = re.compile(r"[,/&|]+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(str(value).strip().split())


def normalize_city_key(city: str) -> str:
    key = normalize_text(city).lower()
    return CITY_ALIASES.get(key, key)


def resolve_city_alias(query: str) -> str:
    """Map user-facing city names to canonical match key."""
    return normalize_city_key(query)


def parse_rating(raw: Any) -> float | None:
    if raw is None:
        return None
    text = normalize_text(str(raw))
    if not text or text.upper() == "NEW":
        return None
    match = _RATING_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1))
    if value < 0 or value > 5:
        return None
    return round(value, 2)


def parse_cost_inr(raw: Any) -> tuple[int | None, str | None]:
    if raw is None:
        return None, None
    text = normalize_text(str(raw))
    if not text or text.lower() in {"-", "na", "n/a"}:
        return None, None

    numbers = [int(n) for n in _COST_DIGITS.findall(text.replace(",", ""))]
    if not numbers:
        return None, text

    cost = max(numbers) if len(numbers) > 1 else numbers[0]
    return cost, text


def parse_cuisines(raw: Any) -> list[str]:
    if not raw:
        return []
    parts = _CUISINE_SPLIT.split(str(raw))
    cuisines: list[str] = []
    seen: set[str] = set()
    for part in parts:
        name = normalize_text(part)
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            seen.add(key)
            cuisines.append(name)
    return cuisines


def extract_city_from_address(address: str | None) -> str:
    if not address:
        return ""
    parts = [normalize_text(p) for p in address.split(",") if normalize_text(p)]
    if not parts:
        return ""
    return parts[-1]


def parse_yes_no(raw: Any) -> bool | None:
    if raw is None:
        return None
    text = normalize_text(str(raw)).lower()
    if text in {"yes", "true", "1"}:
        return True
    if text in {"no", "false", "0"}:
        return False
    return None


def _stable_id(name: str, address: str, url: str | None) -> str:
    payload = f"{name}|{address}|{url or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def row_to_restaurant(row: dict[str, Any], settings: Settings) -> Restaurant | None:
    name = normalize_text(row.get("name"))
    address = normalize_text(row.get("address"))
    if not name:
        return None

    city_raw = extract_city_from_address(address)
    city = normalize_text(city_raw) or "Unknown"
    area = normalize_text(row.get("location")) or None

    cost_inr, cost_display = parse_cost_inr(row.get(COST_COLUMN))
    budget_band: BudgetBand | None = settings.cost_to_budget_band(cost_inr)

    cuisines = parse_cuisines(row.get("cuisines"))
    rating = parse_rating(row.get("rate"))

    votes_raw = row.get("votes")
    votes: int | None = None
    if votes_raw is not None:
        try:
            votes = int(votes_raw)
        except (TypeError, ValueError):
            votes = None

    extras = {
        "listed_in_type": row.get("listed_in(type)"),
        "listed_in_city": row.get("listed_in(city)"),
        "menu_item": row.get("menu_item"),
    }

    return Restaurant(
        id=_stable_id(name, address, row.get("url")),
        name=name,
        city=city,
        area=area,
        address=address or None,
        cuisines=cuisines,
        cost_display=cost_display or (str(cost_inr) if cost_inr is not None else None),
        cost_inr=cost_inr,
        budget_band=budget_band,
        rating=rating,
        votes=votes,
        rest_type=normalize_text(row.get("rest_type")) or None,
        dish_liked=normalize_text(row.get("dish_liked")) or None,
        online_order=parse_yes_no(row.get("online_order")),
        book_table=parse_yes_no(row.get("book_table")),
        url=row.get("url"),
        extras={k: v for k, v in extras.items() if v},
    )


def preprocess_rows(
    rows: list[dict[str, Any]], settings: Settings
) -> tuple[list[Restaurant], dict[str, int]]:
    stats = {
        "input_rows": len(rows),
        "dropped_missing_name": 0,
        "kept": 0,
        "missing_rating": 0,
        "missing_cost": 0,
    }
    restaurants: list[Restaurant] = []

    for row in rows:
        restaurant = row_to_restaurant(row, settings)
        if restaurant is None:
            stats["dropped_missing_name"] += 1
            continue
        if restaurant.rating is None:
            stats["missing_rating"] += 1
        if restaurant.cost_inr is None:
            stats["missing_cost"] += 1
        restaurants.append(restaurant)
        stats["kept"] += 1

    return restaurants, stats


def validate_raw_schema(columns: list[str]) -> None:
    missing = [col for col in REQUIRED_RAW_COLUMNS if col not in columns]
    if missing:
        raise ValueError(
            f"Dataset schema missing required columns: {missing}. "
            f"Found columns: {columns}"
        )
