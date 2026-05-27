"""Validate raw preference payloads into UserPreferences."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from config.settings import get_settings
from models.user_preferences import UserPreferences

RawPreferences = Dict[str, Any]


class PreferenceValidationError(ValueError):
    """Raised when user input fails validation with human-readable detail."""

    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        self.errors = errors or []
        detail = message
        if self.errors:
            detail = f"{message}\n" + "\n".join(f"  - {e}" for e in self.errors)
        super().__init__(detail)


def validate_preferences(data: Union[RawPreferences, UserPreferences]) -> UserPreferences:
    """
    Validate and normalize a preference dict or return an existing model unchanged.
    """
    if isinstance(data, UserPreferences):
        return data

    if not isinstance(data, dict):
        raise PreferenceValidationError(
            "Preferences must be a JSON object",
            ["Expected object with keys: location, budget, cuisines, min_rating, additional"],
        )

    payload = _apply_defaults(dict(data))
    payload = _truncate_additional(payload)

    try:
        return UserPreferences.model_validate(payload)
    except ValidationError as exc:
        raise PreferenceValidationError(
            "Invalid preferences",
            _format_pydantic_errors(exc),
        ) from exc


def _apply_defaults(data: RawPreferences) -> RawPreferences:
    settings = get_settings()
    if data.get("min_rating") is None and "min_rating" not in data:
        data["min_rating"] = settings.default_min_rating
    if data.get("budget") is None and "budget" not in data:
        data["budget"] = settings.default_budget
    return data


def _truncate_additional(data: RawPreferences) -> RawPreferences:
    additional = data.get("additional")
    if additional is None:
        return data
    max_len = get_settings().additional_max_length
    text = str(additional)
    if len(text) > max_len:
        data["additional"] = text[:max_len]
    return data


def _format_pydantic_errors(exc: ValidationError) -> List[str]:
    messages: List[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()))
        msg = err.get("msg", "invalid value")
        if loc:
            messages.append(f"{loc}: {msg}")
        else:
            messages.append(str(msg))
    return messages
