"""Database adapter that delegates to provided tool functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass
class DatabaseClient:
    query_fn: object
    upsert_fn: object

    def query(self, sql: str, params: Mapping[str, Any] | None = None) -> list[dict]:
        params = params or {}
        return self.query_fn(sql, params)

    def upsert(self, table: str, rows: Iterable[dict], conflict_keys: Iterable[str]) -> dict:
        return self.upsert_fn(table, list(rows), list(conflict_keys))

