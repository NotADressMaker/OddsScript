"""Schema definitions for normalized historical game data."""

from __future__ import annotations

from typing import Final, List

REQUIRED_COLUMNS: Final[List[str]] = [
    "date",
    "league",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "total",
]

OPTIONAL_COLUMNS: Final[List[str]] = [
    "neutral_site",
    "home_rest_days",
    "away_rest_days",
    "injuries_home",
    "injuries_away",
    "pace_proxy",
    "weather",
    "closing_total",
    "home_travel_distance",
    "away_travel_distance",
    "xg_home",
    "xg_away",
]

ALL_COLUMNS: Final[List[str]] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
