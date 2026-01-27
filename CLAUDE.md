# CLAUDE.md — SportsBetLang

## Project Overview

SportsBetLang is a domain-specific programming language (DSL) and Python analytics suite for sports betting analysis. It provides a custom `.odds` scripting language, an interactive REPL, a Python library with 30+ modules, and 22 CLI tools — all with **zero external dependencies** (Python 3.7+ stdlib only).

**Version:** 2.0.0-alpha
**Total codebase:** ~39,000 lines of Python across ~103 files

## Repository Structure

```
SportsBetLang/
├── sportsbetlang.py          # Main REPL entry point
├── lexer.py                  # DSL tokenizer
├── parser.py                 # DSL AST parser
├── interpreter.py            # DSL execution engine
├── test_phase1.py            # DSL phase-1 tests
├── setup.py                  # Package configuration
├── requirements.txt          # Empty — stdlib only
├── .env.example              # Environment variable templates (40+ settings)
│
├── sportsbetlang/            # Core package (5,657 lines)
│   ├── analytics/            #   Statistical analysis
│   ├── common/               #   Shared utils (kelly, odds, validators)
│   ├── config/               #   Settings via dataclass
│   ├── core/                 #   Symlinks to root lexer/parser/interpreter
│   ├── data/                 #   Storage layer (CSV + SQLite adapters)
│   ├── strategies/           #   Betting strategy framework (base, flat, kelly)
│   └── tools/                #   Tool framework (base + odds calc)
│
├── lib/                      # Advanced analytics library (15,764 lines, 30+ modules)
│   ├── simple_api.py         #   Simplified interface (SBL, Bet, Compare)
│   ├── advanced_stats.py     #   Bayesian, Monte Carlo, regression
│   ├── ml_models.py          #   DecisionTree, RandomForest, NeuralNetwork
│   ├── model_builder.py      #   Fluent model creation interface
│   ├── backtesting.py        #   Strategy backtesting
│   ├── database.py           #   BettingDatabase for tracking
│   ├── *_analytics.py        #   Sport-specific: nba, nfl, nhl, mlb, cfb, cbb, soccer, horse_racing
│   └── ...                   #   CLV tracker, Elo ratings, Poisson, variance, etc.
│
├── tools/                    # 22 CLI tools (8,879 lines)
│   ├── odds_calc.py          #   Kelly, EV, parlays, vig removal
│   ├── bet_tracker.py        #   Bet tracking & analysis
│   ├── arbitrage_calculator.py
│   ├── hedge_calculator.py
│   ├── sharp_money_indicator.py
│   ├── portfolio_optimizer.py
│   └── ...                   #   Tax calc, teasers, round robin, dutch betting, etc.
│
├── strategies/               # Legacy strategy implementations
│   ├── martingale.py
│   ├── fibonacci.py
│   └── flat_betting.py
│
├── tests/                    # pytest test suite
│   ├── test_interpreter.py
│   ├── test_advanced_stats.py
│   ├── test_ml_models.py
│   └── test_*_analytics.py   #   Sport-specific test files
│
├── examples/                 # 11 .odds scripts + 6 Python examples
├── docs/                     # 11 guides (~228KB total)
└── data/                     # Sample CSV data (NFL, NBA)
```

## Build & Run Commands

```bash
# Run the REPL
python3 sportsbetlang.py

# Run a .odds script
python3 sportsbetlang.py examples/01_basic_bet.odds

# Run all tests
pytest tests/

# Run a specific test file
pytest tests/test_interpreter.py

# Run DSL phase-1 tests directly
python3 test_phase1.py

# Install in development mode
pip install -e .

# Install with dev dependencies (pytest)
pip install -e ".[dev]"
```

## Key Architecture

### DSL Pipeline

```
Source (.odds) → Lexer (tokens) → Parser (AST) → Interpreter (execution)
```

- **Lexer** (`lexer.py`): Tokenizes DSL source into typed tokens
- **Parser** (`parser.py`): Builds an Abstract Syntax Tree from tokens
- **Interpreter** (`interpreter.py`): Walks AST, manages environments/scopes, executes built-in betting functions
- The root-level `lexer.py`, `parser.py`, `interpreter.py` are the canonical files; `sportsbetlang/core/` contains symlinks to them

### Design Patterns Used

