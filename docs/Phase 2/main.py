import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from input.adapters.argparse_adapter import add_preference_arguments, preferences_from_namespace
from input.adapters.cli import prompt_preferences
from input.adapters.json_adapter import preferences_from_json
from input.serializer import PreferenceSerializer
from input.validator import PreferenceValidationError

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Phase 2: User Preferences")
    parser.add_argument("--interactive", "-i", action="store_true", help="Prompt preferences interactively")
    parser.add_argument("--json", "-j", help="Path to JSON file containing preferences")
    add_preference_arguments(parser)
    args = parser.parse_args()

    console.print("[bold blue]Phase 2: User Input & Validation[/bold blue]")
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
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
        sys.exit(130)

    payload = PreferenceSerializer.to_dict(preferences)
    console.print(Panel(
        PreferenceSerializer.to_json(preferences),
        title="UserPreferences (Serialized JSON payload for downstream services)",
        border_style="green",
    ))
    console.print("[bold]Parsed fields:[/bold]", payload)

if __name__ == "__main__":
    main()
