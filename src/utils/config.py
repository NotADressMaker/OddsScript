"""Configuration utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass
class LeagueConfig:
    league: str
    rolling_window: int = 10
    test_size: int = 50
    quantile_low: float = 0.1
    quantile_high: float = 0.9

    @classmethod
    def from_yaml(cls, path: Path) -> "LeagueConfig":
        data: Dict[str, Any] = yaml.safe_load(path.read_text())
        return cls(**data)
