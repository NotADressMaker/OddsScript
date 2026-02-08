"""Verification and contradiction detection."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from sportsbetlang.web_research_agent.extract import AnchoredFact


def triangulate(facts: Iterable[AnchoredFact]) -> Dict[str, List[AnchoredFact]]:
    grouped: Dict[str, List[AnchoredFact]] = defaultdict(list)
    for fact in facts:
        key = _normalize_claim(fact.claim)
        grouped[key].append(fact)

    confirmed: List[AnchoredFact] = []
    unconfirmed: List[AnchoredFact] = []
    for entries in grouped.values():
        unique_sources = {entry.url for entry in entries}
        if len(unique_sources) >= 2:
            confirmed.extend(entries)
        else:
            unconfirmed.extend(entries)

    return {"confirmed": confirmed, "unconfirmed": unconfirmed}


def detect_contradictions(facts: Iterable[AnchoredFact]) -> List[Dict[str, object]]:
    buckets: Dict[str, Dict[float, List[AnchoredFact]]] = defaultdict(lambda: defaultdict(list))
    for fact in facts:
        if fact.attribute is None or fact.value is None:
            continue
        buckets[fact.attribute][fact.value].append(fact)

    contradictions: List[Dict[str, object]] = []
    for attribute, values in buckets.items():
        if len(values) <= 1:
            continue
        contradiction = {
            "attribute": attribute,
            "values": [
                {
                    "value": value,
                    "sources": [entry.url for entry in entries],
                }
                for value, entries in values.items()
            ],
        }
        contradictions.append(contradiction)
    return contradictions


def recency_score(facts: Iterable[AnchoredFact]) -> float:
    timestamps = [fact.timestamp for fact in facts if fact.timestamp]
    if not timestamps:
        return 0.0
    timestamps.sort(reverse=True)
    return 1.0


def _normalize_claim(claim: str) -> str:
    return "".join(char.lower() for char in claim if char.isalnum() or char.isspace())
