from __future__ import annotations

import numpy as np
import pandas as pd

from sportsbetlang.eval.nhl_totals_eval import fit_isotonic_calibration
from sportsbetlang.features.nhl_totals_features import build_nhl_totals_features
from sportsbetlang.models.nhl_totals import SettlementRule, fit

TEAMS = ["A", "B", "C", "D"]


def _schedule(n_games: int) -> pd.DataFrame:
    rows = []
    date = pd.Timestamp("2023-10-01")
    for i in range(n_games):
        h = TEAMS[i % len(TEAMS)]
        a = TEAMS[(i + 1) % len(TEAMS)]
        rows.append(
            {"date": date + pd.Timedelta(days=i), "home_team": h, "away_team": a, "total_line": 6.5}
        )
    return pd.DataFrame(rows)


def test_poisson_world_model_outputs_reasonable_probabilities() -> None:
    rng = np.random.default_rng(0)
    df = _schedule(400)
    df["home_goals"] = rng.poisson(3.2, size=len(df))
    df["away_goals"] = rng.poisson(2.8, size=len(df))
    df["went_to_shootout"] = False

    model = fit(df, settlement_rule=SettlementRule.INCLUDE_SHOOTOUT_DECIDER, distribution="poisson")
    pred = model.predict_proba(df.iloc[-50:])

    assert pred["p_over"].between(0, 1).all()
    assert pred["p_under"].between(0, 1).all()
    assert abs(pred["mean_total"].mean() - 6.0) < 0.8


def test_overdispersed_world_nb_beats_poisson_log_loss() -> None:
    rng = np.random.default_rng(1)
    df = _schedule(500)
    shared = rng.gamma(shape=2.5, scale=1 / 2.5, size=len(df))
    df["home_goals"] = rng.poisson(3.0 * shared)
    df["away_goals"] = rng.poisson(2.8 * shared)
    df["went_to_shootout"] = False

    pois = fit(
        df.iloc[:350],
        settlement_rule=SettlementRule.INCLUDE_SHOOTOUT_DECIDER,
        distribution="poisson",
    )
    nb = fit(
        df.iloc[:350],
        settlement_rule=SettlementRule.INCLUDE_SHOOTOUT_DECIDER,
        distribution="negative_binomial",
    )

    pois_diag = pois.diagnostics(df.iloc[350:])
    nb_diag = nb.diagnostics(df.iloc[350:])

    assert nb_diag["log_loss"] <= pois_diag["log_loss"] + 1e-6


def test_settlement_rule_changes_labels_for_shootout_games() -> None:
    df = _schedule(4)
    df["home_goals"] = [3, 2, 4, 3]
    df["away_goals"] = [3, 2, 2, 3]
    df["went_to_shootout"] = [True, False, False, True]
    df["total_line"] = [6.0, 4.5, 5.5, 6.0]

    inc = fit(df, settlement_rule=SettlementRule.INCLUDE_SHOOTOUT_DECIDER, calibrate=False)
    exc = fit(df, settlement_rule=SettlementRule.EXCLUDE_SHOOTOUT_DECIDER, calibrate=False)

    inc_diag = inc.diagnostics(df)
    exc_diag = exc.diagnostics(df)

    assert inc_diag["mean_total_obs"] > exc_diag["mean_total_obs"]


def test_feature_engineering_no_future_leakage() -> None:
    df = _schedule(8)
    df["home_goals"] = [1, 2, 3, 4, 5, 6, 7, 8]
    df["away_goals"] = [2, 2, 2, 2, 2, 2, 2, 2]

    feat = build_nhl_totals_features(df)
    first = feat.iloc[0]
    assert np.isnan(first["home_roll_goals_for"])

    before = feat.iloc[5]["home_roll_goals_for"]
    df2 = df.copy()
    df2.loc[7, "home_goals"] = 100
    feat2 = build_nhl_totals_features(df2)
    after = feat2.iloc[5]["home_roll_goals_for"]
    assert before == after


def test_isotonic_monotone_and_improves_brier() -> None:
    rng = np.random.default_rng(2)
    raw = np.linspace(0.05, 0.95, 300)
    true = np.clip(0.15 + 0.65 * raw, 0, 1)
    y = rng.binomial(1, true)

    miscal = np.clip(raw**1.8, 0, 1)
    brier_before = np.mean((miscal - y) ** 2)

    iso = fit_isotonic_calibration(miscal, y)
    cal = iso.predict(miscal)
    brier_after = np.mean((cal - y) ** 2)

    assert np.all(np.diff(cal[np.argsort(miscal)]) >= -1e-12)
    assert brier_after <= brier_before
