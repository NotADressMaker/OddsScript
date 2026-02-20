"""Schema definitions for normalized historical game data."""

from __future__ import annotations

from typing import Final, Literal, Tuple

ColumnName = Literal[
    "date",
    "league",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "total",
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

REQUIRED_COLUMNS: Final[Tuple[ColumnName, ...]] = (
    "date",
    "league",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "total",
)

OPTIONAL_COLUMNS: Final[Tuple[ColumnName, ...]] = (
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
)

ALL_COLUMNS: Final[Tuple[ColumnName, ...]] = REQUIRED_COLUMNS + OPTIONAL_COLUMNS
