from __future__ import annotations

import pytest

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser


def test_lexer_error_includes_caret_snippet() -> None:
    code = "let a = 1\n$"
    with pytest.raises(DiagnosticError) as excinfo:
        Lexer(code).tokenize()
    message = str(excinfo.value)
    assert "line 2" in message
    assert "^" in message
    assert "$" in message


def test_keyword_suggestion_for_typos() -> None:
    code = "whlie 1 { }"
    tokens = Lexer(code).tokenize()
    parser = Parser(tokens, code)
    with pytest.raises(DiagnosticError) as excinfo:
        parser.parse()
    assert "Did you mean 'while'" in str(excinfo.value)
