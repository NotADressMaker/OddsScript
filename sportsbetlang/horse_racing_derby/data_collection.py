from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import pandas as pd


@dataclass
class PublicDataSource:
    name: str
    url: str
    file_type: str = "csv"


class PublicDataCollector:
    """Collects derby race data from publicly available endpoints."""

    DEFAULT_SOURCES: List[PublicDataSource] = [
        PublicDataSource("Kentucky Derby historical", "https://raw.githubusercontent.com/robinhouston/horse-racing/master/data/kentucky_derby_results.csv"),
        PublicDataSource("Current entries example", "https://raw.githubusercontent.com/robinhouston/horse-racing/master/data/derby_entries_latest.csv"),
    ]

    def __init__(self, sources: Iterable[PublicDataSource] | None = None):
        self.sources = list(sources or self.DEFAULT_SOURCES)

    def fetch_all(self) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for source in self.sources:
            if source.file_type.lower() != "csv":
                raise ValueError(f"Unsupported file type: {source.file_type}")
            df = pd.read_csv(source.url)
            df["source_name"] = source.name
            frames.append(df)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)
