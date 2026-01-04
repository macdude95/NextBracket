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
        if self.config_path and self.config_path.exists():
            with open(self.config_path, "r") as f:
                if self.config_path.suffix.lower() in [".yaml", ".yml"]:
                    if HAS_YAML:
                        return yaml.safe_load(f)
                    else:
                        raise ImportError("PyYAML is required for YAML config files")
                else:
                    # Default to JSON for backward compatibility
                    return json.load(f)
        else:
            # Default config for backward compatibility
            return {
                "location": {
                    "type": "coordinates",
                    "center": {"latitude": 35.2828, "longitude": -120.6596},
                    "radius": 150,
                    "radius_unit": "km",
                },
                "games": [{"name": "Super Smash Bros. Melee", "id": 1}],
                "filters": {"date_range_days": 90, "max_events": 50},
                "calendar": {
                    "title": "SLO Melee Tournaments",
                    "description": "Upcoming tournaments",
                    "timezone": "America/Los_Angeles",
                },
            }

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

    def _get_admin_ids(self) -> List[str]:
        """Extract admin IDs from config."""
        admin_ids = []

        for admin in self.config.get("admins", []):
            if isinstance(admin, dict) and "id" in admin:
                admin_ids.append(admin["id"])
            elif isinstance(admin, str):
                admin_ids.append(admin)

        return admin_ids

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
        admin_ids = self._get_admin_ids()
        location_params = self._get_location_params()
        filters = self.config.get("filters", {})

        # Calculate date range - include past week to catch recently completed tournaments
        days_ahead = filters.get("date_range_days", 90)
        days_behind = filters.get(
            "include_past_days", 7
        )  # Include past week by default
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        after_date = int((today_start - timedelta(days=days_behind)).timestamp())
        before_date = int((today_start + timedelta(days=days_ahead)).timestamp())

        all_tournaments = []

        # Step 1: Fetch tournaments based on location/game/date criteria
        print(f"Fetching tournaments for {len(videogame_ids)} games...")
        print(f"Location: {location_params}")
        print(f"Date range: {days_ahead} days ahead")

        main_tournaments = self.client.get_tournaments(
            videogame_ids=videogame_ids,
            after_date=after_date,
            before_date=before_date,
            per_page=min(filters.get("max_events", 50), 50),  # API limit
            **location_params,
        )

        all_tournaments.extend(main_tournaments)
        print(f"Found {len(main_tournaments)} tournaments from main criteria")

        # Step 2: Additionally fetch tournaments from specified admins (UNION)
        if admin_ids:
            print(
                f"\nAdditionally fetching tournaments from {len(admin_ids)} admins: {admin_ids}"
            )

            for admin_id in admin_ids:
                print(f"Fetching tournaments from admin {admin_id}...")
                admin_tournaments = self.client.get_tournaments(
                    owner_ids=[admin_id],  # Only filter by this admin
                    after_date=after_date,
                    before_date=before_date,
                    per_page=min(filters.get("max_events", 50), 50),
                    # No location/game filters for admin tournaments
                )
                print(
                    f"Found {len(admin_tournaments)} tournaments from admin {admin_id}"
                )
                all_tournaments.extend(admin_tournaments)

        # Remove duplicates (in case admin tournaments also match main criteria)
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
