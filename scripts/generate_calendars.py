#!/usr/bin/env python3
"""
Script to generate calendars for all configured calendar feeds.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from nextbracket.tournament_fetcher import TournamentFetcher
from nextbracket.calendar_generator import CalendarGenerator


def find_calendar_configs():
    """Find all calendar config files (JSON or YAML)."""
    configs_dir = Path("calendars/configs")
    if not configs_dir.exists():
        print("No calendars/configs directory found")
        return []

    config_files = []
    # Look for both JSON and YAML files
    for pattern in ["*.json", "*.yaml", "*.yml"]:
        for config_file in configs_dir.glob(pattern):
            config_files.append(config_file)

    return config_files


def generate_calendar_for_config(config_path: Path):
    """Generate calendar for a specific config."""
    calendar_name = config_path.stem  # Get filename without extension
    print(f"\n=== Processing calendar: {calendar_name} ===")

    try:
        # Initialize fetcher with this config
        fetcher = TournamentFetcher(str(config_path))

        # Fetch tournaments
        tournaments = fetcher.fetch_tournaments()

        if not tournaments:
            print("No tournaments found for this calendar.")
            return False

        # Generate calendar
        generator = CalendarGenerator(fetcher.config)
        calendar = generator.generate_calendar(tournaments)

        # Save calendar in feeds directory
        feeds_dir = Path("calendars/feeds")
        feeds_dir.mkdir(parents=True, exist_ok=True)
        ics_path = feeds_dir / f"{calendar_name}.ics"
        generator.save_calendar(calendar, str(ics_path))

        print(f"Generated calendar with {len(tournaments)} events")
        return True

    except Exception as e:
        print(f"Error processing calendar {calendar_name}: {e}")
        return False


def main():
    """Generate calendars for all configured feeds."""
    print("NextBracket Calendar Generator")
    print("=" * 40)

    config_files = find_calendar_configs()
    if not config_files:
        print("No calendar configurations found.")
        print("Create configs in calendars/*/config.json")
        return

    print(f"Found {len(config_files)} calendar configurations")

    success_count = 0
    for config_file in config_files:
        if generate_calendar_for_config(config_file):
            success_count += 1

    print("\n=== Summary ===")
    print(f"Processed {len(config_files)} calendars")
    print(f"Successfully generated: {success_count}")
    print(f"Failed: {len(config_files) - success_count}")


if __name__ == "__main__":
    main()
