from __future__ import annotations

import argparse
from typing import Optional

from input.adapters.argparse_adapter import preferences_from_namespace
from input.adapters.cli import prompt_preferences
from input.adapters.json_adapter import preferences_from_json
from models.user_preferences import UserPreferences


def collect_preferences(
    *,
    interactive: bool = False,
    json_payload: Optional[str] = None,
    namespace: Optional[argparse.Namespace] = None,
) -> UserPreferences:
    """
    Collect preferences from the first available source:
    JSON string, argparse namespace, or interactive CLI.
    """
    if json_payload is not None:
        return preferences_from_json(json_payload)
    if namespace is not None:
        return preferences_from_namespace(namespace)
    if interactive:
        return prompt_preferences()
    raise ValueError("No input source provided for preferences")


__all__ = [
    "collect_preferences",
    "prompt_preferences",
    "preferences_from_json",
    "preferences_from_namespace",
]
