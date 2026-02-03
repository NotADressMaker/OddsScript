"""Convert raw injury text into structured JSON records."""

from __future__ import annotations

import re
from typing import Iterable

from sportsbetlang.ingestion.config import ExtractionResult

STATUS_PATTERNS = {
    "out": re.compile(r"\bout\b", re.IGNORECASE),
    "doubtful": re.compile(r"\bdoubtful\b", re.IGNORECASE),
    "questionable": re.compile(r"\bquestionable\b", re.IGNORECASE),
    "limited": re.compile(r"\blimited\b", re.IGNORECASE),
    "active": re.compile(r"\bactive\b", re.IGNORECASE),
}


def extract_injuries(raw: object, observed_at: str, source: str) -> ExtractionResult:
    if raw is None:
        return ExtractionResult(records=[], data_gaps=[_gap("injuries", "no_payload", observed_at)])

    if isinstance(raw, list):
        records = [_normalize_record(item, observed_at, source) for item in raw]
        return ExtractionResult(records=records)

    if isinstance(raw, dict):
        records = [_normalize_record(raw, observed_at, source)]
        return ExtractionResult(records=records)

    if isinstance(raw, str):
        records = _extract_from_text(raw, observed_at, source)
        data_gaps = [] if records else [_gap("injuries", "unparsed_text", observed_at)]
        return ExtractionResult(records=records, raw_text=raw, data_gaps=data_gaps)

    return ExtractionResult(records=[], data_gaps=[_gap("injuries", "unsupported_payload", observed_at)])


def _normalize_record(payload: dict, observed_at: str, source: str) -> dict:
    return {
        "player": payload.get("player") or payload.get("player_name"),
        "team": payload.get("team"),
        "league": payload.get("league"),
        "status": payload.get("status"),
        "injury_type": payload.get("injury_type"),
        "body_part": payload.get("body_part"),
        "minutes_restriction": payload.get("minutes_restriction"),
        "source": payload.get("source", source),
        "observed_at": payload.get("observed_at", observed_at),
        "effective_date": payload.get("effective_date"),
        "confidence": payload.get("confidence", 0.5),
        "raw_text": payload.get("raw_text"),
    }


def _extract_from_text(raw_text: str, observed_at: str, source: str) -> list[dict]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    records: list[dict] = []
    for line in lines:
        status = _infer_status(line)
        record = {
            "player": _extract_player(line),
            "team": None,
            "league": None,
            "status": status,
            "injury_type": _extract_injury_type(line),
            "body_part": _extract_body_part(line),
            "minutes_restriction": _extract_minutes_restriction(line),
            "source": source,
            "observed_at": observed_at,
            "effective_date": None,
            "confidence": 0.3 if status is None else 0.6,
            "raw_text": line,
        }
        if record["player"] is None and record["injury_type"] is None and record["body_part"] is None:
            continue
        records.append(record)
    return records


def _infer_status(text: str) -> str | None:
    for label, pattern in STATUS_PATTERNS.items():
        if pattern.search(text):
            return label
    return None


def _extract_player(text: str) -> str | None:
    match = re.match(r"([A-Z][a-zA-Z.'-]+\s+[A-Z][a-zA-Z.'-]+)", text)
    if match:
        return match.group(1)
    return None


def _extract_injury_type(text: str) -> str | None:
    for keyword in ["strain", "sprain", "fracture", "contusion", "illness"]:
        if keyword in text.lower():
            return keyword
    return None


def _extract_body_part(text: str) -> str | None:
    for part in ["ankle", "knee", "hamstring", "groin", "shoulder", "back", "wrist", "foot"]:
        if part in text.lower():
            return part
    return None


def _extract_minutes_restriction(text: str) -> str | None:
    match = re.search(r"minutes? restriction|limited to (\d+) minutes", text, re.IGNORECASE)
    if match:
        return match.group(0)
    return None


def _gap(category: str, reason: str, observed_at: str) -> dict:
    return {
        "category": category,
        "reason": reason,
        "observed_at": observed_at,
    }

