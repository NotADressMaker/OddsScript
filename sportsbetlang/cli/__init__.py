"""Command-line interface for SportsBetLang."""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType
from typing import Callable


def _load_cli_impl() -> ModuleType:
    cli_path = Path(__file__).resolve().parents[1] / "cli.py"
    loader = SourceFileLoader("sportsbetlang._cli_impl", str(cli_path))
    spec = spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("Unable to load CLI implementation.")
    module = module_from_spec(spec)
    loader.exec_module(module)
    return module


_cli_impl = _load_cli_impl()
main: Callable[[], int] = _cli_impl.main

__all__ = ["main"]
