"""Injury and news fetcher."""

from __future__ import annotations


def fetch_injuries(get_injuries: object, sport: str, date_range: dict) -> object:
    return get_injuries(sport=sport, date_range=date_range)


def fetch_injury_url(fetch_url: object, url: str) -> str:
    return fetch_url(url)

