"""Prediction pipeline for upcoming games."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from src.data.datasources import CSVHistoricalDataSource
from src.models.inference import load_bundle, predict_totals
from src.utils.config import LeagueConfig


def predict_pipeline(
    league: str,
    historical_path: Path,
    upcoming_path: Path,
    artifact_dir: Path,
    config_path: Path,
    line: Optional[float],
) -> pd.DataFrame:
    config = LeagueConfig.from_yaml(config_path)
    if config.league != league:
        raise ValueError(f"Config league {config.league} does not match {league}.")

    historical = CSVHistoricalDataSource(path=historical_path).load()
    historical = historical[historical["league"] == league]

    upcoming = pd.read_csv(upcoming_path)
    for col in historical.columns:
        if col not in upcoming.columns:
            upcoming[col] = pd.NA
    upcoming = upcoming[historical.columns]
    upcoming["date"] = pd.to_datetime(upcoming["date"], errors="coerce")

    if upcoming.empty:
        raise ValueError("No upcoming games found.")

    bundle = load_bundle(artifact_dir)
    predictions = predict_totals(
        historical_df=historical,
        upcoming_df=upcoming,
        rolling_window=config.rolling_window,
        bundle=bundle,
        line=line,
    )
    return predictions
