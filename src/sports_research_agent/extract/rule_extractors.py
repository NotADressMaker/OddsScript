from __future__ import annotations

import re
from datetime import datetime

from .schemas import (
    Citation,
    InjuryReport,
    LineMove,
    ProbablePitcher,
    StartingGoalie,
    StarterInfo,
    StatusEnum,
)
from ..parse.extract_main import extract_main_text
from ..parse.extract_tables import extract_tables

STATUS_MAP = {
    "out": StatusEnum.OUT,
    "doubtful": StatusEnum.DOUBTFUL,
    "questionable": StatusEnum.QUESTIONABLE,
    "probable": StatusEnum.PROBABLE,
    "active": StatusEnum.ACTIVE,
}


def _normalize_status(value: str) -> StatusEnum:
    key = value.strip().lower()
    return STATUS_MAP.get(key, StatusEnum.UNKNOWN)


def _build_citation(claim: str, url: str, snippet: str, retrieved_at: datetime) -> Citation:
    return Citation(claim=claim, url=url, snippet=snippet[:200], retrieved_at=retrieved_at)


def extract_injuries_from_html(
    html: str, source_url: str, retrieved_at: datetime
) -> list[InjuryReport]:
    injuries: list[InjuryReport] = []
    for table in extract_tables(html):
        header = [cell.lower() for cell in table[0]]
        if not any("player" in cell for cell in header):
            continue
        for row in table[1:]:
            row_data = dict(zip(header, row))
            player = row_data.get("player")
            status_value = row_data.get("status") or row_data.get("injury status")
            if not player or not status_value:
                continue
            status = _normalize_status(status_value)
            snippet = f"{player} listed as {status_value}."
            citation = _build_citation(snippet, source_url, snippet, retrieved_at)
            injuries.append(
                InjuryReport(
                    player=player,
                    team=row_data.get("team"),
                    status=status,
                    injury=row_data.get("injury"),
                    update_time=retrieved_at,
                    source_url=source_url,
                    snippet=snippet,
                    citations=[citation],
                    source=source_url,
                    timestamp=retrieved_at,
                    citation=citation,
                )
            )
    return injuries


def extract_goalies_from_text(
    html: str, source_url: str, retrieved_at: datetime
) -> list[StartingGoalie]:
    text = extract_main_text(html)
    results: list[StartingGoalie] = []
    pattern = re.compile(r"(?P<goalie>[A-Z][a-z]+\s[A-Z][a-z]+)\s+\((?P<team>[A-Z]{2,3})\)\s+-\s+(?P<status>confirmed|projected)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        goalie = match.group("goalie")
        status = match.group("status").lower()
        snippet = match.group(0)
        citation = _build_citation(snippet, source_url, snippet, retrieved_at)
        results.append(
            StartingGoalie(
                goalie=goalie,
                team=match.group("team"),
                confirmed=status == "confirmed",
                update_time=retrieved_at,
                source_url=source_url,
                snippet=snippet,
                citations=[citation],
                source=source_url,
                timestamp=retrieved_at,
                citation=citation,
            )
        )
    return results


def extract_probable_pitchers(
    html: str, source_url: str, retrieved_at: datetime
) -> list[ProbablePitcher]:
    text = extract_main_text(html)
    results: list[ProbablePitcher] = []
    pattern = re.compile(
        r"(?P<pitcher>[A-Z][a-z]+\s[A-Z][a-z]+)\s+\((?P<team>[A-Z]{2,3})\)\s+vs\.\s+(?P<opp>[A-Z]{2,3})",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        snippet = match.group(0)
        citation = _build_citation(snippet, source_url, snippet, retrieved_at)
        results.append(
            ProbablePitcher(
                pitcher=match.group("pitcher"),
                team=match.group("team"),
                opponent=match.group("opp"),
                confirmed=False,
                update_time=retrieved_at,
                source_url=source_url,
                snippet=snippet,
                citations=[citation],
                source=source_url,
                timestamp=retrieved_at,
                citation=citation,
            )
        )
    return results


def extract_line_moves(
    html: str, source_url: str, retrieved_at: datetime
) -> list[LineMove]:
    text = extract_main_text(html)
    results: list[LineMove] = []
    pattern = re.compile(
        r"opening\s+(?P<open>[-+]?\d+\.?\d*)\s+to\s+(?P<current>[-+]?\d+\.?\d*)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        open_line = match.group("open")
        current_line = match.group("current")
        magnitude = None
        try:
            magnitude = abs(float(current_line) - float(open_line))
        except ValueError:
            magnitude = None
        direction = None
        if magnitude is not None:
            direction = "up" if float(current_line) > float(open_line) else "down"
        snippet = match.group(0)
        citation = _build_citation(snippet, source_url, snippet, retrieved_at)
        results.append(
            LineMove(
                market="total",
                open=open_line,
                current=current_line,
                direction=direction,
                magnitude=magnitude,
                update_time=retrieved_at,
                source_url=source_url,
                snippet=snippet,
                citations=[citation],
                source=source_url,
                timestamp=retrieved_at,
                citation=citation,
            )
        )
    return results


def extract_qb_starters(
    html: str, source_url: str, retrieved_at: datetime
) -> list[StarterInfo]:
    text = extract_main_text(html)
    results: list[StarterInfo] = []
    pattern = re.compile(
        r"starting\s+qb\s*[:\-]\s*(?P<player>[A-Z][a-z]+\s[A-Z][a-z]+)\s+\((?P<team>[A-Z]{2,3})\)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        snippet = match.group(0)
        citation = _build_citation(snippet, source_url, snippet, retrieved_at)
        results.append(
            StarterInfo(
                player=match.group("player"),
                team=match.group("team"),
                role="QB",
                confirmed=True,
                update_time=retrieved_at,
                source_url=source_url,
                snippet=snippet,
                citations=[citation],
                source=source_url,
                timestamp=retrieved_at,
                citation=citation,
            )
        )
    return results
