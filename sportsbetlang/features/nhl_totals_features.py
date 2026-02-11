"""NHL totals feature engineering with strict past-only rolling windows."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class NHLTotalsFeatureConfig:
    """Configuration for NHL totals feature generation."""

    rolling_window: int = 10
    min_periods: int = 3


_REQUIRED_BASE_COLUMNS = {"date", "home_team", "away_team", "home_goals", "away_goals"}


def _validate_games_df(games_df: pd.DataFrame) -> None:
    missing = sorted(_REQUIRED_BASE_COLUMNS - set(games_df.columns))
    if missing:
        raise ValueError(f"games_df missing required columns: {missing}")


def build_nhl_totals_features(
    games_df: pd.DataFrame,
    config: NHLTotalsFeatureConfig | None = None,
) -> pd.DataFrame:
    """Build past-only features for NHL totals modeling.

    The returned frame keeps the original rows and appends engineered columns.
    All rolling features use ``shift(1)`` before rolling calculations to prevent leakage.
    """

    cfg = config or NHLTotalsFeatureConfig()
    _validate_games_df(games_df)

    df = games_df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)
    df["game_id"] = np.arange(len(df))

    home = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "date": df["date"],
            "team": df["home_team"],
            "opp": df["away_team"],
            "is_home": 1,
            "goals_for": df["home_goals"],
            "goals_against": df["away_goals"],
            "shots_for": df.get("home_shots", np.nan),
            "shots_against": df.get("away_shots", np.nan),
            "xg_for": df.get("home_xg", np.nan),
            "xg_against": df.get("away_xg", np.nan),
            "pp_opps": df.get("home_pp_opps", np.nan),
            "pp_goals": df.get("home_pp_goals", np.nan),
            "pk_opps": df.get("home_pk_opps", np.nan),
            "pk_goals_against": df.get("home_pk_goals_against", np.nan),
            "saves": df.get("home_saves", np.nan),
            "shots_on_goal_against": df.get("away_shots", np.nan),
        }
    )
    away = pd.DataFrame(
        {
            "game_id": df["game_id"],
            "date": df["date"],
            "team": df["away_team"],
            "opp": df["home_team"],
            "is_home": 0,
            "goals_for": df["away_goals"],
            "goals_against": df["home_goals"],
            "shots_for": df.get("away_shots", np.nan),
            "shots_against": df.get("home_shots", np.nan),
            "xg_for": df.get("away_xg", np.nan),
            "xg_against": df.get("home_xg", np.nan),
            "pp_opps": df.get("away_pp_opps", np.nan),
            "pp_goals": df.get("away_pp_goals", np.nan),
            "pk_opps": df.get("away_pk_opps", np.nan),
            "pk_goals_against": df.get("away_pk_goals_against", np.nan),
            "saves": df.get("away_saves", np.nan),
            "shots_on_goal_against": df.get("home_shots", np.nan),
        }
    )

    long_df = pd.concat([home, away], ignore_index=True).sort_values(["team", "date", "game_id"])

    grouped = long_df.groupby("team", group_keys=False)
    long_df["days_rest"] = grouped["date"].diff().dt.total_seconds().div(86400.0)
    long_df["days_rest"] = long_df["days_rest"].fillna(5.0).clip(lower=0.0)
    long_df["is_back_to_back"] = (long_df["days_rest"] <= 1.5).astype(float)

    long_df["three_in_four"] = 0.0
    for _team, idx in grouped.indices.items():
        dates = long_df.loc[idx, "date"].sort_values().to_numpy(dtype="datetime64[D]")
        flags = np.zeros(len(dates), dtype=float)
        for i in range(len(dates)):
            start = dates[i] - np.timedelta64(3, "D")
            flags[i] = float(np.sum((dates[: i + 1] >= start) & (dates[: i + 1] <= dates[i])) >= 3)
        long_df.loc[long_df.loc[idx].sort_values("date").index, "three_in_four"] = flags

    def _rolling_past(series: pd.Series) -> pd.Series:
        return series.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).mean()

    long_df["roll_goals_for"] = grouped["goals_for"].transform(_rolling_past)
    long_df["roll_goals_against"] = grouped["goals_against"].transform(_rolling_past)

    long_df["roll_shots_for"] = grouped["shots_for"].transform(_rolling_past)
    long_df["roll_shots_against"] = grouped["shots_against"].transform(_rolling_past)

    long_df["roll_xg_for"] = grouped["xg_for"].transform(_rolling_past)
    long_df["roll_xg_against"] = grouped["xg_against"].transform(_rolling_past)

    long_df["pp_rate"] = grouped["pp_goals"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    ) / grouped["pp_opps"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    ).replace(0, np.nan)

    long_df["pk_rate"] = 1.0 - grouped["pk_goals_against"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    ) / grouped["pk_opps"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    ).replace(0, np.nan)

    saves_sum = grouped["saves"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    )
    soga_sum = grouped["shots_on_goal_against"].transform(
        lambda s: s.shift(1).rolling(cfg.rolling_window, min_periods=cfg.min_periods).sum()
    )
    long_df["goalie_save_pct"] = saves_sum / soga_sum.replace(0, np.nan)

    long_df["pace_proxy"] = long_df[["roll_shots_for", "roll_shots_against"]].mean(axis=1)
    long_df["xg_process"] = long_df[["roll_xg_for", "roll_xg_against"]].mean(axis=1)

    home_feat = long_df[long_df["is_home"] == 1].set_index("game_id")
    away_feat = long_df[long_df["is_home"] == 0].set_index("game_id")

    out = df.set_index("game_id")
    feature_cols = [
        "days_rest",
        "is_back_to_back",
        "three_in_four",
        "roll_goals_for",
        "roll_goals_against",
        "pace_proxy",
        "xg_process",
        "pp_rate",
        "pk_rate",
        "goalie_save_pct",
    ]
    for col in feature_cols:
        out[f"home_{col}"] = home_feat[col]
        out[f"away_{col}"] = away_feat[col]

    # Total-level features
    out["rest_delta"] = out["home_days_rest"] - out["away_days_rest"]
    out["schedule_stress"] = out["home_three_in_four"] + out["away_three_in_four"]
    out["pace_sum"] = out[["home_pace_proxy", "away_pace_proxy"]].sum(axis=1)
    out["xg_sum"] = out[["home_xg_process", "away_xg_process"]].sum(axis=1)
    out["special_teams_index"] = out[
        ["home_pp_rate", "away_pp_rate", "home_pk_rate", "away_pk_rate"]
    ].mean(axis=1)
    out["goalie_form_index"] = out[["home_goalie_save_pct", "away_goalie_save_pct"]].mean(axis=1)

    return out.reset_index(drop=True)
