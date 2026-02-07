"""Model training and artifact saving."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import json

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.data.feature_engineering import FeatureSchema
from src.utils.metrics import interval_coverage, regression_metrics
from src.utils.splits import expanding_window_split
import yaml


@dataclass
class TrainingArtifacts:
    model_path: Path
    quantile_low_path: Path
    quantile_high_path: Path
    feature_schema_path: Path
    metrics_path: Path
    config_path: Path


def train_models(
    features: pd.DataFrame,
    target: pd.Series,
    output_dir: Path,
    config: Dict[str, Any],
) -> Tuple[TrainingArtifacts, Dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)

    X = features.values
    y = target.values

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("ridge", Ridge(alpha=1.0)),
        ]
    )
    tree_model = HistGradientBoostingRegressor(
        max_depth=6, learning_rate=0.05, max_iter=300
    )
    quantile_low = GradientBoostingRegressor(loss="quantile", alpha=config["quantile_low"])
    quantile_high = GradientBoostingRegressor(
        loss="quantile", alpha=config["quantile_high"]
    )

    metrics: Dict[str, Any] = {}

    for train_idx, test_idx in expanding_window_split(len(X), config["test_size"]):
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        model.fit(X_train, y_train)
        tree_model.fit(X_train, y_train)
        quantile_low.fit(X_train, y_train)
        quantile_high.fit(X_train, y_train)

        ridge_pred = model.predict(X_test)
        tree_pred = tree_model.predict(X_test)
        low_pred = quantile_low.predict(X_test)
        high_pred = quantile_high.predict(X_test)

        metrics["ridge"] = regression_metrics(y_test, ridge_pred)
        metrics["tree"] = regression_metrics(y_test, tree_pred)
        metrics["interval_coverage"] = interval_coverage(y_test, low_pred, high_pred)

    best_model = tree_model
    best_model_path = output_dir / "model.pkl"
    joblib.dump(best_model, best_model_path)

    quantile_low_path = output_dir / "quantile_low.pkl"
    quantile_high_path = output_dir / "quantile_high.pkl"
    joblib.dump(quantile_low, quantile_low_path)
    joblib.dump(quantile_high, quantile_high_path)

    schema = FeatureSchema(columns=list(features.columns))
    feature_schema_path = output_dir / "feature_schema.json"
    feature_schema_path.write_text(json.dumps(schema.to_dict(), indent=2))

    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2))

    config_path = output_dir / "training_config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    artifacts = TrainingArtifacts(
        model_path=best_model_path,
        quantile_low_path=quantile_low_path,
        quantile_high_path=quantile_high_path,
        feature_schema_path=feature_schema_path,
        metrics_path=metrics_path,
        config_path=config_path,
    )
    return artifacts, metrics