- **Abstract Base / Plugin** — `BettingStrategy(ABC)` with concrete `FlatStrategy`, `KellyStrategy`
- **Adapter** — `Storage` abstract interface with `CSVAdapter` and `SQLiteAdapter`
- **Builder** — Fluent `ModelBuilder` API: `Model().named("x").for_classification().using_random_forest().train(X, y)`
- **Factory** — `get_sport_model('nfl', 'spread_model')`
- **Singleton/Config** — `get_config()` / `set_config(kelly_fraction=0.25)`

### Data Storage

Two interchangeable backends behind a unified `Storage` interface:
- **CSV** (`sportsbetlang/data/csv_adapter.py`)
- **SQLite** (`sportsbetlang/data/sqlite_adapter.py`)

### Sports Supported (8)

NFL, NBA, MLB, NHL, College Football, College Basketball, Soccer, Horse Racing — each with dedicated analytics modules in `lib/`.

## Code Conventions

### Naming
- **Classes:** `PascalCase` — `KellyCriterion`, `BettingStrategy`, `Interpreter`
- **Functions/methods:** `snake_case` — `american_to_decimal`, `calculate_kelly`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private members:** `_leading_underscore`
- **Modules:** `snake_case.py`

### Style
- Type hints throughout (Python 3.7+ compatible using `typing`)
- `@dataclass` for data structures
- `Enum` for type-safe constants
- Docstrings with usage examples on public APIs
- Standard library only — no external packages in production code
- `pytest` is the sole dev dependency

### Error Handling
- Custom exceptions in the DSL: `ReturnValue`, `RuntimeError`, `SyntaxError`
- Error messages include file/line information where possible
- CLI tools use try/except with user-friendly messages

## Dependencies

**Production:** None — Python 3.7+ standard library only (`math`, `dataclasses`, `re`, `sqlite3`, `csv`, `json`, `random`, `collections`, `typing`, `pathlib`, `enum`, `copy`)

**Development:** `pytest >= 6.0`, `pytest-cov >= 2.0`

## Configuration

Environment variables are documented in `.env.example` with 40+ settings covering:
- Kelly criterion (fraction, max bet percentage)
- Elo rating system (K-factor, home advantage)
- Sharp money detection (RLM threshold, velocity)
- Risk management (max daily risk, stop loss)
- Display, storage, caching, and API settings

Runtime configuration uses `sportsbetlang/config/settings.py` (a `SportsBetLangConfig` dataclass) with `get_config()` / `set_config()`.

## Testing

Tests live in `tests/` and use pytest. Key test files:

| File | Covers |
|------|--------|
| `test_interpreter.py` | DSL execution engine |
| `test_advanced_stats.py` | Statistical functions |
| `test_ml_models.py` | ML model implementations |
| `test_cbb_analytics.py` | College Basketball |
| `test_cfb_analytics.py` | College Football |
| `test_horse_racing_analytics.py` | Horse Racing |
| `test_soccer_analytics.py` | Soccer |
| `test_sports_data_manager.py` | Data management |

There is also `test_phase1.py` at the root for DSL-specific phase-1 tests (run directly with `python3 test_phase1.py`).

## Development Workflow

- Feature branches use `claude/` prefix (e.g., `claude/improve-horse-racing-models-oqfO3`)
- Pull request workflow — changes merged via GitHub PRs
- No CI/CD pipeline; tests run manually with `pytest tests/`
- Deployment targets: Desktop (pip install), Replit.com (`.replit` config), Google Colab, online Python environments

## Common Tasks for AI Assistants

### Adding a new sport analytics module
1. Create `lib/<sport>_analytics.py` following existing patterns (see `lib/nba_analytics.py`)
2. Export from `lib/__init__.py`
3. Add tests in `tests/test_<sport>_analytics.py`
4. Update docs if appropriate

### Adding a new CLI tool
1. Create `tools/<tool_name>.py` — each tool is a standalone script
2. Follow the pattern of existing tools (argparse CLI, main function)
3. Document in `PACKAGES.md`

### Adding a new betting strategy
1. Subclass `BettingStrategy` from `sportsbetlang/strategies/base.py`
2. Implement `name()` and `decide()` methods
3. Place in `sportsbetlang/strategies/`

### Extending the DSL
1. Add tokens in `lexer.py`
2. Add grammar rules in `parser.py`
3. Add evaluation logic in `interpreter.py`
4. Add tests in `test_phase1.py` or `tests/test_interpreter.py`

### Adding a data storage backend
1. Implement the `Storage` interface from `sportsbetlang/data/storage.py`
2. Follow the adapter pattern used by `csv_adapter.py` and `sqlite_adapter.py`
