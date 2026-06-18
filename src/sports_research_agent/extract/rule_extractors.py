from __future__ import annotations

import re
from datetime import datetime

from ..parse.extract_main import extract_main_text
from ..parse.extract_tables import extract_tables
from .schemas import (
    Citation,
    InjuryReport,
    LineMove,
    NovelSignal,
    ProbablePitcher,
    StarterInfo,
    StartingGoalie,
    StatusEnum,
)

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
            row_data = dict(zip(header, row, strict=False))
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
    pattern = re.compile(
        r"(?P<goalie>[A-Z][a-z]+\s[A-Z][a-z]+)\s+\((?P<team>[A-Z]{2,3})\)\s+-\s+(?P<status>confirmed|projected)",
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


def extract_line_moves(html: str, source_url: str, retrieved_at: datetime) -> list[LineMove]:
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


NOVEL_SIGNAL_PATTERNS: list[tuple[str, str, str]] = [
    (
        "travel_rest",
        (
            r"\b(?:third game in four nights|back[- ]to[- ]back|(?:no|zero) rest|"
            r"travel(?:ing|led)?|late arrival|road trip|time zone|altitude)\b"
        ),
        "negative",
    ),
    (
        "lineup_role",
        (
            r"\b(?:minutes restriction|limited minutes|lineup change|bench(?:ed)?|"
            r"scratched|called up|role change|first start|resting starters?)\b"
        ),
        "mixed",
    ),
    (
        "weather_venue",
        (
            r"\b(?:wind gusts?|crosswind|rain|snow|roof (?:open|closed)|"
            r"field conditions?|humidity|extreme heat|cold front)\b"
        ),
        "mixed",
    ),
    (
        "market_microstructure",
        (
            r"\b(?:reverse line movement|steam move|buyback|stale line|low liquidity|"
            r"market disagreement|split tickets|sharp money)\b"
        ),
        "unknown",
    ),
    (
        "tactical_matchup",
        (
            r"\b(?:pace mismatch|scheme change|defensive matchup|forecheck|bullpen taxed|"
            r"platoon advantage|transition defense|rebounding edge)\b"
        ),
        "mixed",
    ),
    (
        "motivation_schedule",
        (
            r"\b(?:lookahead spot|letdown spot|must[- ]win|revenge spot|trap game|"
            r"clinched|eliminated|rivalry)\b"
        ),
        "mixed",
    ),
    (
        "officiating",
        (
            r"\b(?:referee assignment|umpire assignment|officials?|strike zone|whistle|"
            r"penalty rate|foul rate)\b"
        ),
        "mixed",
    ),
]


def _sentence_windows(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _extract_team_hint(snippet: str) -> str | None:
    bracketed = re.search(r"\(([A-Z]{2,4})\)", snippet)
    if bracketed:
        return bracketed.group(1)
    acronym = re.search(r"\b([A-Z]{2,4})\b", snippet)
    return acronym.group(1) if acronym else None


def extract_novel_moneyline_signals(
    html: str, source_url: str, retrieved_at: datetime
) -> list[NovelSignal]:
    """Extract under-discussed contextual signals for moneyline research.

    These are deliberately broader than canonical injuries/starters so the agent can
    surface potentially stale or slow-to-price information for human review.
    """
    text = extract_main_text(html)
    results: list[NovelSignal] = []
    seen: set[tuple[str, str]] = set()
    for sentence in _sentence_windows(text):
        for category, pattern, default_impact in NOVEL_SIGNAL_PATTERNS:
            if not re.search(pattern, sentence, re.IGNORECASE):
                continue
            snippet = sentence[:240]
            key = (category, snippet.lower())
            if key in seen:
                continue
            seen.add(key)
            citation = _build_citation(snippet, source_url, snippet, retrieved_at)
            novelty_score = (
                0.75 if category in {"travel_rest", "market_microstructure", "lineup_role"} else 0.6
            )
            results.append(
                NovelSignal(
                    category=category,  # type: ignore[arg-type]
                    team=_extract_team_hint(sentence),
                    signal=sentence,
                    moneyline_impact=default_impact,  # type: ignore[arg-type]
                    novelty_score=novelty_score,
                    source_url=source_url,
                    snippet=snippet,
                    citations=[citation],
                    source=source_url,
                    timestamp=retrieved_at,
                    citation=citation,
                    confidence=0.45,
                )
            )
    return results


def extract_qb_starters(html: str, source_url: str, retrieved_at: datetime) -> list[StarterInfo]:
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
