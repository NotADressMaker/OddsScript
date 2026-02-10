from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    OUT = "OUT"
    DOUBTFUL = "DOUBTFUL"
    QUESTIONABLE = "QUESTIONABLE"
    PROBABLE = "PROBABLE"
    ACTIVE = "ACTIVE"
    UNKNOWN = "UNKNOWN"


class Citation(BaseModel):
    claim: str
    url: str
    snippet: str = Field(max_length=200)
    retrieved_at: datetime
    published_at: datetime | None = None


class ExtractedEntityV1(BaseModel):
    schema_version: Literal["v1"] = "v1"
    source: str
    timestamp: datetime | None = None
    confidence: float = 0.5
    citation: Citation


class InjuryReport(ExtractedEntityV1):
    player: str
    team: str | None
    status: StatusEnum
    injury: str | None = None
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]


class StarterInfo(ExtractedEntityV1):
    player: str
    team: str | None
    role: str
    confirmed: bool
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]


class LineupInfo(ExtractedEntityV1):
    team: str
    starters: list[str]
    confirmed: bool
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]


class ProbablePitcher(ExtractedEntityV1):
    pitcher: str
    team: str | None
    opponent: str | None
    confirmed: bool
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]


class StartingGoalie(ExtractedEntityV1):
    goalie: str
    team: str | None
    confirmed: bool
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]


class ScheduleContext(ExtractedEntityV1):
    team: str
    rest_days: int | None
    back_to_back: bool | None
    travel_notes: str | None
    source_url: str
    snippet: str
    citations: list[Citation]
    confidence: float = 0.4


class LineMove(ExtractedEntityV1):
    market: Literal["spread", "total", "moneyline"]
    open: str | None
    current: str | None
    direction: str | None
    magnitude: float | None
    update_time: datetime | None = None
    source_url: str
    snippet: str
    citations: list[Citation]
    confidence: float = 0.4


class NewsItem(ExtractedEntityV1):
    headline: str
    summary: str
    update_time: datetime | None
    source_url: str
    snippet: str
    citations: list[Citation]


class BoxscoreSnapshot(ExtractedEntityV1):
    team: str
    opponent: str | None
    score: str | None
    stats: dict[str, str]
    source_url: str
    snippet: str
    citations: list[Citation]
