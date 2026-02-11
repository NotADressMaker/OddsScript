"""NHL totals probability models (Poisson and Negative Binomial variants)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from sportsbetlang.features.nhl_totals_features import (
    NHLTotalsFeatureConfig,
    build_nhl_totals_features,
)


class SettlementRule(str, Enum):
    """Rule for total-goal settlement around shootouts."""

    INCLUDE_SHOOTOUT_DECIDER = "include_shootout_decider"
    EXCLUDE_SHOOTOUT_DECIDER = "exclude_shootout_decider"


@dataclass(frozen=True)
class CVConfig:
    """Rolling CV options."""

    min_train_games: int = 150
    step_size: int = 25


@dataclass(frozen=True)
class FeatureConfig:
    """Feature generation options."""

    rolling_window: int = 10
    min_periods: int = 3


@dataclass
class NHLTotalsModel:
    """Fitted NHL totals model.

    The model supports three distribution modes:
    - ``poisson``: variance equals mean.
    - ``negative_binomial``: NB2 with estimated dispersion.
    - ``shared_tempo``: Gamma-Poisson mixture interpretation (same NB2 math, different semantics).
    """

    distribution: str = "negative_binomial"
    settlement_rule: SettlementRule = SettlementRule.INCLUDE_SHOOTOUT_DECIDER
    league_mean_total: float = 6.0
    home_advantage: float = 0.0
    attack: dict[str, float] | None = None
    defense: dict[str, float] | None = None
    dispersion_r: float = 1e9
    calibration: IsotonicRegression | None = None

    def _expected_team_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        attack_home = (self.attack or {}).get(home_team, 0.0)
        defense_home = (self.defense or {}).get(home_team, 0.0)
        attack_away = (self.attack or {}).get(away_team, 0.0)
        defense_away = (self.defense or {}).get(away_team, 0.0)

        base = max(self.league_mean_total / 2.0, 0.25)
        mu_home = base * math.exp(self.home_advantage + attack_home - defense_away)
        mu_away = base * math.exp(-self.home_advantage + attack_away - defense_home)
        return max(mu_home, 0.01), max(mu_away, 0.01)

    def predict_proba(
        self, upcoming_games_df: pd.DataFrame, line_col: str = "total_line"
    ) -> pd.DataFrame:
        """Return probabilities and moments for totals markets."""

        rows: list[dict[str, Any]] = []
        for _, row in upcoming_games_df.iterrows():
            mu_home, mu_away = self._expected_team_goals(row["home_team"], row["away_team"])
            mu_total = mu_home + mu_away

            if self.distribution == "poisson":
                var_total = mu_total
                pmf = _poisson_pmf_array(mu_total)
            else:
                r = max(self.dispersion_r, 1e-6)
                var_total = mu_total + (mu_total**2) / r
                pmf = _nb2_pmf_array(mu_total, r)

            line = float(row.get(line_col, np.nan))
            if np.isnan(line):
                raise ValueError(f"Missing line column '{line_col}'")

            if abs(line - round(line)) < 1e-9:
                push_goal = int(round(line))
                p_push = float(pmf[push_goal] if push_goal < len(pmf) else 0.0)
                p_over = float(pmf[push_goal + 1 :].sum())
                p_under = max(0.0, 1.0 - p_over - p_push)
            else:
                threshold = int(math.floor(line)) + 1
                p_push = 0.0
                p_over = float(pmf[threshold:].sum())
                p_under = max(0.0, 1.0 - p_over)

            p_over_raw = p_over
            if self.calibration is not None:
                p_over = float(self.calibration.predict([p_over])[0])
                p_under = max(0.0, 1.0 - p_over - p_push)

            fair_over_odds = 1.0 / p_over if p_over > 0 else np.inf
            fair_under_odds = 1.0 / p_under if p_under > 0 else np.inf

            out = row.to_dict()
            out.update(
                {
                    "mean_total": mu_total,
                    "var_total": var_total,
                    "p_over": p_over,
                    "p_under": p_under,
                    "p_push": p_push,
                    "p_over_raw": p_over_raw,
                    "fair_over_decimal": fair_over_odds,
                    "fair_under_decimal": fair_under_odds,
                }
            )
            rows.append(out)

        return pd.DataFrame(rows)

    def diagnostics(
        self, games_df: pd.DataFrame, line_col: str = "total_line", bins: int = 10
    ) -> dict[str, Any]:
        """Compute calibration and fit diagnostics."""

        pred_df = self.predict_proba(games_df, line_col=line_col)
        labels = _label_over(games_df, line_col, self.settlement_rule)
        p = pred_df["p_over"].to_numpy(dtype=float)

        eps = 1e-9
        p = np.clip(p, eps, 1 - eps)
        log_loss = float(-np.mean(labels * np.log(p) + (1 - labels) * np.log(1 - p)))
        brier = float(np.mean((p - labels) ** 2))

        observed_totals = _total_from_settlement(games_df, self.settlement_rule)
        mean_total = float(pred_df["mean_total"].mean())
        var_total = float(pred_df["var_total"].mean())
        obs_mean = float(np.mean(observed_totals))
        obs_var = float(np.var(observed_totals))

        rel = _reliability_data(p, labels, bins=bins)

        return {
            "log_loss": log_loss,
            "brier": brier,
            "mean_total_pred": mean_total,
            "var_total_pred": var_total,
            "mean_total_obs": obs_mean,
            "var_total_obs": obs_var,
            "variance_gap": var_total - obs_var,
            "reliability": rel,
        }


def fit(
    games_df: pd.DataFrame,
    *,
    settlement_rule: SettlementRule,
    feature_config: FeatureConfig | None = None,
    cv_config: CVConfig | None = None,
    distribution: str = "negative_binomial",
    calibrate: bool = True,
) -> NHLTotalsModel:
    """Fit NHL totals model from historical games."""

    if settlement_rule not in set(SettlementRule):
        raise ValueError(f"Unknown settlement rule: {settlement_rule}")
    if distribution not in {"poisson", "negative_binomial", "shared_tempo"}:
        raise ValueError("distribution must be one of: poisson, negative_binomial, shared_tempo")

    df = games_df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)

    feat_cfg = feature_config or FeatureConfig()
    _ = build_nhl_totals_features(
        df,
        NHLTotalsFeatureConfig(
            rolling_window=feat_cfg.rolling_window, min_periods=feat_cfg.min_periods
        ),
    )

    totals = _total_from_settlement(df, settlement_rule)
    league_mean_total = float(np.mean(totals))
    home_mean = float(np.mean(df["home_goals"]))
    away_mean = float(np.mean(df["away_goals"]))
    home_advantage = 0.5 * math.log(max(home_mean, 1e-6) / max(away_mean, 1e-6))

    teams = sorted(set(df["home_team"]).union(set(df["away_team"])))
    attack: dict[str, float] = {}
    defense: dict[str, float] = {}
    gm = league_mean_total / 2.0

    for team in teams:
        is_home = df["home_team"] == team
        is_away = df["away_team"] == team
        goals_for = pd.concat([df.loc[is_home, "home_goals"], df.loc[is_away, "away_goals"]])
        goals_against = pd.concat([df.loc[is_home, "away_goals"], df.loc[is_away, "home_goals"]])
        attack[team] = math.log((float(goals_for.mean()) + 0.1) / (gm + 0.1))
        defense[team] = math.log((float(goals_against.mean()) + 0.1) / (gm + 0.1))

    observed_var = float(np.var(totals))
    observed_mean = float(np.mean(totals))
    if observed_var <= observed_mean + 1e-9:
        dispersion_r = 1e9
    else:
        dispersion_r = (observed_mean**2) / (observed_var - observed_mean)

    model = NHLTotalsModel(
        distribution=distribution,
        settlement_rule=settlement_rule,
        league_mean_total=league_mean_total,
        home_advantage=home_advantage,
        attack=attack,
        defense=defense,
        dispersion_r=dispersion_r,
    )

    if calibrate and "total_line" in df.columns and len(df) >= 100:
        cv = cv_config or CVConfig()
        split = max(cv.min_train_games, int(len(df) * 0.7))
        split = min(split, len(df) - 1)
        train = df.iloc[:split]
        valid = df.iloc[split:]
        calib_model = fit(
            train,
            settlement_rule=settlement_rule,
            feature_config=feature_config,
            cv_config=cv_config,
            distribution=distribution,
            calibrate=False,
        )
        valid_pred = calib_model.predict_proba(valid, line_col="total_line")
        y_valid = _label_over(valid, "total_line", settlement_rule)
        iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
        iso.fit(valid_pred["p_over"], y_valid)
        model.calibration = iso

    return model


def _total_from_settlement(df: pd.DataFrame, rule: SettlementRule) -> np.ndarray:
    if rule == SettlementRule.INCLUDE_SHOOTOUT_DECIDER:
        return df["home_goals"].to_numpy(dtype=float) + df["away_goals"].to_numpy(dtype=float)

    if "went_to_shootout" not in df.columns:
        raise ValueError("went_to_shootout column required for EXCLUDE_SHOOTOUT_DECIDER")
    base = df["home_goals"].to_numpy(dtype=float) + df["away_goals"].to_numpy(dtype=float)
    so = df["went_to_shootout"].fillna(False).to_numpy(dtype=bool)
    return base - so.astype(float)


def _label_over(df: pd.DataFrame, line_col: str, rule: SettlementRule) -> np.ndarray:
    totals = _total_from_settlement(df, rule)
    line = df[line_col].to_numpy(dtype=float)
    labels = np.zeros(len(df), dtype=float)
    for i, (total, line_value) in enumerate(zip(totals, line, strict=True)):
        if abs(line_value - round(line_value)) < 1e-9:
            labels[i] = float(total >= int(round(line_value)) + 1)
        else:
            labels[i] = float(total > line_value)
    return labels


def _poisson_pmf_array(mu: float, max_goal: int | None = None) -> np.ndarray:
    upper = max_goal or int(max(15, math.ceil(mu + 8 * math.sqrt(max(mu, 1e-6)) + 5)))
    pmf = np.zeros(upper + 1)
    pmf[0] = math.exp(-mu)
    for k in range(1, upper + 1):
        pmf[k] = pmf[k - 1] * mu / k
    s = pmf.sum()
    return pmf / s if s > 0 else pmf


def _nb2_pmf_array(mu: float, r: float, max_goal: int | None = None) -> np.ndarray:
    upper = max_goal or int(
        max(20, math.ceil(mu + 10 * math.sqrt(max(mu + (mu**2) / max(r, 1e-6), 1e-6)) + 5))
    )
    p = r / (r + mu)
    q = 1.0 - p
    pmf = np.zeros(upper + 1)
    for k in range(upper + 1):
        logpmf = (
            math.lgamma(k + r)
            - math.lgamma(r)
            - math.lgamma(k + 1)
            + r * math.log(p)
            + k * math.log(q)
        )
        pmf[k] = math.exp(logpmf)
    s = pmf.sum()
    return pmf / s if s > 0 else pmf


def _reliability_data(pred: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict[str, float]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (pred >= lo) & (pred < hi if hi < 1 else pred <= hi)
        if not np.any(mask):
            out.append(
                {
                    "bin_low": float(lo),
                    "bin_high": float(hi),
                    "count": 0.0,
                    "pred_mean": np.nan,
                    "obs_rate": np.nan,
                }
            )
            continue
        out.append(
            {
                "bin_low": float(lo),
                "bin_high": float(hi),
                "count": float(mask.sum()),
                "pred_mean": float(pred[mask].mean()),
                "obs_rate": float(y[mask].mean()),
            }
        )
    return out
