import argparse
import sys
from rich.console import Console
from config.settings import get_settings
from data.repository import RestaurantRepository

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Phase 1: Data Ingestion")
    parser.add_argument("--refresh", action="store_true", help="Force refresh cache")
    args = parser.parse_args()

    console.print("[bold blue]Phase 1: Initializing Data Ingestion[/bold blue]")
    repo = RestaurantRepository()
    try:
        repo.load(force_refresh=args.refresh)
        console.print(
            f"[green]✔ Success![/green] Loaded {repo.count} restaurants into repository.\n"
            f"Cache location: [cyan]{get_settings().restaurant_cache_path}[/cyan]"
        )
    except Exception as exc:
        console.print(f"[red]Error during ingestion:[/red] {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
