#!/usr/bin/env python3
"""CLI: data, preferences, integration, and Groq recommendations (Phases 1–4)."""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config.settings import get_settings
from data.preprocessor import normalize_city_key
from data.repository import DataNotLoadedError, RestaurantRepository
from input.adapters.argparse_adapter import add_preference_arguments, preferences_from_namespace
from input.adapters.cli import prompt_preferences
from input.adapters.json_adapter import preferences_from_json
from input.serializer import PreferenceSerializer
from input.validator import PreferenceValidationError
from presentation.formatter import print_filter_stats, print_recommendations
from presentation.dedup import dedup_recommendation_result
from services.integration import IntegrationService
from services.llm.exceptions import LLMConfigError, LLMError, LLMQuotaError
from services.recommendation_engine import RecommendationEngine

console = Console()


def _resolve_preferences(args: argparse.Namespace):
    if getattr(args, "json", None):
        return preferences_from_json(args.json)
    return preferences_from_namespace(args)


def _print_filter_stats(result) -> None:
    counts = result.filter_result.step_counts
    console.print(
        f"[bold]Filter pipeline:[/bold] {counts.initial} total → "
        f"{counts.after_location} location → "
        f"{counts.after_rating} rating → "
        f"{counts.after_budget} budget → "
        f"{counts.after_cuisine} cuisine"
    )
    console.print(
        f"[bold]Capped for LLM:[/bold] {len(result.capped_candidates)} "
        f"(max {get_settings().candidate_cap})"
    )


def _print_prompt_payload(payload) -> None:
    import json

    console.print(Panel(payload.system_message, title="System message", border_style="blue"))
    console.print(Panel(payload.user_message, title="User message", border_style="cyan"))
    console.print(
        "[dim]Structured candidates:[/dim]",
        json.dumps(payload.candidates[:3], ensure_ascii=False, indent=2),
    )
    if len(payload.candidates) > 3:
        console.print(f"[dim]… {len(payload.candidates) - 3} more in payload[/dim]")


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _print_sample(restaurants: list, limit: int) -> None:
    table = Table(title=f"Sample results (showing up to {limit})")
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


def _print_preferences(preferences) -> None:
    payload = PreferenceSerializer.to_dict(preferences)
    console.print(Panel(
        PreferenceSerializer.to_json(preferences),
        title="UserPreferences (serialized for Phase 3)",
        border_style="green",
    ))
    console.print("[dim]Parsed fields:[/dim]", payload)


def _run_integration(
    repo: RestaurantRepository,
    preferences,
    *,
    candidate_cap: int | None = None,
    top_k: int | None = None,
    settings=None,
):
    return IntegrationService(repo, settings=settings).run(
        preferences,
        candidate_cap=candidate_cap,
        top_k=top_k,
    )


def cmd_load(args: argparse.Namespace) -> int:
    repo = RestaurantRepository()
    repo.load(force_refresh=args.refresh)
    console.print(
        f"[green]Loaded {repo.count} restaurants[/green] "
        f"(cache: {get_settings().restaurant_cache_path})"
    )
    return 0


def cmd_preferences(args: argparse.Namespace) -> int:
    try:
        if args.json:
            preferences = preferences_from_json(args.json)
        elif args.interactive:
            preferences = prompt_preferences()
        else:
            preferences = preferences_from_namespace(args)
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return 130

    _print_preferences(preferences)

    if args.preview_filter:
        repo = RestaurantRepository()
        try:
            repo.load(force_refresh=args.refresh)
        except Exception as exc:
            console.print(f"[red]Failed to load data:[/red] {exc}")
            return 1
        result = _run_integration(repo, preferences)
        _print_filter_stats(result)
        if result.skip_llm:
            console.print(f"\n[yellow]{result.user_message}[/yellow]")
        elif args.limit:
            _print_sample(result.capped_candidates, args.limit)

    return 0


