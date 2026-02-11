"""CLI utility for NHL totals model training, backtesting, and slate scoring."""

from __future__ import annotations

import argparse
import json

import pandas as pd

from sportsbetlang.eval.nhl_totals_eval import (
    RollingOriginConfig,
    conservative_kelly,
    remove_vig_two_way,
    rolling_origin_backtest,
)
from sportsbetlang.models.nhl_totals import SettlementRule, fit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NHL totals model workflow")
    parser.add_argument("--train", required=True, help="Historical games CSV")
    parser.add_argument("--slate", help="Upcoming games CSV with total_line")
    parser.add_argument(
        "--distribution",
        default="negative_binomial",
        choices=["poisson", "negative_binomial", "shared_tempo"],
    )
    parser.add_argument(
        "--settlement-rule",
        default=SettlementRule.INCLUDE_SHOOTOUT_DECIDER.value,
        choices=[r.value for r in SettlementRule],
    )
    parser.add_argument("--backtest", action="store_true", help="Run rolling-origin backtest")
    parser.add_argument("--kelly-fraction", type=float, default=0.25)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settlement_rule = SettlementRule(args.settlement_rule)

    train_df = pd.read_csv(args.train)
    model = fit(train_df, settlement_rule=settlement_rule, distribution=args.distribution)

    payload: dict[str, object] = {
        "model": {
            "distribution": model.distribution,
            "settlement_rule": model.settlement_rule.value,
            "league_mean_total": model.league_mean_total,
            "dispersion_r": model.dispersion_r,
        }
    }

    if args.backtest:
        bt = rolling_origin_backtest(
            train_df,
            settlement_rule=settlement_rule,
            distribution=args.distribution,
            cv_config=RollingOriginConfig(),
        )
        payload["backtest_metrics"] = bt["metrics"]

    if args.slate:
        slate_df = pd.read_csv(args.slate)
        pred = model.predict_proba(slate_df)
        if {"over_odds", "under_odds"}.issubset(pred.columns):
            fair_probs = pred.apply(
                lambda r: remove_vig_two_way(float(r["over_odds"]), float(r["under_odds"])),
                axis=1,
                result_type="expand",
            )
            pred["market_fair_over"] = fair_probs[0]
            pred["market_fair_under"] = fair_probs[1]
            pred["edge_over"] = pred["p_over"] - pred["market_fair_over"]
            pred["edge_under"] = pred["p_under"] - pred["market_fair_under"]
            pred["kelly_over"] = pred.apply(
                lambda r: conservative_kelly(
                    r["p_over"], float(r["over_odds"]), fraction=args.kelly_fraction
                ),
                axis=1,
            )
            pred["kelly_under"] = pred.apply(
                lambda r: conservative_kelly(
                    r["p_under"], float(r["under_odds"]), fraction=args.kelly_fraction
                ),
                axis=1,
            )
        pred = pred.sort_values("p_over", ascending=False)
        payload["slate"] = pred.head(args.top).to_dict(orient="records")

    if args.json:
        print(json.dumps(payload, indent=2, default=float))
    else:
        print("Model summary:")
        print(payload["model"])
        if "backtest_metrics" in payload:
            print("Backtest:")
            print(payload["backtest_metrics"])
        if "slate" in payload:
            print("Top slate edges:")
            print(pd.DataFrame(payload["slate"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
