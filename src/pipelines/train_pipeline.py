"""Training pipeline for league-specific totals models."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd

from src.data.datasources import CSVHistoricalDataSource
from src.data.feature_engineering import FeatureConfig, FeatureEngineer
from src.models.training import train_models
from src.utils.config import LeagueConfig


def train_pipeline(league: str, data_path: Path, config_path: Path) -> Dict[str, str]:
    config = LeagueConfig.from_yaml(config_path)
    if config.league != league:
        raise ValueError(f"Config league {config.league} does not match {league}.")

    data_source = CSVHistoricalDataSource(path=data_path)
    historical = data_source.load()
    historical = historical[historical["league"] == league]

    if historical.empty:
        raise ValueError("No historical data found for league.")

    feature_engineer = FeatureEngineer(FeatureConfig(rolling_window=config.rolling_window))
    features, target = feature_engineer.build_features(historical)

    output_dir = Path("artifacts") / league / datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    artifacts, _ = train_models(
        features=features,
        target=target,
        output_dir=output_dir,
        config={
            "league": league,
            "rolling_window": config.rolling_window,
            "test_size": config.test_size,
            "quantile_low": config.quantile_low,
            "quantile_high": config.quantile_high,
        },
    )

    return {
        "model_path": str(artifacts.model_path),
        "artifact_dir": str(output_dir),
    }
