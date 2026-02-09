"""Feature engineering for totals (O/U) regression models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from src.data.schema import ALL_COLUMNS

@dataclass
class FeatureConfig:
    rolling_window: int = 10


class FeatureEngineer:
    """Build rolling features for totals prediction with leakage prevention."""

    def __init__(self, config: FeatureConfig) -> None:
        self.config = config

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = pd.NA
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values("date")
        df["neutral_site"] = df["neutral_site"].fillna(False).astype(bool)
        for col in ["home_rest_days", "away_rest_days", "injuries_home", "injuries_away"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        for col in ["home_travel_distance", "away_travel_distance", "xg_home", "xg_away"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["pace_proxy"] = pd.to_numeric(df["pace_proxy"], errors="coerce")
        df["weather"] = pd.to_numeric(df["weather"], errors="coerce")
        df["closing_total"] = pd.to_numeric(df["closing_total"], errors="coerce")
        df["total"] = pd.to_numeric(df["total"], errors="coerce")
        return df

    def build_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        df = self.prepare(df)
        league_min_date = df.groupby("league")["date"].transform("min")
        df["month"] = df["date"].dt.month.fillna(1)
        df["week_of_season"] = ((df["date"] - league_min_date).dt.days // 7).fillna(0)

        long_df = self._to_long(df)
        long_df = self._add_rolling_stats(long_df)
        merged = self._merge_back(df, long_df)

        features = self._select_features(merged)
        target = merged["total"].astype(float)
        return features, target

    def _to_long(self, df: pd.DataFrame) -> pd.DataFrame:
        home = df[[
            "date",
            "league",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "total",
            "pace_proxy",
            "neutral_site",
            "xg_home",
            "xg_away",
        ]].rename(
            columns={
                "home_team": "team",
                "away_team": "opponent",
                "home_score": "points_for",
                "away_score": "points_against",
                "xg_home": "xg_for",
                "xg_away": "xg_against",
            }
        )
        home["is_home"] = 1
        away = df[[
            "date",
            "league",
            "away_team",
            "home_team",
            "away_score",
            "home_score",
            "total",
            "pace_proxy",
            "neutral_site",
            "xg_away",
            "xg_home",
        ]].rename(
            columns={
                "away_team": "team",
                "home_team": "opponent",
                "away_score": "points_for",
                "home_score": "points_against",
                "xg_away": "xg_for",
                "xg_home": "xg_against",
            }
        )
        away["is_home"] = 0
        home["is_draw"] = (home["points_for"] == home["points_against"]).astype(int)
        away["is_draw"] = (away["points_for"] == away["points_against"]).astype(int)
        long_df = pd.concat([home, away], ignore_index=True)
        long_df = long_df.sort_values(["league", "team", "date"]).reset_index(drop=True)
        return long_df

    def _add_rolling_stats(self, long_df: pd.DataFrame) -> pd.DataFrame:
        window = self.config.rolling_window
        group = long_df.groupby(["league", "team"], sort=False)

        long_df["roll_points_for"] = group["points_for"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_points_against"] = group["points_against"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_total"] = group["total"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_total_var"] = group["total"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).var()
        ).fillna(0.0)
        long_df["roll_pace"] = group["pace_proxy"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_off_rating"] = group["points_for"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_def_rating"] = group["points_against"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        long_df["roll_draw_rate"] = group["is_draw"].transform(
            lambda s: s.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.0)
        return long_df

    def _merge_back(self, df: pd.DataFrame, long_df: pd.DataFrame) -> pd.DataFrame:
        home_features = long_df[long_df["is_home"] == 1].rename(
            columns={
                "team": "home_team",
                "opponent": "away_team",
                "roll_points_for": "home_roll_points_for",
                "roll_points_against": "home_roll_points_against",
                "roll_total": "home_roll_total",
                "roll_total_var": "home_roll_total_var",
                "roll_pace": "home_roll_pace",
                "roll_off_rating": "home_roll_off_rating",
                "roll_def_rating": "home_roll_def_rating",
                "roll_draw_rate": "home_roll_draw_rate",
            }
        )
        away_features = long_df[long_df["is_home"] == 0].rename(
            columns={
                "team": "away_team",
                "opponent": "home_team",
                "roll_points_for": "away_roll_points_for",
                "roll_points_against": "away_roll_points_against",
                "roll_total": "away_roll_total",
                "roll_total_var": "away_roll_total_var",
                "roll_pace": "away_roll_pace",
                "roll_off_rating": "away_roll_off_rating",
                "roll_def_rating": "away_roll_def_rating",
                "roll_draw_rate": "away_roll_draw_rate",
            }
        )
        merged = df.merge(
            home_features[[
                "date",
                "league",
                "home_team",
                "away_team",
                "home_roll_points_for",
                "home_roll_points_against",
                "home_roll_total",
                "home_roll_total_var",
                "home_roll_pace",
                "home_roll_off_rating",
                "home_roll_def_rating",
                "home_roll_draw_rate",
            ]],
            on=["date", "league", "home_team", "away_team"],
            how="left",
        )
        merged = merged.merge(
            away_features[[
                "date",
                "league",
                "home_team",
                "away_team",
                "away_roll_points_for",
                "away_roll_points_against",
                "away_roll_total",
                "away_roll_total_var",
                "away_roll_pace",
                "away_roll_off_rating",
                "away_roll_def_rating",
                "away_roll_draw_rate",
            ]],
            on=["date", "league", "home_team", "away_team"],
            how="left",
        )
        return merged.sort_values("date").reset_index(drop=True)

    def _select_features(self, df: pd.DataFrame) -> pd.DataFrame:
        features = pd.DataFrame(
            {
                "home_roll_points_for": df["home_roll_points_for"],
                "away_roll_points_for": df["away_roll_points_for"],
                "home_roll_points_against": df["home_roll_points_against"],
                "away_roll_points_against": df["away_roll_points_against"],
                "home_roll_total": df["home_roll_total"],
                "away_roll_total": df["away_roll_total"],
                "home_roll_total_var": df["home_roll_total_var"],
                "away_roll_total_var": df["away_roll_total_var"],
                "home_roll_pace": df["home_roll_pace"],
                "away_roll_pace": df["away_roll_pace"],
                "home_roll_off_rating": df["home_roll_off_rating"],
                "away_roll_off_rating": df["away_roll_off_rating"],
                "home_roll_def_rating": df["home_roll_def_rating"],
                "away_roll_def_rating": df["away_roll_def_rating"],
                "home_roll_draw_rate": df["home_roll_draw_rate"],
                "away_roll_draw_rate": df["away_roll_draw_rate"],
                "home_rest_days": df["home_rest_days"],
                "away_rest_days": df["away_rest_days"],
                "injuries_home": df["injuries_home"],
                "injuries_away": df["injuries_away"],
                "home_travel_distance": df["home_travel_distance"],
                "away_travel_distance": df["away_travel_distance"],
                "neutral_site": df["neutral_site"].astype(int),
                "pace_proxy": df["pace_proxy"],
                "weather": df["weather"],
                "closing_total": df["closing_total"],
                "xg_home": df["xg_home"],
                "xg_away": df["xg_away"],
                "month": df["month"],
                "week_of_season": df["week_of_season"],
            }
        )
        return features.fillna(features.mean(numeric_only=True)).fillna(0.0)


@dataclass
class FeatureSchema:
    columns: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {"columns": self.columns}
