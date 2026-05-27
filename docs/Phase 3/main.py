import argparse
import sys
from rich.console import Console
from rich.table import Table
from config.settings import get_settings
from data.repository import RestaurantRepository
from input.adapters.argparse_adapter import add_preference_arguments, preferences_from_namespace
from input.adapters.cli import prompt_preferences
from input.adapters.json_adapter import preferences_from_json
from input.validator import PreferenceValidationError
from services.integration import IntegrationService

console = Console()

def _print_filter_stats(result) -> None:
    counts = result.filter_result.step_counts
    console.print(
        f"[bold]Filter pipeline stats:[/bold] {counts.initial} initial → "
        f"{counts.after_location} location → "
        f"{counts.after_rating} rating → "
        f"{counts.after_budget} budget → "
        f"{counts.after_cuisine} cuisine"
    )
    console.print(
        f"[bold]Capped for LLM:[/bold] {len(result.capped_candidates)} candidates "
        f"(cap limit: {get_settings().candidate_cap})"
    )

def _print_sample(restaurants: list, limit: int = 5) -> None:
    table = Table(title=f"Sample matches (showing up to {limit})")
    table.add_column("Name", style="cyan")
    table.add_column("Location")
    table.add_column("Cuisines")
    table.add_column("Rating", justify="right")
    table.add_column("Cost")
    table.add_column("Band")

    for restaurant in restaurants[:limit]:
        rating = f"{restaurant.rating:.1f}" if restaurant.rating is not None else "—"
        cost = restaurant.cost_display or "—"
        band = restaurant.budget_band or "—"
        table.add_row(
            restaurant.name,
            restaurant.location_display,
            restaurant.cuisine_display[:40],
            rating,
            cost,
            band,
        )
    console.print(table)
    if len(restaurants) > limit:
        console.print(f"[dim]… and {len(restaurants) - limit} more[/dim]")

def main():
    parser = argparse.ArgumentParser(description="Phase 3: Integration & Hard Constraints Filter")
    parser.add_argument("--interactive", "-i", action="store_true", help="Prompt preferences interactively")
    parser.add_argument("--json", "-j", help="Path to JSON file containing preferences")
    parser.add_argument("--refresh", action="store_true", help="Force refresh dataset cache")
    parser.add_argument("--limit", type=int, default=5, help="Number of preview records to display")
    add_preference_arguments(parser)
    args = parser.parse_args()

    console.print("[bold blue]Phase 3: Integration & Constraint Filter Pipeline[/bold blue]")

    # 1. Get user preferences
    try:
        if args.json:
            preferences = preferences_from_json(args.json)
        elif args.interactive:
            preferences = prompt_preferences()
        else:
            preferences = preferences_from_namespace(args)
    except PreferenceValidationError as exc:
        console.print(f"[red]Validation Error:[/red] {exc}")
        sys.exit(1)

    # 2. Load restaurant repository
    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
    except Exception as exc:
        console.print(f"[red]Failed to load repository dataset:[/red] {exc}")
        sys.exit(1)

    # 3. Apply constraints filter
    integration_service = IntegrationService(repo)
    result = integration_service.run(preferences)

    # 4. Display counts and matching records
    _print_filter_stats(result)
    if result.skip_llm:
        console.print(f"\n[yellow]{result.user_message}[/yellow]")
    else:
        _print_sample(result.capped_candidates, args.limit)

if __name__ == "__main__":
    main()
