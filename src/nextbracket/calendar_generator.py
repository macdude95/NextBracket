"""
iCal calendar generator for NextBracket.
"""

from datetime import datetime, timezone
from typing import Dict, List
from icalendar import Calendar, Event, vText
from pathlib import Path


class CalendarGenerator:
    """Generates iCal calendar from tournament data."""

    def __init__(self, config: Dict):
        self.config = config

    def generate_calendar(self, tournaments: List[Dict]) -> Calendar:
        """Generate iCal calendar from tournament data."""
        cal = Calendar()

        # Calendar metadata
        cal.add("prodid", "-//NextBracket//Tournament Calendar//EN")
        cal.add("version", "2.0")
        cal.add(
            "name",
            vText(self.config.get("calendar", {}).get("title", "Tournament Calendar")),
        )
        cal.add(
            "description",
            vText(
                self.config.get("calendar", {}).get(
                    "description", "Upcoming tournaments"
                )
            ),
        )

        # Add timezone
        timezone_str = self.config.get("calendar", {}).get("timezone", "UTC")

        for tournament in tournaments:
            event = self._create_event(tournament, timezone_str)
            if event:
                cal.add_component(event)

        return cal

    def _create_event(self, tournament: Dict, timezone_str: str) -> Event:
        """Create an iCal event from tournament data."""
        event = Event()

        # Basic event info
        event.add("summary", self._get_event_summary(tournament))
        event.add("description", self._get_event_description(tournament))
        event.add("location", self._get_event_location(tournament))
        event.add("url", f"https://start.gg/{tournament.get('slug', '')}")

        # Parse start and end times
        start_time = self._parse_datetime(tournament.get("startAt"))
        end_time = self._parse_datetime(tournament.get("endAt"))

        if start_time:
            event.add("dtstart", start_time)
        if end_time:
            event.add("dtend", end_time)
        elif start_time:
            # If no end time, assume 4 hours for single-day tournaments
            from datetime import timedelta

            event.add("dtend", start_time + timedelta(hours=4))

        # Unique ID for the event
        event.add("uid", f"tournament-{tournament.get('id')}@nextbracket")

        return event

    def _get_event_summary(self, tournament: Dict) -> str:
        """Generate event summary/title."""
        name = tournament.get("name", "Unknown Tournament")

        # Add game info if available
        events = tournament.get("events", [])
        if events:
            game_names = set()
            for event in events:
                videogame = event.get("videogame", {})
                if videogame.get("name"):
                    game_names.add(videogame["name"])

            if game_names:
                games_str = ", ".join(sorted(str(name) for name in game_names))
                return f"{name} ({games_str})"

        return name

    def _get_event_description(self, tournament: Dict) -> str:
        """Generate event description."""
        description_parts = []

        # Tournament info
        if tournament.get("numAttendees"):
            description_parts.append(f"Attendees: {tournament['numAttendees']}")

        # Events breakdown
        events = tournament.get("events", [])
        if events:
            event_names = []
            for event in events:
                name = event.get("name", "Unknown Event")
                event_names.append(str(name))  # Ensure string
            description_parts.append(f"Events: {', '.join(event_names)}")

        # Registration status
        if tournament.get("isRegistrationOpen") is False:
            description_parts.append("Registration Closed")

        # Add URL
        description_parts.append(
            f"View on start.gg: https://start.gg/{tournament.get('slug', '')}"
        )

        return "\n".join(description_parts)

    def _get_event_location(self, tournament: Dict) -> str:
        """Generate event location string."""
        location_parts = []

        if tournament.get("venueAddress"):
            location_parts.append(str(tournament["venueAddress"]))

        city_state = []
        if tournament.get("city"):
            city_state.append(str(tournament["city"]))
        if tournament.get("state"):
            city_state.append(str(tournament["state"]))

        if city_state:
            location_parts.append(", ".join(city_state))

        if tournament.get("countryCode"):
            location_parts.append(str(tournament["countryCode"]))

        return ", ".join(location_parts) if location_parts else "TBD"

    def _parse_datetime(self, timestamp: int) -> datetime:
        """Parse Unix timestamp to datetime object."""
        if not timestamp:
            return None

        try:
            # start.gg uses Unix timestamps
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, TypeError):
            return None

    def save_calendar(
        self, calendar: Calendar, output_path: str = "tournament_calendar.ics"
    ):
        """Save calendar to iCal file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as f:
            f.write(calendar.to_ical())

        print(f"Calendar saved to {output_file}")
