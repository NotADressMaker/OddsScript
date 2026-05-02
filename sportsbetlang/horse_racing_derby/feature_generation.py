from __future__ import annotations

import numpy as np
import pandas as pd


class DerbyFeatureGenerator:
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        data["horse_speed_avg_3"] = (
            data.groupby("horse")["speed_figure"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
        )
        data["horse_days_since_last"] = (
            data.groupby("horse")["race_date"].diff().dt.days.fillna(30)
        )
        data["jockey_win_rate_lookback"] = (
            data.groupby("jockey")["won"].transform(lambda s: s.shift(1).rolling(25, min_periods=5).mean())
        ).fillna(data["won"].mean())
        data["trainer_win_rate_lookback"] = (
            data.groupby("trainer")["won"].transform(lambda s: s.shift(1).rolling(25, min_periods=5).mean())
        ).fillna(data["won"].mean())
        data["is_sloppy_or_muddy"] = data["track_condition"].str.lower().isin(["sloppy", "muddy"]).astype(int)
        data["market_implied_prob"] = 1 / data["market_odds_decimal"].clip(lower=1.01)

        data["horse_speed_avg_3"] = data["horse_speed_avg_3"].fillna(data["speed_figure"].median())
        data = data.replace([np.inf, -np.inf], np.nan).fillna(0.0)
        return data

    @staticmethod
    def feature_columns() -> list[str]:
        return [
            "speed_figure",
            "horse_speed_avg_3",
            "horse_days_since_last",
            "distance_furlongs",
            "jockey_win_rate_lookback",
            "trainer_win_rate_lookback",
            "is_sloppy_or_muddy",
            "market_implied_prob",
        ]
