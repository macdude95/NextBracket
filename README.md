# NextBracket

NextBracket is an open-source tool that collects tournament listings from start.gg and produces subscribe-ready calendar feeds so players can keep track of upcoming competitive events in their area.

## Features

- **Automated Tournament Tracking**: Fetches tournament data from start.gg API
- **Location-Based Filtering**: Find tournaments within a specified radius
- **Game-Specific Filtering**: Track tournaments for specific games
- **iCal Calendar Feed**: Subscribe to tournament calendars in any calendar app
- **Daily Updates**: Automated GitHub Actions workflow keeps feeds current
- **Configurable**: Easy JSON configuration for location, games, and filters

## Quick Start

1. **Configure your preferences** in `calendars/configs/`
2. **Set your start.gg API key** in GitHub repository secrets as `STARTGG_API_KEY`
3. **Subscribe to the calendar** using the links below

## Subscribe to Tournament Calendars

Each calendar feed is available at its own URL. Currently available calendars:

### SLO Melee Tournaments ✅

**Focus:** Super Smash Bros. Melee tournaments within 300km of San Luis Obispo
**Status:** Active - tournaments from 7 days ago through 180 days ahead loaded

**Google Calendar:** [Add to Calendar](webcal://raw.githubusercontent.com/macdude95/NextBracket/main/calendars/feeds/slo-melee.ics)

**Apple Calendar:** [Subscribe](webcal://raw.githubusercontent.com/macdude95/NextBracket/main/calendars/feeds/slo-melee.ics)

**Other Apps:** Copy this URL: `https://raw.githubusercontent.com/macdude95/NextBracket/main/calendars/feeds/slo-melee.ics`

## Configuration

Create config files in `calendars/configs/{calendar-name}.yaml` (YAML) or `calendars/configs/{calendar-name}.json` (JSON):

```yaml
# Geographic filtering - tournaments within radius of center point
location:
  center:
    latitude: 35.2828 # center point latitude
    longitude: -120.6596 # center point longitude
  radius: 150 # kilometers from center point

# Games to filter by - only tournaments including these games
games:
  - id: 1 # Super Smash Bros. Melee

# Tournament admins - tournaments from these organizers included regardless of filters (UNION logic)
admins:
  - 'admin_id' # Admin Name

# Filtering options
filters:
  date_range_days: 90 # look ahead this many days
  max_events: 50 # maximum tournaments to fetch
  include_past_days: 7 # include tournaments from this many days ago

# Calendar display settings
calendar:
  title: 'Calendar Title'
  description: 'Calendar Description'
```

**Admin Behavior**: Admins use UNION logic - tournaments from specified admins are **added** to the calendar regardless of location/game filters. This ensures you never miss tournaments from your favorite organizers.

⚠️ **Note**: Admin filtering is currently implemented but may have API compatibility issues. Core location/game/date filtering is fully operational.

## Development

### Prerequisites

- Python 3.8+
- start.gg API key (get from [start.gg developer settings](https://start.gg/admin/profile/developer))

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```bash
python scripts/generate_calendars.py
```

This will generate calendar feeds in `calendars/feeds/` for all configured calendars.

## GitHub Actions

The repository includes automated daily updates via GitHub Actions:

- **Schedule**: Daily at 6 AM PST
- **Trigger**: Also supports manual runs
- **Process**: Fetches tournaments → generates calendar → commits updates

## API Integration

Built on start.gg's GraphQL API with support for:

- Geographic filtering with coordinates and radius
- Game-specific tournament queries
- Attendee counts and registration status
- Venue and location data
