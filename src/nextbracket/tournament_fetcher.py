"""
Tournament data fetcher for NextBracket.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .api_client import StartGGClient


class TournamentFetcher:
    """Fetches tournament data based on configuration."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self.config = self._load_config()
        self.client = StartGGClient()

    def _load_config(self) -> Dict:
        """Load configuration from JSON or YAML file."""
        if not self.config_path or not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                "Please create a config file in calendars/configs/ with your desired settings.\n"
                "See README.md for configuration examples."
            )

        with open(self.config_path, "r") as f:
            if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                if HAS_YAML:
                    return yaml.safe_load(f)
                else:
                    raise ImportError(
                        "PyYAML is required for YAML config files.\n"
                        "Install with: pip install PyYAML"
                    )
            else:
                # Default to JSON
                return json.load(f)

    def _get_videogame_ids(self) -> List[int]:
        """Extract videogame IDs from config, resolving names if needed."""
        videogame_ids = []

        for game in self.config.get("games", []):
            if isinstance(game, dict) and "id" in game:
                videogame_ids.append(game["id"])
            elif isinstance(game, dict) and "name" in game:
                # Try to resolve name to ID
                game_id = self.client.get_videogame_id(game["name"])
                if game_id:
                    videogame_ids.append(game_id)
                else:
                    print(f"Warning: Could not resolve game ID for {game['name']}")
            elif isinstance(game, str):
                # Game specified as string
                game_id = self.client.get_videogame_id(game)
                if game_id:
                    videogame_ids.append(game_id)
                else:
                    print(f"Warning: Could not resolve game ID for {game}")

        return videogame_ids

    def _get_owner_ids(self) -> List[str]:
        """Extract owner IDs from config (users who created tournaments)."""
        owner_ids = []

        for owner in self.config.get("owners", []):
            if isinstance(owner, dict) and "id" in owner:
                owner_ids.append(owner["id"])
            elif isinstance(owner, str):
                owner_ids.append(owner)

        return owner_ids

    def _get_location_params(self) -> Dict:
        """Extract location parameters from config."""
        location = self.config.get("location", {})

        # Assume coordinates if center is specified (for backward compatibility)
        if "center" in location:
            return {
                "latitude": location["center"]["latitude"],
                "longitude": location["center"]["longitude"],
                "radius": location["radius"],
                "radius_unit": location.get("radius_unit", "km"),
            }

        # For now, only coordinates are supported
        # City names would require geocoding
        print(
            "Warning: Only coordinate-based location filtering is currently supported"
        )
        return {}

    def fetch_tournaments(self) -> List[Dict]:
        """Fetch tournaments based on configuration using UNION logic."""
        videogame_ids = self._get_videogame_ids()
        owner_ids = self._get_owner_ids()
        location_params = self._get_location_params()
        filters = self.config.get("filters", {})

        # Debug: print what we got (remove in production)
        # print(f"Debug - videogame_ids: {videogame_ids}")
        # print(f"Debug - owner_ids: {owner_ids}")
        # print(f"Debug - admin_ids: {admin_ids}")
        # print(f"Debug - location_params: {location_params}")

        # Calculate date range - symmetric window based on years (optional)
        date_range_years = self.config.get("date_range_years")
        if date_range_years is not None and date_range_years > 0:
            days_range = date_range_years * 365  # Convert years to approximate days
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            after_date = int((today_start - timedelta(days=days_range)).timestamp())
            before_date = int((today_start + timedelta(days=days_range)).timestamp())
        else:
            # No date filtering - get all tournaments
            after_date = None
            before_date = None
            days_range = 0

        all_tournaments = []

        # Step 1: Fetch tournaments based on location/game/date criteria
        print(f"Fetching tournaments for {len(videogame_ids)} games...")
        print(f"Location: {location_params}")
        if days_range > 0:
            print(f"Date range: ±{days_range} days from today")
        else:
            print("Date range: No limit (all tournaments)")

        main_tournaments = self.client.get_tournaments(
            videogame_ids=videogame_ids,
            after_date=after_date,
            before_date=before_date,
            per_page=100,  # Reasonable default for API pagination
            **location_params,
        )

        if main_tournaments is None:
            print("Error: get_tournaments returned None for main criteria")
            main_tournaments = []

        all_tournaments.extend(main_tournaments)
        print(f"Found {len(main_tournaments)} tournaments from main criteria")

        # Step 2: Additionally fetch tournaments from specified owners (UNION)
        if owner_ids:
            print(
                f"\nAdditionally fetching tournaments from {len(owner_ids)} owners: {owner_ids}"
            )

            for owner_id in owner_ids:
                print(f"Fetching tournaments from owner {owner_id}...")
                owner_tournaments = self.client.get_tournaments(
                    owner_ids=[owner_id],  # Only filter by this owner
                    after_date=after_date,
                    before_date=before_date,
                    per_page=100,
                    videogame_ids=None,  # Don't filter by games for owner tournaments
                    # No location filters for owner tournaments
                )
                print(
                    f"Found {len(owner_tournaments)} tournaments from owner {owner_id}"
                )
                all_tournaments.extend(owner_tournaments)

        # Remove duplicates (in case owner tournaments also match main criteria)
        seen_ids = set()
        unique_tournaments = []
        for tournament in all_tournaments:
            tournament_id = tournament.get("id")
            if tournament_id and tournament_id not in seen_ids:
                seen_ids.add(tournament_id)
                unique_tournaments.append(tournament)

        # Apply additional filters
        filtered_tournaments = self._apply_filters(unique_tournaments, filters)

        print(f"\nTotal unique tournaments after UNION: {len(filtered_tournaments)}")
        return filtered_tournaments

    def _apply_filters(self, tournaments: List[Dict], filters: Dict) -> List[Dict]:
        """Apply additional filters to tournament results."""
        filtered = []

        min_attendees = filters.get("min_attendees", 0)

        for tournament in tournaments:
            # Filter by minimum attendees
            num_attendees = tournament.get("numAttendees")
            if num_attendees is not None and num_attendees < min_attendees:
                continue

            # Note: We no longer filter by registration status
            # isRegistrationOpen=False just means registration is closed, not that the tournament is cancelled

            filtered.append(tournament)

        return filtered
