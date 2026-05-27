"""Build grounded LLM prompt payloads from preferences and candidates."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from config.settings import Settings, get_settings
from input.serializer import PreferenceSerializer
from models.integration import PromptPayload
from models.restaurant import Restaurant
from models.user_preferences import UserPreferences

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a restaurant recommendation assistant for Zomato-style dining in India.

Rules:
1. Recommend ONLY from the numbered candidate list provided. Never invent restaurants.
2. Use exact candidate "id" and "name" values in your response.
3. Rank at most {top_k} restaurants (or fewer if fewer candidates exist).
4. For each pick, explain why it matches the user's preferences and note trade-offs when relevant.
5. Apply soft preferences from "additional" when ranking among valid candidates.
6. If candidates are a weak fit, say so honestly rather than overstating the match.
7. Respond with valid JSON only, using this schema:
{{
  "summary": "optional short overview of top picks",
  "recommendations": [
    {{
      "rank": 1,
      "id": "candidate id from the list",
      "name": "exact name from the list",
      "explanation": "why this restaurant fits"
    }}
  ]
}}"""


class PromptBuilder:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def build(
        self,
        preferences: UserPreferences,
        candidates: List[Restaurant],
        *,
        top_k: int | None = None,
    ) -> PromptPayload:
        top_k = top_k if top_k is not None else self._settings.recommendation_top_k
        top_k = min(top_k, len(candidates)) if candidates else top_k

        compact = [self._compact_row(r) for r in candidates]
        prefs_dict = PreferenceSerializer.to_dict(preferences)

        system_message = SYSTEM_PROMPT_TEMPLATE.format(top_k=top_k)
        user_message = self._build_user_message(
            preferences=preferences,
            prefs_dict=prefs_dict,
            candidates=compact,
            top_k=top_k,
        )

        payload = PromptPayload(
            system_message=system_message,
            user_message=user_message,
            candidates=compact,
            top_k=top_k,
            preferences=prefs_dict,
            metadata={
                "candidate_count": len(candidates),
                "total_available": len(candidates),
            },
        )

        if self._settings.log_prompts:
            logger.info(
                "Prompt payload built: %d candidates, top_k=%d, ~%d chars user message",
                len(candidates),
                top_k,
                len(user_message),
            )
            logger.debug("System message:\n%s", system_message)
            logger.debug("User message:\n%s", user_message)

        return payload

    def _build_user_message(
        self,
        *,
        preferences: UserPreferences,
        prefs_dict: Dict[str, Any],
        candidates: List[Dict[str, Any]],
        top_k: int,
    ) -> str:
        prefs_json = json.dumps(prefs_dict, ensure_ascii=False, indent=2)
        candidates_json = json.dumps(candidates, ensure_ascii=False, indent=2)

        additional_section = ""
        if preferences.additional:
            additional_section = (
                f"\nSoft preferences (use when ranking): {preferences.additional}\n"
            )

        return f"""## User preferences
{prefs_json}
{additional_section}
## Candidate restaurants (rank ONLY from this list; {len(candidates)} shown)
Each entry has a unique "id" — use it to disambiguate duplicate names.

{candidates_json}

## Task
Rank the best {top_k} restaurant(s) for these preferences (at most {min(top_k, len(candidates))}).
Return JSON matching the schema in the system instructions."""

    def _compact_row(self, restaurant: Restaurant) -> Dict[str, Any]:
        max_len = self._settings.prompt_field_max_length
        notes_parts: List[str] = []
        if restaurant.rest_type:
            notes_parts.append(restaurant.rest_type)
        if restaurant.dish_liked:
            notes_parts.append(self._truncate(restaurant.dish_liked, max_len))

        row: Dict[str, Any] = {
            "id": restaurant.id,
            "name": restaurant.name,
            "location": restaurant.location_display,
            "cuisines": restaurant.cuisine_display,
            "rating": restaurant.rating,
            "cost": restaurant.cost_display or (
                str(restaurant.cost_inr) if restaurant.cost_inr is not None else None
            ),
            "budget_band": restaurant.budget_band,
        }
        if notes_parts:
            row["notes"] = self._truncate("; ".join(notes_parts), max_len)

        return {k: v for k, v in row.items() if v is not None}

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        text = text.strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"
