from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import yaml


@dataclass(frozen=True)
class TrustedSource:
    domain: str
    label: str
    source_type: str
    rss: tuple[str, ...] = field(default_factory=tuple)
    sitemaps: tuple[str, ...] = field(default_factory=tuple)
    allowed_paths: tuple[str, ...] = field(default_factory=tuple)
    content_types: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class SourceRegistry:
    league: str
    sources: list[TrustedSource]

    def domains(self) -> set[str]:
        return {source.domain for source in self.sources}

    def sources_for_content(self, content_type: str) -> list[TrustedSource]:
        return [
            source
            for source in self.sources
            if not source.content_types or content_type in source.content_types
        ]

    def find_by_domain(self, domain: str) -> TrustedSource | None:
        for source in self.sources:
            if source.domain == domain:
                return source
        return None


def _normalize_tuple(values: Iterable[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    return tuple(value.strip() for value in values if value and value.strip())


def load_registry(path: str | Path) -> SourceRegistry:
    data = yaml.safe_load(Path(path).read_text())
    league = data.get("league", "unknown")
    sources: list[TrustedSource] = []
    for item in data.get("sources", []):
        sources.append(
            TrustedSource(
                domain=item["domain"],
                label=item.get("label", item["domain"]),
                source_type=item.get("type", "news"),
                rss=_normalize_tuple(item.get("rss")),
                sitemaps=_normalize_tuple(item.get("sitemaps")),
                allowed_paths=_normalize_tuple(item.get("allowed_paths")),
                content_types=_normalize_tuple(item.get("content_types")),
            )
        )
    return SourceRegistry(league=league, sources=sources)
