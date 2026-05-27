"""Orchestrate filter → cap → prompt (Phase 3)."""

from __future__ import annotations

import logging
from typing import List, Optional

from config.settings import Settings, get_settings
from data.repository import RestaurantRepository
from models.integration import IntegrationResult
from models.restaurant import Restaurant
from models.user_preferences import UserPreferences
from services.candidate_selector import select_candidates
from services.filter import HardConstraintFilter
from services.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class IntegrationService:
    def __init__(
        self,
        repository: RestaurantRepository,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings or get_settings()
        self._filter = HardConstraintFilter()
        self._prompt_builder = PromptBuilder(self._settings)

    def run(
        self,
        preferences: UserPreferences,
        *,
        candidate_cap: Optional[int] = None,
        top_k: Optional[int] = None,
    ) -> IntegrationResult:
        all_restaurants = self._repository.all()

        filter_result = self._filter.filter(all_restaurants, preferences)

        if filter_result.is_empty:
            hints = filter_result.relaxation_hints()
            message = (
                "No restaurants match your filters. "
                + " ".join(hints)
                if hints
                else "No restaurants match your filters. Try broadening your search."
            )
            logger.info("Empty filter result for location=%s", preferences.location)
            return IntegrationResult(
                filter_result=filter_result,
                capped_candidates=[],
                prompt_payload=None,
                skip_llm=True,
                user_message=message,
            )

        capped = select_candidates(
            filter_result.candidates,
            cap=candidate_cap,
            settings=self._settings,
        )

        effective_top_k = top_k if top_k is not None else self._settings.recommendation_top_k
        prompt_payload = self._prompt_builder.build(
            preferences,
            capped,
            top_k=effective_top_k,
        )

        logger.info(
            "Integration complete: %d filtered → %d capped for LLM",
            len(filter_result.candidates),
            len(capped),
        )

        return IntegrationResult(
            filter_result=filter_result,
            capped_candidates=capped,
            prompt_payload=prompt_payload,
            skip_llm=False,
            user_message=None,
        )
