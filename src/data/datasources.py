"""Data source interfaces for historical and upcoming games."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from src.data.schema import ALL_COLUMNS


class HistoricalDataSource(Protocol):
    """Protocol for loading historical game data."""

    def load(self) -> pd.DataFrame:
        """Return normalized historical game data."""


@dataclass
class CSVHistoricalDataSource:
    """Load historical games from a user-provided CSV file."""

    path: Path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        missing = [col for col in ALL_COLUMNS if col not in df.columns]
        for col in missing:
            df[col] = pd.NA
        df = df[list(ALL_COLUMNS)]
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        return df


@dataclass
class APIDataSource:
    """Placeholder for fetching historical data from an API.

    Implementers should override `fetch` with their API logic.
    """

    endpoint: str

    def load(self) -> pd.DataFrame:
        raise NotImplementedError(
            "APIDataSource is a placeholder. Implement fetch logic for your provider."
        )
