# Areas for Improvement

This document captures concrete improvement opportunities based on the current repository state.

## Documentation and Onboarding
- **Fix the clone path typo in the README.** The quick-start instructions say `cd programminglangauage`, which looks like a typo that can confuse new users; it should match the repo name. (Source: `README.md` clone instructions.)
- **Document API/server dependencies separately from core.** The README and `requirements.txt` emphasize "no external dependencies," but there is a dedicated `requirements-api.txt` for FastAPI/uvicorn, etc. It would help to add a short README section that explains when to use each requirements file and how to run the API/server components.

## Packaging and Installation
- **Add an installable `api` extra in `setup.py`.** Since API dependencies are already listed in `requirements-api.txt`, exposing them as an optional extra (e.g., `pip install .[api]`) would make setup easier and keep packaging in sync with the API stack.

## Modeling + Betting Realism
- **Introduce first-class Market objects (totals/spread/moneyline/props) with consistent fields.** Standardize how market metadata (type, selection, line, odds, book, timestamps) is represented across the DSL, Python utilities, and storage layers.
- **Normalize line & odds formats (American/decimal/implied probability).** Provide canonical conversion utilities and enforce consistent normalization in analytics pipelines and bet records.
- **Add vig-aware comparison utilities with optional devigging.** Enable fair pricing comparisons across books and model outputs with both raw and devigged calculations.
- **Codify correlation/exposure rules.** Track same-game, same-team, and same-market dependencies to prevent correlated exposure in portfolio and parlay tools.
- **Expand backtesting hooks for realism.** Support time-based splits, CLV benchmarking, and slippage assumptions for model evaluation and strategy testing.
