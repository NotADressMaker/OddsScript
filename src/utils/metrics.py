"""Evaluation metrics for regression."""

from __future__ import annotations

from typing import Dict

import numpy as np


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.clip(y_true, 1e-6, None))))
    return {"mae": mae, "rmse": rmse, "mape": mape}


def interval_coverage(
    y_true: np.ndarray, low: np.ndarray, high: np.ndarray
) -> float:
    covered = (y_true >= low) & (y_true <= high)
    return float(np.mean(covered))
