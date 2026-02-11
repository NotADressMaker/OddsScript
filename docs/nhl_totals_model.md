# NHL Totals Probability Model

This module models **distribution tails** for NHL totals (O/U) rather than only an expected total.

## Settlement rules

Use `SettlementRule` consistently across training, labels, and backtests:

- `INCLUDE_SHOOTOUT_DECIDER`: totals include the shootout-deciding goal.
- `EXCLUDE_SHOOTOUT_DECIDER`: totals remove one goal for shootout games (`went_to_shootout=True`).

Mixing rules changes labels and can silently bias calibration, so the API validates required columns.

## Why Poisson and Negative Binomial

- Poisson is the baseline (fast, interpretable, variance = mean).
- NHL totals are often overdispersed; NB2 introduces dispersion `r` so variance is `mu + mu^2/r`.
- `shared_tempo` mode uses a Gamma-Poisson interpretation to represent common game tempo shocks.

## Features

`build_nhl_totals_features` computes strict past-only rolling features:

- schedule/rest (`days_rest`, `is_back_to_back`, `three_in_four`)
- team process (`rolling shots/xG proxies`)
- special teams (`pp_rate`, `pk_rate`)
- goalie form (`rolling save% proxy`)

All rolling values use `shift(1)` to avoid leakage.

## Backtesting and calibration

Use `rolling_origin_backtest` (expanding window default) for leakage-safe time-series validation.

Key metrics:

- log loss
- Brier score
- expected calibration error (ECE)
- predicted-vs-observed totals variance

`fit_isotonic_calibration` gives monotonic post-hoc calibration for over probabilities. Reliability data is available for plotting diagrams.

## Odds and staking

The CLI supports market conversion to fair probabilities with vig removal (including asymmetric split support in eval utilities) and conservative fractional Kelly sizing.

## Running

```bash
python -m sportsbetlang.tools.nhl_totals_cli \
  --train data/nhl_history.csv \
  --slate data/nhl_slate.csv \
  --distribution negative_binomial \
  --backtest
```

## Practical warning

NHL totals markets are relatively efficient. Treat small edges as noisy, monitor calibration drift, and use conservative bankroll sizing.
