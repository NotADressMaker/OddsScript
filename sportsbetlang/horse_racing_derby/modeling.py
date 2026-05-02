from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression


class DerbyWinModel:
    def __init__(self):
        self.model = LogisticRegression(max_iter=2000, class_weight="balanced")

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "DerbyWinModel":
        self.model.fit(X, y)
        return self

    def predict_win_probability(self, X: pd.DataFrame):
        return self.model.predict_proba(X)[:, 1]
