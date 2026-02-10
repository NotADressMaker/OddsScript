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


def test_cli_runtime_limit_flags_trigger(tmp_path: Path):
    program = tmp_path / "loop.odds"
    program.write_text("while true { }\n", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sportsbetlang",
            "--max-steps",
            "10",
            str(program),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "step limit" in result.stdout.lower()


def test_cli_limits_pragma_overrides_mode(tmp_path: Path):
    program = tmp_path / "pragma.odds"
    program.write_text("#limits max_steps=5\nwhile true { }\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "sportsbetlang", "--mode", "expert", str(program)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "step limit" in result.stdout.lower()
