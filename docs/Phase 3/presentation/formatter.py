"""Format recommendation results for CLI display (Phase 5c — aligned with API shape).

Changes from Phase 4:
- print_filter_stats() mirrors FilterStatsDTO step counts
- AI/template badge logic matches the frontend badge labels
- fallback_reason displayed when used_fallback=True
- Field widths honour the required display fields from the problem statement
"""

from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from models.integration import FilterResult
from models.recommendation import RecommendationResult

console = Console()


# ── Filter stats ──────────────────────────────────────────────────────────────

def print_filter_stats(filter_result: FilterResult, capped_for_llm: Optional[int] = None) -> None:
    """Print a filter-step summary table mirroring the API FilterStatsDTO.

    Parameters
    ----------
    filter_result:  FilterResult produced by HardConstraintFilter.
    capped_for_llm: If provided, add a final "Sent to AI" step.
    """
    counts = filter_result.step_counts

    table = Table(title="Filter pipeline", show_header=True, header_style="bold dim")
    table.add_column("Step", style="dim")
    table.add_column("Count", justify="right", style="bold")

    steps = [
        ("Total in dataset",    counts.initial),
        ("After location",      counts.after_location),
        ("After min rating",    counts.after_rating),
        ("After budget band",   counts.after_budget),
        ("After cuisine",       counts.after_cuisine),
    ]
    if capped_for_llm is not None:
        steps.append(("Sent to AI (cap)", capped_for_llm))

    for label, value in steps:
        table.add_row(label, f"{value:,}")

    console.print(table)


# ── Recommendations ───────────────────────────────────────────────────────────

def print_recommendations(result: RecommendationResult) -> None:
    """Print ranked recommendations to the terminal.

    Aligns with the API RecommendationItemDTO shape:
      rank | name | cuisine | rating | estimated_cost | location | explanation
    AI/template badge mirrors the frontend 🤖 / 📊 logic.
    """
    # ── Empty result ──
    if result.is_empty:
        msg = result.summary or "No recommendations available."
        console.print(Panel(msg, title="No Results", border_style="yellow"))
        return

    # ── Fallback warning ──
    if result.used_fallback:
        reason = result.fallback_reason or "AI unavailable"
        console.print(
            Panel(
                Text.assemble(
                    ("📊 Ranked by rating", "bold yellow"),
                    f" — {reason}",
                ),
                border_style="yellow",
                expand=False,
            )
        )

    # ── Summary ──
    if result.summary:
        console.print(Panel(result.summary, title="✨ Summary", border_style="green"))

    # ── Table ──
    table = Table(
        title=f"Top {len(result.recommendations)} Recommendation(s)",
        show_lines=True,
    )
    table.add_column("#",           justify="right",  style="bold",    no_wrap=True, width=3)
    table.add_column("Restaurant",  style="cyan",                       min_width=20, max_width=32)
    table.add_column("Cuisine",                                          min_width=16, max_width=28)
    table.add_column("Rating",      justify="right",  style="yellow",  no_wrap=True, width=6)
    table.add_column("Est. Cost",   justify="right",  style="green",   no_wrap=True, width=10)
    table.add_column("Location",                                         min_width=18, max_width=28)
    table.add_column("Why",                                              min_width=30, max_width=60)

    for item in result.recommendations:
        rating_str = f"⭐ {item.rating:.1f}" if item.rating is not None else "—"
        cost_str   = f"₹{item.estimated_cost}" if item.estimated_cost else "—"

        # Badge: matches frontend logic — 🤖 for AI, 📊 for template
        if item.is_ai_generated:
            name_cell = Text.assemble(item.name, " ", ("🤖", ""))
        else:
            name_cell = Text.assemble(item.name, " ", ("📊", "dim"))

        # Truncate explanation to keep table readable; full text via --verbose (future)
        explanation = item.explanation
        if len(explanation) > 120:
            explanation = explanation[:117] + "…"

        table.add_row(
            str(item.rank),
            name_cell,
            item.cuisine,
            rating_str,
            cost_str,
            item.location,
            explanation,
        )

    console.print(table)
