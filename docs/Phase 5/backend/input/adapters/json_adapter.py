"""JSON / dict adapter for preferences (API-style payloads)."""

from __future__ import annotations

import json
from typing import Any, Dict

from input.validator import PreferenceValidationError, validate_preferences
from models.user_preferences import UserPreferences


def preferences_from_json(payload: str) -> UserPreferences:
    """Parse a JSON string into validated UserPreferences."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise PreferenceValidationError(
            "Malformed JSON",
            [str(exc)],
        ) from exc

    if not isinstance(data, dict):
        raise PreferenceValidationError(
            "Malformed JSON",
            ["Root value must be a JSON object"],
        )

    return validate_preferences(data)


def preferences_from_dict(data: Dict[str, Any]) -> UserPreferences:
    return validate_preferences(data)
