"""Backward-compatible packaged CLI entry point."""

from sportsbetlang.betlang_cli import main  # noqa: I001


if __name__ == "__main__":
    raise SystemExit(main())