def cmd_query(args: argparse.Namespace) -> int:
    try:
        preferences = preferences_from_namespace(args)
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1

    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
    except Exception as exc:
        console.print(f"[red]Failed to load data:[/red] {exc}")
        return 1

    result = _run_integration(repo, preferences)
    _print_filter_stats(result)
    if result.skip_llm:
        console.print(f"[yellow]{result.user_message}[/yellow]")
        return 0

    console.print(
        f"[bold]{len(result.filter_result.candidates)} matches[/bold], "
        f"showing top {min(args.limit, len(result.capped_candidates))} capped candidates"
    )
    _print_sample(result.capped_candidates, args.limit)
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    try:
        if args.interactive:
            preferences = prompt_preferences()
        else:
            preferences = _resolve_preferences(args)
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return 130

    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
    except Exception as exc:
        console.print(f"[red]Failed to load data:[/red] {exc}")
        return 1

    settings = get_settings()
    if args.verbose or args.log_prompts:
        settings = settings.model_copy(update={"log_prompts": True})
    if args.verbose or args.log_llm:
        settings = settings.model_copy(update={"log_llm_responses": True})

    integration = _run_integration(
        repo,
        preferences,
        candidate_cap=args.cap,
        top_k=args.top_k,
        settings=settings,
    )
    print_filter_stats(integration.filter_result, capped_for_llm=len(integration.capped_candidates))

    if integration.skip_llm:
        console.print(f"\n[yellow]{integration.user_message}[/yellow]")
        return 0

    if args.show_prompt and integration.prompt_payload:
        _print_prompt_payload(integration.prompt_payload)

    try:
        engine = RecommendationEngine(settings=settings)
        result = engine.recommend(
            integration,
            preferences,
            force_fallback=args.fallback_only,
        )
    except LLMConfigError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except LLMQuotaError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except LLMError as exc:
        console.print(f"[red]Recommendation failed:[/red] {exc}")
        return 1

    console.print()
    deduped_result, removed = dedup_recommendation_result(result)
    if removed:
        console.print(f"[dim]🔁 {removed} duplicate outlet(s) collapsed[/dim]")
    print_recommendations(deduped_result)
    return 0


