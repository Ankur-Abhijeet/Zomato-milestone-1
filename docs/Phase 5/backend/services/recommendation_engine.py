"""Phase 4: Groq LLM ranking + parse + merge + fallback."""

from __future__ import annotations

import logging
from typing import List, Optional

from config.settings import Settings, get_settings
from models.integration import IntegrationResult
from models.recommendation import RecommendationItem, RecommendationResult
from models.restaurant import Restaurant
from models.user_preferences import UserPreferences
from services.fallback import build_fallback_result
from services.llm.exceptions import (
    LLMConfigError,
    LLMError,
    LLMQuotaError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from services.llm.groq_client import GroqLLMClient
from services.response_parser import ParseError, ResponseParser

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        *,
        client: Optional[GroqLLMClient] = None,
        parser: Optional[ResponseParser] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client or GroqLLMClient(self._settings)
        self._parser = parser or ResponseParser()

    def recommend(
        self,
        integration_result: IntegrationResult,
        preferences: UserPreferences,
        *,
        force_fallback: bool = False,
    ) -> RecommendationResult:
        if integration_result.skip_llm:
            message = integration_result.user_message or "No candidates to recommend."
            return RecommendationResult.from_message(message)

        payload = integration_result.prompt_payload
        candidates = integration_result.capped_candidates
        if payload is None or not candidates:
            return RecommendationResult.from_message(
                "No prompt or candidates available for recommendation."
            )

        top_k = payload.top_k

        if force_fallback:
            return build_fallback_result(
                candidates,
                preferences,
                top_k=top_k,
                reason="forced fallback (CLI flag)",
            )

        try:
            raw = self._client.complete(payload)
            parsed = self._parser.parse(raw, candidates, top_k=top_k)
            return self._to_result(
                parsed.summary,
                parsed.recommendations,
                candidates,
                preferences,
                top_k,
            )
        except LLMQuotaError:
            raise
        except LLMConfigError:
            raise
        except ParseError as exc:
            logger.warning("LLM parse failed: %s", exc)
            return build_fallback_result(
                candidates,
                preferences,
                top_k=top_k,
                reason=f"could not parse AI response ({exc})",
            )
        except (LLMTimeoutError, LLMRateLimitError, LLMError) as exc:
            logger.warning("LLM call failed, using fallback: %s", exc)
            return build_fallback_result(
                candidates,
                preferences,
                top_k=top_k,
                reason=str(exc),
            )

    def _to_result(
        self,
        summary: Optional[str],
        parsed_items: list,
        candidates: List[Restaurant],
        preferences: UserPreferences,
        top_k: int,
    ) -> RecommendationResult:
        by_id = {r.id: r for r in candidates}
        items: List[RecommendationItem] = []

        for parsed in parsed_items:
            restaurant = by_id.get(parsed.restaurant_id)
            if restaurant is None:
                continue
            items.append(
                RecommendationItem(
                    rank=parsed.rank,
                    restaurant_id=restaurant.id,
                    name=restaurant.name,
                    cuisine=restaurant.cuisine_display,
                    rating=restaurant.rating,
                    estimated_cost=restaurant.cost_display
                    or (
                        f"₹{restaurant.cost_inr}"
                        if restaurant.cost_inr is not None
                        else None
                    ),
                    location=restaurant.location_display,
                    explanation=parsed.explanation,
                    is_ai_generated=True,
                )
            )

        if not items:
            return build_fallback_result(
                candidates,
                preferences,
                top_k=top_k,
                reason="no valid recommendations after validation",
            )

        return RecommendationResult(
            summary=summary,
            recommendations=items,
            used_fallback=False,
            top_k=top_k,
        )
