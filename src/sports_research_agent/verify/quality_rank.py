from __future__ import annotations

from dataclasses import dataclass

from ..sources.registry import SourceRegistry


@dataclass(frozen=True)
class SourceScore:
    domain: str
    score: float


QUALITY_SCORE = {
    "official": 1.0,
    "team": 0.9,
    "beat": 0.8,
    "newswire": 0.7,
    "media": 0.6,
    "blog": 0.4,
}


def score_sources(registry: SourceRegistry) -> list[SourceScore]:
    scores: list[SourceScore] = []
    for source in registry.sources:
        scores.append(SourceScore(domain=source.domain, score=QUALITY_SCORE.get(source.source_type, 0.5)))
    return scores


def source_quality(registry: SourceRegistry, domain: str) -> float:
    source = registry.find_by_domain(domain)
    if not source:
        return 0.5
    return QUALITY_SCORE.get(source.source_type, 0.5)