def cmd_integrate(args: argparse.Namespace) -> int:
    try:
        if args.interactive:
            preferences = prompt_preferences()
        else:
            preferences = _resolve_preferences(args)
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        return 130

    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
    except Exception as exc:
        console.print(f"[red]Failed to load data:[/red] {exc}")
        return 1

    settings = get_settings()
    if args.verbose or args.log_prompts:
        settings = settings.model_copy(update={"log_prompts": True})

    result = _run_integration(
        repo,
        preferences,
        candidate_cap=args.cap,
        top_k=args.top_k,
        settings=settings,
    )
    _print_filter_stats(result)

    if result.skip_llm:
        console.print(f"\n[yellow]{result.user_message}[/yellow]")
        console.print("[dim]LLM call skipped (no candidates).[/dim]")
        return 0

    console.print(
        f"\n[green]Ready for Phase 4:[/green] {len(result.capped_candidates)} candidates, "
        f"top_k={result.prompt_payload.top_k if result.prompt_payload else args.top_k}"
    )

    if args.show_prompt and result.prompt_payload:
        _print_prompt_payload(result.prompt_payload)
    elif args.limit:
        _print_sample(result.capped_candidates, args.limit)

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
    except Exception as exc:
        console.print(f"[red]Failed to load data:[/red] {exc}")
        return 1

    from collections import Counter

    cities = Counter(normalize_city_key(r.city) for r in repo.all())
    bands = Counter(r.budget_band or "unknown" for r in repo.all())

    console.print(f"Total restaurants: [bold]{repo.count}[/bold]")
    console.print("Top cities:", ", ".join(f"{c} ({n})" for c, n in cities.most_common(10)))
    console.print("Budget bands:", dict(bands))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zomato recommender — restaurant data and user preferences"
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    load_parser = sub.add_parser("load", help="Download/cache restaurant data")
    load_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-download from Hugging Face and rebuild cache",
    )
    load_parser.set_defaults(func=cmd_load)

    prefs_parser = sub.add_parser(
        "preferences",
        help="Capture and validate user preferences (Phase 2)",
    )
    prefs_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for preferences interactively",
    )
    prefs_parser.add_argument(
        "--json",
        default=None,
        help='Preferences as JSON object, e.g. \'{"location":"Bangalore",...}\'',
    )
    prefs_parser.add_argument(
        "--preview-filter",
        action="store_true",
        help="Apply hard filters to dataset and show match count",
    )
    prefs_parser.add_argument("--limit", type=int, default=5)
    prefs_parser.add_argument("--refresh", action="store_true")
    add_preference_arguments(
        prefs_parser,
        require_location=False,
        default_location=None,
    )
    prefs_parser.set_defaults(func=cmd_preferences)

    query_parser = sub.add_parser(
        "query",
        help="Filter restaurants using preference flags",
    )
    query_parser.add_argument("--limit", type=int, default=10)
    query_parser.add_argument("--refresh", action="store_true")
    add_preference_arguments(
        query_parser,
        require_location=False,
        default_location="Bangalore",
    )
    query_parser.set_defaults(func=cmd_query)

    integrate_parser = sub.add_parser(
        "integrate",
        help="Filter, cap candidates, and build LLM prompt (Phase 3)",
    )
    integrate_parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Prompt for preferences interactively",
    )
    integrate_parser.add_argument("--json", default=None)
    integrate_parser.add_argument(
        "--show-prompt",
        action="store_true",
        help="Print full system/user messages (dev preview)",
    )
    integrate_parser.add_argument(
        "--log-prompts",
        action="store_true",
        help="Log prompt to logger (also enabled with -v)",
    )
    integrate_parser.add_argument(
        "--cap",
        type=int,
        default=None,
        help=f"Candidate cap (default: {get_settings().candidate_cap})",
    )
    integrate_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        dest="top_k",
        help=f"Recommendations to request (default: {get_settings().recommendation_top_k})",
    )
    integrate_parser.add_argument("--limit", type=int, default=5)
    integrate_parser.add_argument("--refresh", action="store_true")
    add_preference_arguments(
        integrate_parser,
        require_location=False,
        default_location="Bangalore",
    )
    integrate_parser.set_defaults(func=cmd_integrate)

    recommend_parser = sub.add_parser(
        "recommend",
        help="Full pipeline: filter → Groq LLM → ranked recommendations (Phase 4)",
    )
    recommend_parser.add_argument("-i", "--interactive", action="store_true")
    recommend_parser.add_argument("--json", default=None)
    recommend_parser.add_argument("--show-prompt", action="store_true")
    recommend_parser.add_argument("--log-prompts", action="store_true")
    recommend_parser.add_argument(
        "--log-llm",
        action="store_true",
        help="Log raw Groq response (also enabled with -v)",
    )
    recommend_parser.add_argument(
        "--fallback-only",
        action="store_true",
        help="Skip Groq; use rule-based template recommendations",
    )
    recommend_parser.add_argument("--cap", type=int, default=None)
    recommend_parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        dest="top_k",
    )
    recommend_parser.add_argument("--refresh", action="store_true")
    add_preference_arguments(
        recommend_parser,
        require_location=False,
        default_location="Bangalore",
    )
    recommend_parser.set_defaults(func=cmd_recommend)

    stats_parser = sub.add_parser("stats", help="Dataset summary after load")
    stats_parser.add_argument("--refresh", action="store_true")
    stats_parser.set_defaults(func=cmd_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if (
        args.command == "preferences"
        and not args.interactive
        and not args.json
        and args.location is None
    ):
        console.print(
            "[yellow]No flags provided; starting interactive mode.[/yellow] "
            "Use --json or pass --location / other flags for non-interactive input."
        )
        args.interactive = True

    try:
        return args.func(args)
    except DataNotLoadedError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1
    except PreferenceValidationError as exc:
        console.print(f"[red]{exc}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
