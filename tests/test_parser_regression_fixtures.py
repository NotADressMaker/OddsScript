from __future__ import annotations

from pathlib import Path

import pytest

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser


def _parse(path: Path) -> None:
    code = path.read_text(encoding="utf-8")
    tokens = Lexer(code).tokenize()
    Parser(tokens, code).parse()


def test_regression_fixture_errors_are_diagnostic() -> None:
    for path in Path("tests/fixtures/parser_regressions").glob("*.odds"):
        with pytest.raises(DiagnosticError):
            _parse(path)
