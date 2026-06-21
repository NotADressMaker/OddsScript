# Getting started with VigScript

Install the package, then run a `.vig` strategy:

```bash
pip install git+https://github.com/NotADressMaker/SportsBetLang.git
vigscript run examples/martingale-risk.vig
vigscript repl
vigscript backtest examples/mlb-moneyline.vig
```

`.sportsodds` files are still supported for compatibility, but new scripts should use `.vig`.
