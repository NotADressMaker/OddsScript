"""Utilities for building machine-learning friendly UFC fight datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

UFC_DATASET_COLUMNS = [
    "event_date",
    "event_name",
    "weight_class",
    "fighter",
    "opponent",
    "is_favorite",
    "moneyline",
    "implied_probability",
    "result",
    "method",
    "round",
    "scheduled_rounds",
    "reach_inches",
    "height_inches",
    "age",
    "sig_strikes_landed",
    "sig_strikes_attempted",
    "takedowns_landed",
    "takedowns_attempted",
    "sub_attempts",
]


@dataclass(frozen=True)
class UFCFightRow:
    """One fighter-perspective row for a UFC bout dataset."""

    event_date: str
    event_name: str
    weight_class: str
    fighter: str
    opponent: str
    is_favorite: bool | None = None
    moneyline: int | None = None
    implied_probability: float | None = None
    result: str = ""
    method: str = ""
    round: int | None = None
    scheduled_rounds: int | None = None
    reach_inches: float | None = None
    height_inches: float | None = None
    age: float | None = None
    sig_strikes_landed: int | None = None
    sig_strikes_attempted: int | None = None
    takedowns_landed: int | None = None
    takedowns_attempted: int | None = None
    sub_attempts: int | None = None

    def to_record(self) -> dict[str, object]:
        return {column: _clean_value(getattr(self, column)) for column in UFC_DATASET_COLUMNS}


def american_implied_probability(moneyline: int | str | None) -> float | None:
    """Convert American odds to no-vig-unadjusted implied probability."""
    if moneyline in (None, ""):
        return None
    odds = int(moneyline)
    if odds < 0:
        return round(abs(odds) / (abs(odds) + 100), 6)
    if odds > 0:
        return round(100 / (odds + 100), 6)
    return None


def build_ufc_fight_dataset(rows: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """
    Normalize UFC fight records into a stable fighter-perspective schema.

    Inputs may already use the target column names. Common aliases such as
    ``date``, ``fighter_name``, ``opponent_name``, and ``odds`` are accepted.
    Missing implied probabilities are derived from American moneyline odds.
    """
    dataset: list[dict[str, object]] = []
    for raw in rows:
        normalized = _normalize_row(raw)
        dataset.append(UFCFightRow(**normalized).to_record())
    return dataset


def build_ufc_dataset_file(input_path: str | Path, output_path: str | Path) -> int:
    """Read a CSV of UFC fight rows, normalize it, and write a dataset CSV."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    with input_path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        dataset = build_ufc_fight_dataset(reader)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=UFC_DATASET_COLUMNS)
        writer.writeheader()
        writer.writerows(dataset)
    return len(dataset)


def _normalize_row(raw: Mapping[str, object]) -> dict[str, object]:
    def pick(*names: str, default: object = "") -> object:
        for name in names:
            value = raw.get(name)
            if value not in (None, ""):
                return value
        return default

    moneyline = _optional_int(pick("moneyline", "odds", "american_odds", default=None))
    implied = _optional_float(pick("implied_probability", "implied_prob", default=None))
    if implied is None:
        implied = american_implied_probability(moneyline)

    return {
        "event_date": str(pick("event_date", "date")),
        "event_name": str(pick("event_name", "event")),
        "weight_class": str(pick("weight_class", "division")),
        "fighter": str(pick("fighter", "fighter_name", "red_fighter")),
        "opponent": str(pick("opponent", "opponent_name", "blue_fighter")),
        "is_favorite": _optional_bool(pick("is_favorite", "favorite", default=None)),
        "moneyline": moneyline,
        "implied_probability": implied,
        "result": str(pick("result", "outcome")),
        "method": str(pick("method", "finish_method")),
        "round": _optional_int(pick("round", "finish_round", default=None)),
        "scheduled_rounds": _optional_int(pick("scheduled_rounds", "bout_rounds", default=None)),
        "reach_inches": _optional_float(pick("reach_inches", "reach", default=None)),
        "height_inches": _optional_float(pick("height_inches", "height", default=None)),
        "age": _optional_float(pick("age", default=None)),
        "sig_strikes_landed": _optional_int(pick("sig_strikes_landed", "ssl", default=None)),
        "sig_strikes_attempted": _optional_int(pick("sig_strikes_attempted", "ssa", default=None)),
        "takedowns_landed": _optional_int(pick("takedowns_landed", "td_landed", default=None)),
        "takedowns_attempted": _optional_int(pick("takedowns_attempted", "td_attempted", default=None)),
        "sub_attempts": _optional_int(pick("sub_attempts", "submission_attempts", default=None)),
    }


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(float(str(value)))


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(str(value))


def _optional_bool(value: object) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "favorite", "fav"}


def _clean_value(value: object) -> object:
    if value is None:
        return ""
    return value
