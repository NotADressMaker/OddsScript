from __future__ import annotations

from datetime import datetime


def choose_most_recent(items: list, attr: str) -> object | None:
    def _key(item: object) -> datetime:
        value = getattr(item, attr)
        return value or datetime.min

    if not items:
        return None
    return max(items, key=_key)
