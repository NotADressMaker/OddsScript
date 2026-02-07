"""Inference utilities for totals regression models."""

from __future__ import annotations

from dataclasses import dataclass
from math import erf
from pathlib import Path
from typing import Optional

import json

import joblib
import numpy as np
import pandas as pd

from src.data.feature_engineering import FeatureConfig, FeatureEngineer


@dataclass
class ModelBundle:
    model: object
    quantile_low: object
    quantile_high: object
    feature_columns: list[str]


def load_bundle(artifact_dir: Path) -> ModelBundle:
    model = joblib.load(artifact_dir / "model.pkl")
    quantile_low = joblib.load(artifact_dir / "quantile_low.pkl")
    quantile_high = joblib.load(artifact_dir / "quantile_high.pkl")
    schema = json.loads((artifact_dir / "feature_schema.json").read_text())
    return ModelBundle(
        model=model,
        quantile_low=quantile_low,
        quantile_high=quantile_high,
        feature_columns=schema["columns"],
    )


def predict_totals(
    historical_df: pd.DataFrame,
    upcoming_df: pd.DataFrame,
    rolling_window: int,
    bundle: ModelBundle,
    line: Optional[float] = None,
) -> pd.DataFrame:
    combined = pd.concat([historical_df, upcoming_df], ignore_index=True)
    engineer = FeatureEngineer(FeatureConfig(rolling_window=rolling_window))
    features, _ = engineer.build_features(combined)
    historical_features = features.head(len(historical_df))
    upcoming_features = features.tail(len(upcoming_df)).copy()
    upcoming_features.index = upcoming_df.index
    upcoming_features = upcoming_features[bundle.feature_columns]

    baseline_means = historical_features[bundle.feature_columns].mean(numeric_only=True)
    warnings = _build_warnings(historical_df, upcoming_df, rolling_window)
    for idx in warnings:
        upcoming_features.loc[idx, :] = baseline_means

    preds = bundle.model.predict(upcoming_features.values)
    low = bundle.quantile_low.predict(upcoming_features.values)
    high = bundle.quantile_high.predict(upcoming_features.values)

    result = upcoming_df.copy()
    result["predicted_total_mean"] = preds
    result["prediction_interval_80_low"] = low
    result["prediction_interval_80_high"] = high
    if warnings:
        result["warning"] = result.index.map(lambda idx: warnings.get(idx))

    if line is not None:
        interval_width = np.maximum(high - low, 1e-6)
        residual_std = np.mean(interval_width / 2.56)
        if residual_std == 0:
            residual_std = 1.0
        prob_over = 1.0 - _normal_cdf((line - preds) / residual_std)
        result["probability_over"] = prob_over

    return result


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(erf)(x / np.sqrt(2.0)))


def _build_warnings(
    historical_df: pd.DataFrame, upcoming_df: pd.DataFrame, rolling_window: int
) -> dict[int, str]:
    warnings: dict[int, str] = {}
    teams = set(historical_df["home_team"]).union(set(historical_df["away_team"]))
    counts = (
        historical_df[["home_team", "away_team"]]
        .stack()
        .value_counts()
        .to_dict()
    )
    for idx, row in upcoming_df.iterrows():
        missing = []
        for team in [row.get("home_team"), row.get("away_team")]:
            if team not in teams:
                missing.append(str(team))
            elif counts.get(team, 0) < rolling_window:
                warnings[idx] = (
                    f"Insufficient history for {team}; using league baseline."
                )
        if missing:
            warnings[idx] = (
                f"Unseen teams {', '.join(missing)}; using league baseline."
            )
    return warnings
