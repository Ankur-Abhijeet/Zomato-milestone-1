"""Build UserPreferences from argparse namespace flags."""

from __future__ import annotations

import argparse
from typing import Any, Dict, Optional

from input.validator import validate_preferences
from models.user_preferences import UserPreferences


def preferences_from_namespace(namespace: argparse.Namespace) -> UserPreferences:
    raw = namespace_to_dict(namespace)
    return validate_preferences(raw)


def namespace_to_dict(namespace: argparse.Namespace) -> Dict[str, Any]:
    """Map CLI flags to a preference payload (omitted optionals stay unset)."""
    data: Dict[str, Any] = {}

    if getattr(namespace, "location", None) is not None:
        data["location"] = namespace.location

    if getattr(namespace, "budget", None) is not None:
        data["budget"] = namespace.budget

    cuisines = getattr(namespace, "cuisines", None)
    if cuisines is not None:
        data["cuisines"] = cuisines

    min_rating = getattr(namespace, "min_rating", None)
    if min_rating is not None:
        data["min_rating"] = min_rating

    additional = getattr(namespace, "additional", None)
    if additional is not None:
        data["additional"] = additional

    return data


def add_preference_arguments(
    parser: argparse.ArgumentParser,
    *,
    require_location: bool = True,
    default_location: Optional[str] = None,
) -> None:
    """Attach standard preference flags to an argparse parser."""
    parser.add_argument(
        "--location",
        required=require_location and default_location is None,
        default=default_location,
        help="City or area (required)",
    )
    parser.add_argument(
        "--budget",
        choices=["low", "medium", "high"],
        default=None,
        help="Budget band (default: medium)",
    )
    parser.add_argument(
        "--cuisines",
        default=None,
        help="Comma-separated cuisines (default: any)",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=None,
        dest="min_rating",
        help="Minimum rating 0–5 (default: 3.0)",
    )
    parser.add_argument(
        "--additional",
        default=None,
        help="Free-text preferences (family-friendly, quick service, …)",
    )
