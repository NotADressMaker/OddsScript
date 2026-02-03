"""Entity resolution utilities."""

from __future__ import annotations

import hashlib


def resolve_team_id(name: str, league: str | None = None) -> str:
    key = f"{name.lower()}::{league or 'unknown'}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def resolve_player_id(name: str, team_id: str | None = None) -> str:
    key = f"{name.lower()}::{team_id or 'unknown'}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

