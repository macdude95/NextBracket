"""
start.gg GraphQL API client for NextBracket.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()


class StartGGClient:
    """GraphQL client for start.gg API."""

    BASE_URL = "https://api.start.gg/gql/alpha"
    API_KEY = os.getenv("STARTGG_API_KEY")

    def __init__(self):
        if not self.API_KEY:
            raise ValueError("STARTGG_API_KEY not found in environment variables")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.API_KEY}",
                "Content-Type": "application/json",
            }
        )

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = self.session.post(self.BASE_URL, json=payload)
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        return data.get("data", {})

    def get_tournaments(
        self,
        videogame_ids: Optional[List[int]] = None,
        videogame_names: Optional[List[str]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius: Optional[int] = None,
        radius_unit: str = "km",
        after_date: Optional[str] = None,
        before_date: Optional[str] = None,
        owner_ids: Optional[List[str]] = None,
        per_page: int = 50,
        page: int = 1,
    ) -> List[Dict]:
        """
        Query tournaments with various filters.

        Based on start.gg GraphQL API patterns.
        This will need to be adjusted based on actual API documentation.
        """

        # Convert radius to meters if needed (start.gg likely uses meters)
        radius_meters = None
        if radius:
            if radius_unit.lower() == "km":
                radius_meters = radius * 1000
            elif radius_unit.lower() == "miles":
                radius_meters = int(radius * 1609.34)  # miles to meters

        # Build filter object
        filters = {}

        if videogame_ids:
            filters["videogameIds"] = videogame_ids

        # Add location filtering with correct API structure
        if latitude and longitude and radius:
            # Format coordinates as string: "lat,lng"
            coordinates = f"{latitude},{longitude}"
            # Format radius with units
            radius_str = f"{radius}{radius_unit}"
            filters["location"] = {"distanceFrom": coordinates, "distance": radius_str}
            print(f"Using location filter: {coordinates} within {radius_str}")
        else:
            print(
                f"Note: No location filter - fetching all tournaments for game IDs: {videogame_ids}"
            )

        # Add date filtering if provided
        if after_date:
            filters["afterDate"] = after_date
            print(f"Filtering tournaments after: {after_date}")
        if before_date:
            filters["beforeDate"] = before_date
            print(f"Filtering tournaments before: {before_date}")

        # Add owner filtering if provided (using correct API structure)
        if owner_ids:
            filters["ownerId"] = owner_ids[0]  # Use actual admin ID
            print(f"Filtering tournaments by owner: {owner_ids[0]}")

        # Use different query structure depending on whether we're filtering by owner or not
        if owner_ids:
            # Use simple owner query when only filtering by owner (no other filters)
            # Based on user's working example
            query = """
            query TournamentsByOwner($perPage: Int!, $ownerId: ID!) {
                tournaments(query: {
                  perPage: $perPage
                  filter: {
                    ownerId: $ownerId
                  }
                }) {
                nodes {
                  id
                  name
                  slug
                  startAt
                  endAt
                  timezone
                  venueAddress
                  city
                  state
                  countryCode
                  isRegistrationOpen
                  numAttendees
                  events {
                    id
                    name
                    videogame {
                      id
                      name
                    }
                  }
                }
              }
            }
            """
            variables = {"perPage": per_page, "ownerId": owner_ids[0]}
        else:
            # Use the standard TournamentPageFilter query for other filters
            query = """
            query($perPage: Int, $page: Int, $filter: TournamentPageFilter) {
              tournaments(query: {
                perPage: $perPage
                page: $page
                filter: $filter
              }) {
                nodes {
                  id
                  name
                  slug
                  startAt
                  endAt
                  timezone
                  venueAddress
                  city
                  state
                  countryCode
                  isRegistrationOpen
                  numAttendees
                  events {
                    id
                    name
                    videogame {
                      id
                      name
                    }
                  }
                }
              }
            }
            """
            variables = {"perPage": per_page, "page": page, "filter": filters}

        try:
            data = self._execute_query(query, variables)
            tournaments = data.get("tournaments", {}).get("nodes", [])
            return tournaments
        except Exception as e:
            print(f"Error fetching tournaments: {e}")
            print(f"Query used: {query[:100]}...")
            print(f"Variables used: {variables}")
            return []

    def get_tournament_details(self, tournament_slug: str) -> Dict:
        """Get tournament details including owner information."""
        query = """
        query TournamentDetails($slug: String) {
          tournament(slug: $slug) {
            id
            name
            slug
            owner {
              id
              name
            }
            events {
              id
              name
              videogame {
                id
                name
              }
            }
          }
        }
        """

        try:
            data = self._execute_query(query, {"slug": tournament_slug})
            tournament = data.get("tournament", {})
            return tournament
        except Exception as e:
            print(f"Error fetching tournament details for {tournament_slug}: {e}")
            return {}

    def get_event_standings(
        self, event_id: str, page: int = 1, per_page: int = 50
    ) -> List[Dict]:
        """Get tournament standings to find user IDs."""
        query = """
        query EventStandings($eventId: ID!, $page: Int!, $perPage: Int!) {
          event(id: $eventId) {
            id
            name
            standings(query: {
              perPage: $perPage,
              page: $page
            }){
              nodes {
                placement
                entrant {
                  id
                  name
                }
              }
            }
          }
        }
        """

        try:
            data = self._execute_query(
                query, {"eventId": event_id, "page": page, "perPage": per_page}
            )
            event = data.get("event", {})
            standings = event.get("standings", {}).get("nodes", [])
            return standings
        except Exception as e:
            print(f"Error fetching event standings for {event_id}: {e}")
            return []

    def get_videogame_id(self, game_name: str) -> Optional[int]:
        """Get videogame ID by name. This may need adjustment based on actual API."""
        query = """
        query Videogames($name: String) {
          videogames(query: {name: $name}) {
            nodes {
              id
              name
            }
          }
        }
        """

        try:
            data = self._execute_query(query, {"name": game_name})
            videogames = data.get("videogames", {}).get("nodes", [])
            if videogames:
                return videogames[0]["id"]
        except Exception as e:
            print(f"Error fetching videogame ID for {game_name}: {e}")

        return None
