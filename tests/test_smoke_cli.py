"""Smoke tests for the CLI entry point."""

import subprocess
import sys
from pathlib import Path


def test_cli_runs_poisson_example():
    odds_path = Path(__file__).resolve().parents[1] / "test_poisson.odds"
    result = subprocess.run(
        [sys.executable, "-m", "sportsbetlang", str(odds_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
