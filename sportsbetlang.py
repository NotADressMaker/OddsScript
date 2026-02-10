#!/usr/bin/env python3
"""Legacy script that forwards to the unified BetLang CLI."""

from sportsbetlang.betlang_cli import main  # noqa: I001


if __name__ == "__main__":
    raise SystemExit(main())
