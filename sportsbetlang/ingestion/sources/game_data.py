"""Game data fetcher."""

from __future__ import annotations

from typing import Iterable


def fetch_game_data(get_game_data: object, sport: str, date_range: dict, level: str) -> list[dict]:
    payload = get_game_data(sport=sport, date_range=date_range, level=level)
    return payload or []

