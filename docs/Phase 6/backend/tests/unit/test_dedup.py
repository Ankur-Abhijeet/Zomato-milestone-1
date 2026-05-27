"""Unit tests for _deduplicate() — Phase 6."""

from __future__ import annotations

import pytest

from api.schemas.response import RecommendationItemDTO, _deduplicate


def _item(rank: int, name: str, location: str = "Bangalore", **kw) -> RecommendationItemDTO:
    return RecommendationItemDTO(
        rank=rank,
        id=f"id-{rank}",
        name=name,
        cuisine="Various",
        rating=4.0,
        estimated_cost="1,000",
        location=location,
        explanation="Test explanation",
        is_ai_generated=True,
        **kw,
    )


class TestDeduplicate:
    def test_single_item_unchanged(self):
        items = [_item(1, "Solo Bistro")]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 1
        assert removed == 0
        assert deduped[0].rank == 1

    def test_no_duplicates_unchanged(self):
        items = [_item(1, "Alpha"), _item(2, "Beta"), _item(3, "Gamma")]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 3
        assert removed == 0
        assert [i.rank for i in deduped] == [1, 2, 3]

    def test_all_same_name_location_keeps_rank1(self):
        """Bellandur scenario: LLM returns 3× same outlet."""
        items = [
            _item(1, "Chili's", "Bellandur, Bangalore"),
            _item(2, "Chili's", "Bellandur, Bangalore"),
            _item(3, "Chili's", "Bellandur, Bangalore"),
        ]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 1
        assert removed == 2
        assert deduped[0].rank == 1
        assert deduped[0].name == "Chili's"

    def test_mixed_dupes_and_unique(self):
        items = [
            _item(1, "Chili's", "Bellandur"),
            _item(2, "Chili's", "Bellandur"),   # dup of rank 1
            _item(3, "Bombay Brasserie", "Bellandur"),
            _item(4, "Chili's", "Bellandur"),   # dup of rank 1
            _item(5, "Nook", "Bellandur"),
        ]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 3
        assert removed == 2
        # Ranks are re-numbered 1, 2, 3
        assert [i.rank for i in deduped] == [1, 2, 3]
        assert [i.name for i in deduped] == ["Chili's", "Bombay Brasserie", "Nook"]

    def test_case_insensitive_dedup(self):
        """Name casing should not matter."""
        items = [
            _item(1, "THE COFFEE HOUSE", "MG Road"),
            _item(2, "The Coffee House", "MG Road"),
        ]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 1
        assert removed == 1

    def test_same_name_different_location_kept(self):
        """Same brand, different area → both are kept."""
        items = [
            _item(1, "Chili's", "Koramangala"),
            _item(2, "Chili's", "Indiranagar"),
        ]
        deduped, removed = _deduplicate(items)
        assert len(deduped) == 2
        assert removed == 0

    def test_ranks_renumbered_contiguously(self):
        """After dedup, ranks must be 1, 2, 3, … without gaps."""
        items = [
            _item(1, "A", "X"),
            _item(2, "A", "X"),   # dup
            _item(3, "B", "X"),
            _item(4, "C", "X"),
        ]
        deduped, removed = _deduplicate(items)
        assert [i.rank for i in deduped] == [1, 2, 3]
        assert removed == 1

    def test_empty_list(self):
        deduped, removed = _deduplicate([])
        assert deduped == []
        assert removed == 0
