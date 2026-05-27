"""Parse and validate Groq JSON responses against candidate restaurants."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from models.restaurant import Restaurant

logger = logging.getLogger(__name__)

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


class ParseError(ValueError):
    """LLM response could not be parsed or validated."""


class ParsedRecommendation:
    __slots__ = ("rank", "restaurant_id", "name", "explanation")

    def __init__(
        self,
        rank: int,
        restaurant_id: str,
        name: str,
        explanation: str,
    ) -> None:
        self.rank = rank
        self.restaurant_id = restaurant_id
        self.name = name
        self.explanation = explanation


class ParsedLLMResponse:
    __slots__ = ("summary", "recommendations")

    def __init__(
        self,
        summary: Optional[str],
        recommendations: List[ParsedRecommendation],
    ) -> None:
        self.summary = summary
        self.recommendations = recommendations


class ResponseParser:
    def parse(
        self,
        raw_text: str,
        candidates: List[Restaurant],
        *,
        top_k: int,
    ) -> ParsedLLMResponse:
        data = self._load_json(raw_text)
        summary = _coerce_optional_str(
            data.get("summary") or data.get("overview") or data.get("intro")
        )
        raw_items = data.get("recommendations") or data.get("results") or data.get("items")
        if raw_items is None:
            raise ParseError("Response JSON missing 'recommendations' array")

        if not isinstance(raw_items, list):
            raise ParseError("'recommendations' must be a JSON array")

        by_id = {r.id: r for r in candidates}
        by_name = {_normalize_key(r.name): r for r in candidates}

        parsed_items: List[ParsedRecommendation] = []
        seen_ids: set[str] = set()

        for index, item in enumerate(raw_items):
            if not isinstance(item, dict):
                logger.debug("Skipping non-object recommendation at index %d", index)
                continue

            restaurant = self._match_candidate(item, by_id, by_name)
            if restaurant is None:
                logger.warning(
                    "Dropping hallucinated recommendation: %s",
                    item.get("name") or item.get("id"),
                )
                continue

            if restaurant.id in seen_ids:
                logger.debug("Skipping duplicate recommendation id=%s", restaurant.id)
                continue
            seen_ids.add(restaurant.id)

            rank = _coerce_rank(item.get("rank"), default=len(parsed_items) + 1)
            explanation = _coerce_optional_str(
                item.get("explanation") or item.get("reason") or item.get("why")
            ) or _default_explanation(restaurant)

            parsed_items.append(
                ParsedRecommendation(
                    rank=rank,
                    restaurant_id=restaurant.id,
                    name=restaurant.name,
                    explanation=explanation,
                )
            )

        if not parsed_items:
            raise ParseError("No valid recommendations after matching to candidates")

        parsed_items.sort(key=lambda x: (x.rank, x.name.lower()))
        for idx, item in enumerate(parsed_items[:top_k], start=1):
            item.rank = idx

        return ParsedLLMResponse(
            summary=summary,
            recommendations=parsed_items[:top_k],
        )

    def _match_candidate(
        self,
        item: Dict[str, Any],
        by_id: Dict[str, Restaurant],
        by_name: Dict[str, Restaurant],
    ) -> Optional[Restaurant]:
        raw_id = item.get("id") or item.get("restaurant_id")
        if raw_id is not None:
            match = by_id.get(str(raw_id).strip())
            if match:
                return match

        raw_name = item.get("name") or item.get("restaurant_name")
        if raw_name:
            return by_name.get(_normalize_key(str(raw_name)))

        return None

    @staticmethod
    def _load_json(raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        fence = _JSON_FENCE.search(text)
        if fence:
            text = fence.group(1).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Invalid JSON from LLM: {exc}") from exc
        if not isinstance(data, dict):
            raise ParseError("LLM JSON root must be an object")
        return data


def _normalize_key(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _coerce_rank(value: Any, default: int) -> int:
    try:
        rank = int(value)
        return rank if rank > 0 else default
    except (TypeError, ValueError):
        return default


def _coerce_optional_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _default_explanation(restaurant: Restaurant) -> str:
    rating = f"{restaurant.rating:.1f}/5" if restaurant.rating is not None else "a solid rating"
    return (
        f"{restaurant.name} in {restaurant.location_display} serves "
        f"{restaurant.cuisine_display} with {rating}."
    )
