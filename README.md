# NextBracket

NextBracket is an open-source tool that collects tournament listings from start.gg and produces subscribe-ready calendar feeds so players can keep track of upcoming competitive events in their area.

## 🗓️ How do I subscribe to one of the existing calendars?

You can subscribe to any of the generated calendars generated using your preferred calendar app. All calendar feeds can be found in the `calendars/feeds/` folder.

**Example: SLO Melee Tournaments calendar feed - slo-melee.ics**

```
webcal://raw.githubusercontent.com/macdude95/NextBracket/main/calendars/feeds/slo-melee.ics
```

**Works with:** Google Calendar, Apple Calendar, Outlook, and most other calendar applications.

---

## Features

- **Automated Tournament Tracking**: Fetches tournament data from start.gg API
- **Location-Based Filtering**: Find tournaments within a specified radius
- **Game-Specific Filtering**: Track tournaments for specific games
- **iCal Calendar Feed**: Subscribe to tournament calendars in any calendar app
- **Daily Updates**: Automated GitHub Actions workflow keeps feeds current
- **Configurable**: Easy JSON configuration for location, games, and filters

## Dev Setup

1. **Configure your preferences** in `calendars/configs/`
2. **Set your start.gg API key** in GitHub repository secrets as `STARTGG_API_KEY`
3. **Subscribe to the calendar** using the links below

## Configuration

Create config files in `calendars/configs/{calendar-name}.yaml` (YAML) or `calendars/configs/{calendar-name}.json` (JSON):

```yaml
# Games to filter by - only tournaments including these games
games:
  - id: 1 # Super Smash Bros. Melee

# Geographic filtering - tournaments within radius of center point
location:
  center:
    latitude: 35.2828 # San Luis Obispo latitude
    longitude: -120.6596 # San Luis Obispo longitude
  radius: 50 # kilometers from center point

# Tournament owners - tournaments from these organizers included regardless of filters (UNION logic)
owners:
  - '2821656' # Busted Controllers organizer
  - '15246' # Bozion/Emerey Philippsen organizer

# Calendar display settings
calendar:
  title: 'SLO Melee Tournaments'
  description: 'Upcoming Super Smash Bros. Melee tournaments in the San Luis Obispo area'
```

**Owner Behavior**: Owners use UNION logic - tournaments from specified owners are **added** to the calendar regardless of location/game filters. This ensures you never miss tournaments from your favorite organizers.

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

Built on [start.gg's GraphQL API](https://developer.start.gg/docs/intro) with support for:

- Geographic filtering with coordinates and radius
- Game-specific tournament queries
- Attendee counts and registration status
- Venue and location data
