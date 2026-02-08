from __future__ import annotations

from collections import defaultdict
from typing import Iterable
from urllib.parse import urlparse

from ..extract.schemas import InjuryReport, LineMove, StarterInfo
from ..sources.registry import SourceRegistry
from .quality_rank import source_quality
from .recency import choose_most_recent


def _domain(url: str) -> str:
    return urlparse(url).netloc


def reconcile_injuries(
    registry: SourceRegistry, injuries: Iterable[InjuryReport]
) -> list[InjuryReport]:
    grouped: dict[str, list[InjuryReport]] = defaultdict(list)
    for item in injuries:
        key = f"{item.player.lower()}|{item.team or ''}"
        grouped[key].append(item)

    reconciled: list[InjuryReport] = []
    for items in grouped.values():
        ranked = sorted(
            items,
            key=lambda item: (source_quality(registry, _domain(item.source_url)), item.update_time),
            reverse=True,
        )
        best = ranked[0]
        best.confidence = source_quality(registry, _domain(best.source_url))
        reconciled.append(best)
    return reconciled


def reconcile_starters(
    registry: SourceRegistry, starters: Iterable[StarterInfo]
) -> list[StarterInfo]:
    grouped: dict[str, list[StarterInfo]] = defaultdict(list)
    for item in starters:
        key = f"{item.player.lower()}|{item.role}|{item.team or ''}"
        grouped[key].append(item)

    reconciled: list[StarterInfo] = []
    for items in grouped.values():
        most_recent = choose_most_recent(items, "update_time")
        if most_recent is None:
            continue
        most_recent.confidence = source_quality(registry, _domain(most_recent.source_url))
        reconciled.append(most_recent)
    return reconciled


def reconcile_line_moves(
    registry: SourceRegistry, moves: Iterable[LineMove]
) -> list[LineMove]:
    reconciled: list[LineMove] = []
    for move in moves:
        move.confidence = source_quality(registry, _domain(move.source_url))
        reconciled.append(move)
    return reconciled
