"""Smoke tests for the CLI entry point."""

import json
import subprocess
import sys
from pathlib import Path


def test_legacy_cli_runs_poisson_example():
    odds_path = Path(__file__).resolve().parents[1] / "test_poisson.sportsodds"
    result = subprocess.run(
        [sys.executable, "-m", "sportsbetlang", str(odds_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_cli_runtime_limit_flags_trigger(tmp_path: Path):
    program = tmp_path / "loop.sportsodds"
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
    assert "definitely-infinite" in result.stdout.lower()


def test_betlang_run_supports_json_output():
    odds_path = Path(__file__).resolve().parents[1] / "examples" / "01_basic_bet.sportsodds"
    result = subprocess.run(
        [sys.executable, "-m", "sportsbetlang", "run", str(odds_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "run"
    assert payload["status"] == "ok"


def test_betlang_test_subcommand_accepts_pytest_args():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sportsbetlang",
            "test",
            "tests/test_smoke_cli.py::test_legacy_cli_runs_poisson_example",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    json_start = result.stdout.rfind("{")
    assert json_start != -1, result.stdout
    payload = json.loads(result.stdout[json_start:])
    assert payload["command"] == "test"
    assert payload["exit_code"] == 0


def test_betlang_research_terminal_accepts_help_and_quit():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sportsbetlang",
            "research-terminal",
            "--no-external-search",
        ],
        input=":help\n:quit\n",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "SportsBetLang Research Terminal" in result.stdout
    assert "Use :quit or :exit" in result.stdout
