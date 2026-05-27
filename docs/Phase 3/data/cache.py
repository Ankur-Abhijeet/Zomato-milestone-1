"""Local Parquet cache for preprocessed restaurants."""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

import pandas as pd

from models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def cache_exists(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def save_restaurants(restaurants: list[Restaurant], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".parquet.tmp")
    records = [r.model_dump() for r in restaurants]
    df = pd.DataFrame(records)
    df.to_parquet(tmp_path, index=False)
    tmp_path.replace(path)
    logger.info("Wrote %d restaurants to cache %s", len(restaurants), path)


def load_restaurants(path: Path) -> list[Restaurant]:
    if not cache_exists(path):
        raise FileNotFoundError(f"Cache not found: {path}")
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        raise ValueError(f"Corrupt cache at {path}: {exc}") from exc

    if df.empty:
        raise ValueError(f"Cache at {path} contains no rows")

    df = df.where(pd.notnull(df), None)
    restaurants = [
        Restaurant.model_validate(_sanitize_record(row))
        for row in df.to_dict("records")
    ]
    return restaurants


def _sanitize_record(row: dict[str, Any]) -> dict[str, Any]:
    """Coerce pandas/parquet NaN floats back to None for Pydantic."""
    cleaned = dict(row)
    for key in ("cost_inr", "rating", "votes"):
        value = cleaned.get(key)
        if isinstance(value, float) and math.isnan(value):
            cleaned[key] = None
    band = cleaned.get("budget_band")
    if band is not None and (isinstance(band, float) and math.isnan(band)):
        cleaned["budget_band"] = None
    return cleaned


def invalidate_cache(path: Path) -> None:
    if path.exists():
        path.unlink()
        logger.warning("Removed invalid cache: %s", path)
