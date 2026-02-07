from __future__ import annotations

import pandas as pd

from src.data.feature_engineering import FeatureConfig, FeatureEngineer


def test_feature_engineering_rolling_no_leakage() -> None:
    df = pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-05",
                "2024-01-10",
                "2024-01-15",
            ],
            "league": ["NBA", "NBA", "NBA", "NBA"],
            "home_team": ["A", "B", "A", "B"],
            "away_team": ["B", "A", "B", "A"],
            "home_score": [100, 95, 110, 90],
            "away_score": [90, 105, 98, 102],
            "total": [190, 200, 208, 192],
        }
    )
    df["date"] = pd.to_datetime(df["date"])

    engineer = FeatureEngineer(FeatureConfig(rolling_window=2))
    features, _ = engineer.build_features(df)

    first_game = features.iloc[0]
    assert first_game["home_roll_total"] == 0.0
    assert first_game["away_roll_total"] == 0.0

    second_game = features.iloc[1]
    assert second_game["home_roll_total"] == 190
    assert second_game["away_roll_total"] == 190
