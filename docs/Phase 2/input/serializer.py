"""Stable serialization of UserPreferences for filter + prompt layers."""

from __future__ import annotations

import json
from typing import Any, Dict

from models.user_preferences import UserPreferences


class PreferenceSerializer:
    """Convert preferences to stable dict/JSON (Phase 3 consumes this shape)."""

    @staticmethod
    def to_dict(preferences: UserPreferences) -> Dict[str, Any]:
        return preferences.model_dump(mode="json")

    @staticmethod
    def to_json(preferences: UserPreferences, *, indent: int = 2) -> str:
        return json.dumps(PreferenceSerializer.to_dict(preferences), indent=indent)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Return normalized dict without re-validation (use validate_preferences first)."""
        return UserPreferences.model_validate(data).model_dump(mode="json")
