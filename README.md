# VigScript

VigScript is an open-source programming language and analytics toolkit built specifically for sports betting. It lets bettors, analysts, and developers write betting strategies as code, backtest them against historical results, simulate bankroll risk, analyze odds, and generate repeatable research workflows.

VigScript combines a custom betting-focused scripting language with built-in odds math, bankroll management tools, predictive modeling utilities, APIs, dashboards, and data pipelines. The goal is not to sell picks, but to help users test whether betting ideas survive real-world variance, vig, drawdowns, and risk constraints.

> **Responsible-use disclaimer:** VigScript is for education, research, simulation, and strategy testing. It is not financial advice, investment advice, a recommendation to wager real money, or a guarantee of betting success.

> **Former name:** VigScript was formerly known as SportsBetLang. The Python package and selected legacy commands still use `sportsbetlang` during the compatibility transition.

## Tagline

Open-source sports betting language and analytics toolkit for odds math, bankroll simulation, backtesting, and strategy research.

## What VigScript is for

VigScript is centered on writing and testing betting strategies as code. Supporting APIs, dashboards, predictive models, and data pipelines exist to make language-driven research more transparent and repeatable.

Use VigScript to:

- Write betting strategy logic in readable `.vig` scripts.
- Backtest strategies against historical data and market assumptions.
- Simulate bankroll drawdown, risk of ruin, losing streaks, and staking constraints.
- Analyze expected value, implied probability, devigged prices, closing line value, and variance.
- Generate reports that explain why a strategy passed, failed, or needs more data.
- Feed dashboards, APIs, notebooks, and modeling utilities from the same strategy workflow.

VigScript helps users test betting logic against variance, vig, bankroll limits, and losing streaks before risking capital.

## Install

```bash
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
```

The distribution currently keeps the historical `sportsbetlang` package name so existing imports continue to work.

## Preferred CLI

Use `vigscript` for new workflows:

```bash
vigscript run examples/martingale-risk.vig
vigscript repl
vigscript backtest examples/mlb-moneyline.vig
```

Legacy commands such as `sportsbetlang` and `betlang` remain aliases where supported.

## Preferred script extension

`.vig` is the preferred extension for VigScript programs.

`.sportsodds` files are still supported for compatibility, but new scripts should use `.vig`.

## Flagship examples

- `examples/martingale-risk.vig` — shows why Martingale systems require large bankroll reserves and exposes step probabilities.
- `examples/flat-betting-mlb.vig` — models fixed-stake MLB moneyline research with ROI and losing-streak reporting.
- `examples/kelly-sizing.vig` — compares full Kelly, fractional Kelly, expected value, and bankroll exposure.
- `examples/line-shopping-ev.vig` — evaluates devigged fair prices and expected value across books.
- `examples/bankroll-drawdown.vig` — simulates drawdowns, risk of ruin, and variance constraints.

## Documentation map

Start with the VigScript-first docs:

- `docs/introduction.md`
- `docs/getting-started.md`
- `docs/language/syntax.md`
- `docs/language/variables.md`
- `docs/language/bets.md`
- `docs/language/strategies.md`
- `docs/language/backtesting.md`
- `docs/guides/martingale-risk.md`
- `docs/guides/kelly-sizing.md`
- `docs/guides/flat-betting.md`
- `docs/guides/line-shopping.md`
- `docs/reference/cli.md`
- `docs/reference/api.md`
- `docs/reference/odds-math.md`
- `docs/reference/bankroll.md`
- `docs/migration/sportsbetlang-to-vigscript.md`

## Python compatibility API

Existing Python code can continue to import the historical package while public-facing docs transition to VigScript:

```python
from sportsbetlang import generate_code
```

## Development

```bash
python -m pytest tests/test_cli.py tests/test_interpreter.py
python -m ruff check sportsbetlang/betlang_cli.py sportsbetlang/__version__.py
```

## License and responsibility

VigScript is open-source research software. Betting involves financial risk. Validate data, understand assumptions, respect local laws, and never wager more than you can afford to lose.
