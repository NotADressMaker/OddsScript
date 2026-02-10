# BetLang Golden Paths, Recipes, and Troubleshooting

This guide focuses on the **canonical workflows** most users need day-to-day.

## Golden path 1: Build a model

```bash
# 1) Install development dependencies
pip install -e ".[dev]"

# 2) Train/evaluate with your preferred script(s)
python examples/ml_model_examples.py

# 3) Validate project health
betlang test -q
```

## Golden path 2: Backtest a strategy

```bash
# Run a strategy-focused DSL program
betlang run examples/07_advanced_strategy.odds

# Compare against expected outputs for curated examples
betlang run examples/13_totals_spread_props.odds > /tmp/13_totals_spread_props.txt
diff -u examples/expected_outputs/13_totals_spread_props.txt /tmp/13_totals_spread_props.txt
```

## Golden path 3: Track CLV-style line movement research

```bash
# Use the compliant research workflow and return machine-readable output
betlang research --json "closing line movement for tonight's nba slate"
```

## Golden path 4: Ingest historical/live data

```bash
# Backfill run
betlang ingest backfill --sport nba --start 2025-10-01 --end 2025-10-31 --markets spread,total,moneyline

# Live run
betlang ingest live --sport nba --start 2025-10-01 --end 2025-10-01 --markets spread,total,moneyline
```

## Golden path 5: Interactive DSL iteration

```bash
betlang repl
```

---

## Copy-paste recipes

### Format + lint a program

```bash
betlang format examples/01_basic_bet.odds --write
betlang lint examples/01_basic_bet.odds
```

### Run a program in JSON mode

```bash
betlang run examples/01_basic_bet.odds --json
```

### Run tests with extra pytest args

```bash
betlang test tests/test_smoke_cli.py -q
```

### Ingestion output for automation

```bash
betlang ingest backfill --sport nfl --start 2025-09-01 --end 2025-09-07 --json
```

### Research output for automation

```bash
betlang research --json "probable pitchers today" --max-results 5
```

---

## Troubleshooting

### `Error: File 'X' not found`
- Verify the path is relative to your current working directory.
- Use `pwd` to check location and run with an absolute path if needed.

### `Runtime Error: ... step limit`
- Your script hit runtime safety limits.
- Increase limits for trusted code: `betlang run my.odds --max-steps 200000`.

### `Dependency Error: ...`
- Optional dependencies may be missing for research workflows.
- Install extras: `pip install -e ".[research]"` or `pip install -e ".[dev]"`.

### Ingestion returns sparse counts/data gaps
- Confirm `--sport`, dates, and configured source availability.
- Re-run with a smaller date window first, then expand.

### JSON expected but got plain text
- Add `--json` to the command. This is supported across `run`, `repl`, `test`, `ingest`, `research`, `format`, and `lint`.
