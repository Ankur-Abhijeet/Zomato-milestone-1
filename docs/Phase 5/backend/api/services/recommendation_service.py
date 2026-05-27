"""Thin orchestration service for the recommendations endpoint (Phase 5a).

Delegates all business logic to the existing Phase 3/4 core:
  - IntegrationService  (filter → cap → prompt)
  - RecommendationEngine (Groq LLM → parse → fallback)

The Groq call is offloaded to a thread-pool via asyncio.to_thread() so the
FastAPI event loop is never blocked by synchronous I/O.
"""

from __future__ import annotations

import asyncio
import logging

from config.settings import Settings
from data.repository import RestaurantRepository
from api.schemas.request import RecommendRequest
from api.schemas.response import RecommendResponse
from input.validator import validate_preferences
from services.integration import IntegrationService
from services.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class RecommendationService:
    """Thin HTTP-to-core bridge; owns no business logic."""

    def __init__(
        self,
        repository: RestaurantRepository,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._settings = settings

    async def recommend(self, body: RecommendRequest) -> RecommendResponse:
        """Run the full pipeline asynchronously and return a response DTO."""
        # 1. Validate + normalise preferences (reuses Phase 2 validator)
        prefs = validate_preferences(
            {
                "location": body.location,
                "budget": body.budget,
                "cuisines": body.cuisines,
                "min_rating": body.min_rating,
                "additional": body.additional,
            }
        )

        # 2. Phase 3: filter → cap → prompt
        integration_service = IntegrationService(self._repository, self._settings)
        integration = await asyncio.to_thread(
            integration_service.run, prefs, top_k=body.top_k
        )

        if integration.skip_llm:
            logger.info(
                "Skipping LLM for location=%s: %s",
                prefs.location,
                integration.user_message,
            )
            return RecommendResponse.from_empty(integration)

        # 3. Phase 4: Groq LLM ranking (offloaded to thread-pool)
        engine = RecommendationEngine(self._settings)
        result = await asyncio.to_thread(engine.recommend, integration, prefs)

        logger.info(
            "Recommendation complete: %d results, fallback=%s",
            len(result.recommendations),
            result.used_fallback,
        )

        return RecommendResponse.from_domain(
            result,
            integration.filter_result,
            len(integration.capped_candidates),
        )
