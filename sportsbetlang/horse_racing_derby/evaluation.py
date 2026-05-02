from __future__ import annotations

import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score


class DerbyEvaluator:
    @staticmethod
    def evaluate(y_true, y_prob) -> dict:
        return {
            "brier": float(brier_score_loss(y_true, y_prob)),
            "log_loss": float(log_loss(y_true, y_prob, labels=[0, 1])),
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
        }

    @staticmethod
    def value_bet_summary(scored_df: pd.DataFrame) -> pd.DataFrame:
        subset = scored_df[scored_df["is_value_bet"]].copy()
        if subset.empty:
            return pd.DataFrame({"count": [0], "avg_edge_probability": [0.0]})
        return pd.DataFrame(
            {
                "count": [int(len(subset))],
                "avg_edge_probability": [float(subset["edge_probability"].mean())],
            }
        )
