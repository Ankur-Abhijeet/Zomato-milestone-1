"""Interactive CLI adapter for user preferences."""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.prompt import Confirm, FloatPrompt, Prompt

from config.settings import get_settings
from input.validator import PreferenceValidationError, validate_preferences
from models.user_preferences import BUDGET_VALUES, UserPreferences

console = Console()


def prompt_preferences() -> UserPreferences:
    """Prompt the user for all preference fields with validation retries."""
    settings = get_settings()
    console.print("\n[bold]Restaurant preferences[/bold]")
    console.print(
        "[dim]Press Enter to accept defaults shown in brackets. "
        "Ctrl+C to cancel.[/dim]\n"
    )

    while True:
        location = Prompt.ask("Location (city or area)", default="")
        location = location.strip()
        if location:
            break
        console.print("[red]Location is required.[/red]")

    budget = _prompt_budget(settings.default_budget)
    cuisines_raw = Prompt.ask(
        "Cuisines (comma-separated, or leave empty for any)",
        default="",
    )
    min_rating = FloatPrompt.ask(
        "Minimum rating (0–5)",
        default=settings.default_min_rating,
    )
    additional: Optional[str] = None
    if Confirm.ask("Add other preferences (family-friendly, quick service, …)?", default=False):
        additional = Prompt.ask("Describe what you're looking for", default="")

    raw = {
        "location": location,
        "budget": budget,
        "cuisines": cuisines_raw,
        "min_rating": min_rating,
        "additional": additional or None,
    }

    try:
        return validate_preferences(raw)
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        raise


def _prompt_budget(default: str) -> str:
    allowed = "/".join(BUDGET_VALUES)
    while True:
        value = Prompt.ask(
            f"Budget ({allowed})",
            default=default,
        ).strip().lower()
        if not value:
            return default
        if value in BUDGET_VALUES:
            return value
        console.print(
            f"[red]Invalid budget. Choose one of: {', '.join(BUDGET_VALUES)}[/red]"
        )
