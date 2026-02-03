"""Odds feed fetcher."""

from __future__ import annotations

from typing import Iterable

from sportsbetlang.ingestion.config import RunContext
from sportsbetlang.ingestion.normalizers.markets import normalize_market


def fetch_odds(get_odds: object, sport: str, markets: Iterable[str], date_range: dict, observed_at: str) -> list[dict]:
    snapshots: list[dict] = []
    for market in markets:
        payload = get_odds(sport=sport, market=market, date_range=date_range, books=None)
        for item in payload or []:
            normalized = normalize_market(item)
            normalized["observed_at"] = observed_at
            normalized.setdefault("source", "get_odds")
            snapshots.append(normalized)
    return snapshots

