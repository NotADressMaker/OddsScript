"""Market normalization helpers."""

from __future__ import annotations


def normalize_market(item: dict) -> dict:
    market = (item.get("market") or "").lower()
    selection = item.get("selection") or item.get("team") or item.get("side")
    line = item.get("line")
    price = item.get("price") or item.get("odds")
    if market == "spread" and line is not None and selection:
        line = float(line)
    if market == "total" and isinstance(selection, str):
        selection = selection.lower()
        if selection in {"over", "under"}:
            selection = selection
    return {
        "event_id": str(item.get("event_id") or item.get("game_id") or ""),
        "book": item.get("book") or "unknown",
        "market": market,
        "selection": str(selection) if selection is not None else "",
        "line": line,
        "price": float(price) if price is not None else 0.0,
        "source": item.get("source") or "odds_feed",
        "raw": item,
    }

