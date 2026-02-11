"""Backtesting and calibration evaluation for NHL totals models."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

from sportsbetlang.models.nhl_totals import CVConfig, SettlementRule, fit


@dataclass(frozen=True)
class RollingOriginConfig:
    min_train_games: int = 200
    step_size: int = 25
    expanding: bool = True


def rolling_origin_backtest(
    games_df: pd.DataFrame,
    *,
    settlement_rule: SettlementRule,
    distribution: str = "negative_binomial",
    cv_config: RollingOriginConfig | None = None,
    line_col: str = "total_line",
) -> dict[str, object]:
    """Run rolling-origin backtest and return predictions + metrics."""

    cfg = cv_config or RollingOriginConfig()
    df = games_df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df.sort_values("date").reset_index(drop=True)

    all_pred = []
    for split in range(cfg.min_train_games, len(df), cfg.step_size):
        train_start = 0 if cfg.expanding else max(0, split - cfg.min_train_games)
        train = df.iloc[train_start:split]
        test = df.iloc[split : min(split + cfg.step_size, len(df))]
        if test.empty:
            continue
        model = fit(
            train,
            settlement_rule=settlement_rule,
            cv_config=CVConfig(min_train_games=cfg.min_train_games, step_size=cfg.step_size),
            distribution=distribution,
            calibrate=False,
        )
        pred = model.predict_proba(test, line_col=line_col)
        pred["total_obs"] = test["home_goals"].to_numpy() + test["away_goals"].to_numpy()
        pred["is_over"] = _labels(test, settlement_rule, line_col)
        all_pred.append(pred)

    if not all_pred:
        raise ValueError("Insufficient rows for rolling-origin backtest")

    pred_df = pd.concat(all_pred, ignore_index=True)
    p = np.clip(pred_df["p_over"].to_numpy(dtype=float), 1e-9, 1 - 1e-9)
    y = pred_df["is_over"].to_numpy(dtype=float)

    log_loss = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    brier = float(np.mean((p - y) ** 2))
    ece = expected_calibration_error(p, y)

    return {
        "predictions": pred_df,
        "metrics": {
            "log_loss": log_loss,
            "brier": brier,
            "ece": ece,
            "pred_var_mean": float(pred_df["var_total"].mean()),
            "obs_var": float(np.var(pred_df["total_obs"])),
        },
        "reliability": reliability_diagram_data(p, y),
    }


def fit_isotonic_calibration(pred_proba: np.ndarray, labels: np.ndarray) -> IsotonicRegression:
    """Fit isotonic calibration model."""

    iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
    iso.fit(pred_proba, labels)
    return iso


def reliability_diagram_data(
    pred_proba: np.ndarray, labels: np.ndarray, bins: int = 10
) -> pd.DataFrame:
    """Build reliability diagram bin summary."""

    pred_proba = np.asarray(pred_proba, dtype=float)
    labels = np.asarray(labels, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)

    rows = []
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        mask = (pred_proba >= lo) & (pred_proba < hi if hi < 1 else pred_proba <= hi)
        if np.any(mask):
            rows.append(
                {
                    "bin_low": lo,
                    "bin_high": hi,
                    "count": int(mask.sum()),
                    "pred_mean": float(pred_proba[mask].mean()),
                    "obs_rate": float(labels[mask].mean()),
                }
            )
        else:
            rows.append(
                {"bin_low": lo, "bin_high": hi, "count": 0, "pred_mean": np.nan, "obs_rate": np.nan}
            )
    return pd.DataFrame(rows)


def expected_calibration_error(pred_proba: np.ndarray, labels: np.ndarray, bins: int = 10) -> float:
    """Compute ECE."""

    rel = reliability_diagram_data(pred_proba, labels, bins=bins)
    total = max(rel["count"].sum(), 1)
    ece = 0.0
    for _, row in rel.dropna(subset=["pred_mean", "obs_rate"]).iterrows():
        ece += (row["count"] / total) * abs(row["pred_mean"] - row["obs_rate"])
    return float(ece)


def remove_vig_two_way(over_odds_decimal: float, under_odds_decimal: float) -> tuple[float, float]:
    """Convert two-way decimal odds to fair probabilities with proportional overround removal."""

    imp_over = 1.0 / over_odds_decimal
    imp_under = 1.0 / under_odds_decimal
    total = imp_over + imp_under
    return imp_over / total, imp_under / total


def remove_vig_asymmetric(
    over_odds_decimal: float,
    under_odds_decimal: float,
    over_margin_share: float,
) -> tuple[float, float]:
    """Remove vig with asymmetric margin split.

    ``over_margin_share`` sets the share of overround assigned to the over side.
    """

    imp_over = 1.0 / over_odds_decimal
    imp_under = 1.0 / under_odds_decimal
    overround = (imp_over + imp_under) - 1.0
    over_adj = imp_over - overround * over_margin_share
    under_adj = imp_under - overround * (1.0 - over_margin_share)
    z = over_adj + under_adj
    return over_adj / z, under_adj / z


def conservative_kelly(prob: float, odds_decimal: float, fraction: float = 0.25) -> float:
    """Fractional Kelly stake fraction."""

    b = odds_decimal - 1.0
    if b <= 0:
        return 0.0
    raw = (prob * odds_decimal - 1.0) / b
    return max(0.0, raw * fraction)


def _labels(df: pd.DataFrame, settlement_rule: SettlementRule, line_col: str) -> np.ndarray:
    totals = df["home_goals"].to_numpy(dtype=float) + df["away_goals"].to_numpy(dtype=float)
    if settlement_rule == SettlementRule.EXCLUDE_SHOOTOUT_DECIDER:
        totals = totals - df["went_to_shootout"].fillna(False).to_numpy(dtype=bool).astype(float)

    labels = []
    for total, line in zip(totals, df[line_col].to_numpy(dtype=float), strict=True):
        if abs(line - round(line)) < 1e-9:
            labels.append(float(total >= int(round(line)) + 1))
        else:
            labels.append(float(total > line))
    return np.array(labels, dtype=float)
