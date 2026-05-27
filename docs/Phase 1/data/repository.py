"""In-memory restaurant store with hard-constraint filtering."""

from __future__ import annotations

import logging
from typing import Literal

from config.settings import Settings, get_settings
from data import cache as cache_module
from data.loader import DatasetLoadError, download_raw_rows
from data.matching import cuisines_overlap, matches_location
from data.preprocessor import preprocess_rows
from models.restaurant import BudgetBand, Restaurant

logger = logging.getLogger(__name__)

BudgetFilter = Literal["low", "medium", "high"]


class DataNotLoadedError(RuntimeError):
    """Raised when the repository is queried before load()."""


class RestaurantRepository:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._restaurants: list[Restaurant] = []
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded and bool(self._restaurants)

    @property
    def count(self) -> int:
        return len(self._restaurants)

    def load(self, *, force_refresh: bool = False) -> None:
        """Load restaurants from cache or Hugging Face (idempotent)."""
        if self._loaded and not force_refresh:
            logger.debug("Restaurant data already loaded (%d rows)", self.count)
            return

        cache_path = self._settings.restaurant_cache_path

        if not force_refresh and cache_module.cache_exists(cache_path):
            try:
                self._restaurants = cache_module.load_restaurants(cache_path)
                self._loaded = True
                logger.info(
                    "Loaded %d restaurants from cache %s",
                    self.count,
                    cache_path,
                )
                return
            except (ValueError, FileNotFoundError) as exc:
                logger.warning("Cache invalid, will re-download: %s", exc)
                cache_module.invalidate_cache(cache_path)

        try:
            raw_rows = download_raw_rows(self._settings)
        except DatasetLoadError:
            raise

        restaurants, stats = preprocess_rows(raw_rows, self._settings)
        if not restaurants:
            raise DatasetLoadError(
                "No valid restaurants after preprocessing. "
                f"Stats: {stats}"
            )

        logger.info("Preprocessing stats: %s", stats)
        cache_module.save_restaurants(restaurants, cache_path)
        self._restaurants = restaurants
        self._loaded = True

    def all(self) -> list[Restaurant]:
        self._ensure_loaded()
        return list(self._restaurants)

    def find_by_filters(
        self,
        *,
        location: str | None = None,
        budget: BudgetFilter | None = None,
        cuisines: list[str] | None = None,
        min_rating: float | None = None,
    ) -> list[Restaurant]:
        """
        Apply hard constraints (Phase 3 will call this).

        - location: matches city (with aliases) or area substring
        - budget: exact band match; unknown cost excluded when budget set
        - cuisines: any overlap (case-insensitive); empty = any
        - min_rating: inclusive >= threshold; unrated rows excluded
        """
        self._ensure_loaded()
        results = self._restaurants

        if location:
            results = [r for r in results if matches_location(r, location)]

        if min_rating is not None:
            results = [
                r
                for r in results
                if r.rating is not None and r.rating >= min_rating
            ]

        if budget is not None:
            results = [
                r for r in results if r.budget_band is not None and r.budget_band == budget
            ]

        if cuisines:
            results = [r for r in results if cuisines_overlap(r.cuisines, cuisines)]

        return results

    def _ensure_loaded(self) -> None:
        if not self.is_loaded:
            raise DataNotLoadedError(
                "Restaurant data is not loaded. Call load() first."
            )
