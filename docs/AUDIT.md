# SportsBetLang Audit Report

## What the repo does
SportsBetLang is a domain-specific language (DSL) for sports betting analysis, plus a large Python analytics toolkit. The DSL allows `.odds` scripts to express betting logic (bets, parlays, bankroll management) and executes them through a custom lexer, parser, and interpreter. The Python libraries provide odds conversion utilities, sport-specific analytics, model helpers, and data tooling that can be used independently or from SportsBetLang scripts.

The runtime model is an in-process interpreter: source code is tokenized, parsed into an AST, and evaluated with built-in betting functions and modules. The repository also ships a wide set of domain libraries under `lib/` for sports modeling and betting math.

## Structure map (key files)
- Language runtime:
  - `lexer.py` – tokenization
  - `parser.py` – AST construction
  - `interpreter.py` – runtime evaluation
  - `sportsbetlang.py` – legacy CLI entry point
  - `sportsbetlang/cli.py` – packaged CLI entry point
- Libraries:
  - `lib/betting_core.py` – odds conversion + EV math
  - `lib/nhl_analytics.py` – NHL analytics utilities
- Examples:
  - `examples/*.odds` – language examples
- Tests:
  - `tests/test_interpreter.py` – language unit tests
  - `tests/test_nhl_analytics.py` – NHL analytics tests
- Packaging/CI:
  - `setup.py`, `pyproject.toml`
  - `.github/workflows/ci.yml`
- Docs:
  - `docs/LANGUAGE_SPEC.md`
  - `docs/ARCHITECTURE.md`

## Findings

### Correctness
- **P1**: AST dataclass inheritance error in `parser.py` caused test collection to fail (`non-default argument ... follows default argument`). This prevented parsing from working at all in some environments.
- **P1**: Interpreter referenced a missing `runtime_error` helper, leading to runtime exceptions when undefined variables or import errors were encountered.
- **P1**: `lib/nhl_analytics.py` lacked multiple analytics helpers expected by the test suite (team xG, Corsi/Fenwick, PDO, goalie analysis, player props, etc.).
- **P1**: `lib/poisson_calculator.py` did not expose the `simulate_poisson` alias used by soccer simulations, causing runtime failures.
- **P2**: `lib/nhl_analytics.py` did not expose the `Situation` enum expected by tests, causing import errors.

### Safety / Reliability
- **P1**: No execution guardrails for untrusted scripts (infinite loops or runaway recursion could lock the interpreter). The runtime had no step limit or call-depth limits.

### Developer Experience (DX)
- **P1**: Packaging did not include the `sportsbetlang` package or expose a stable CLI entry point. The `console_scripts` entry targeted a missing module (`sportsbetlang:main`).
- **P2**: CLI error messages lacked consistent line/column context and did not expose call stacks for easier debugging.

## Changes made (mapped to findings)
- **Correctness**
  - Fixed AST dataclass inheritance by making line/column keyword-only fields to avoid invalid init ordering.
  - Added missing `runtime_error` handling and structured runtime error formatting.
  - Implemented missing NHL analytics helpers and expanded NHL data containers to match test expectations.
  - Added `simulate_poisson` alias to the Poisson calculator and corrected SP+ home advantage handling.
  - Added `Situation` enum to `lib/nhl_analytics.py` for test compatibility.
- **Safety / Reliability**
  - Added execution step limits and max call-depth guardrails in the interpreter to prevent runaway scripts.
- **DX / Packaging**
  - Added a packaged CLI entry point (`sportsbetlang`), `pyproject.toml`, and updated `setup.py` to package the language runtime.
  - Improved parser and lexer diagnostics with clearer token formatting.
  - Added CI workflow and expanded tests, including a CLI smoke test and betting math coverage.
  - Documented architecture and updated README with canonical run/test commands.

## How to verify
```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run the CLI on an example program
sportsbetlang examples/01_basic_bet.odds

# Run tests
pytest
```
