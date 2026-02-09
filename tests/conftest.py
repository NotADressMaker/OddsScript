import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_addoption(parser: Any) -> None:
    if importlib.util.find_spec("pytest_cov") is None:
        parser.addoption("--cov", action="store", default=None, help="(ignored)")
        parser.addoption(
            "--cov-report",
            action="append",
            default=[],
            help="(ignored)",
        )
