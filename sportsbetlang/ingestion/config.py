"""Configuration models for the ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional, Sequence


@dataclass(frozen=True)
class SourceConfig:
    api_keys: Mapping[str, str] = field(default_factory=dict)
    base_urls: Mapping[str, str] = field(default_factory=dict)
    db_connection: Optional[str] = None
    allowed_domains: Sequence[str] = field(default_factory=tuple)
    scraping_allowed: bool = False


@dataclass(frozen=True)
class PipelineConfig:
    sport: str
    start_date: str
    end_date: str
    markets: Sequence[str]
    leagues: Optional[Sequence[str]] = None
    teams: Optional[Sequence[str]] = None
    sources: SourceConfig = field(default_factory=SourceConfig)
    seed: int = 7

    def market_list(self) -> list[str]:
        return [market.strip() for market in self.markets if market.strip()]


@dataclass(frozen=True)
class RunContext:
    observed_at: str
    run_mode: str
    extra: Mapping[str, str] = field(default_factory=dict)
    data_gaps: list[dict] = field(default_factory=list)

    def record_gap(self, gap: dict) -> None:
        self.data_gaps.append(gap)


@dataclass(frozen=True)
class ExtractionResult:
    records: list[dict]
    raw_text: Optional[str] = None
    data_gaps: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class PipelineReport:
    counts: Mapping[str, int]
    data_gaps: Sequence[dict]
    feature_preview_sql: str
    notes: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class Tooling:
    get_odds: object
    get_game_data: object
    get_injuries: object
    fetch_url: object
    query_db: object
    upsert_db: object
    validate_schema: object
    now_utc: object

    def as_dict(self) -> dict:
        return {
            "get_odds": self.get_odds,
            "get_game_data": self.get_game_data,
            "get_injuries": self.get_injuries,
            "fetch_url": self.fetch_url,
            "query_db": self.query_db,
            "upsert_db": self.upsert_db,
            "validate_schema": self.validate_schema,
            "now_utc": self.now_utc,
        }


DEFAULT_MARKETS: tuple[str, ...] = ("spread", "total", "moneyline")

