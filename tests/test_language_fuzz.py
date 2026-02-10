from __future__ import annotations

import pytest

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser

hypothesis = pytest.importorskip("hypothesis")
st = hypothesis.strategies

def parse_source(source: str):
    tokens = Lexer(source).tokenize()
    return Parser(tokens, source).parse()


@hypothesis.given(st.text(min_size=0, max_size=120))
def test_parser_never_crashes_on_random_text(source: str) -> None:
    try:
        parse_source(source)
    except DiagnosticError:
        pass


@hypothesis.given(
    st.lists(
        st.sampled_from([
            "let", "x", "=", "1", "if", "true", "{", "}", "(", ")", "+", "-", "\n",
        ]),
        min_size=1,
        max_size=60,
    ).map(" ".join)
)
def test_parser_handles_token_sequences(sequence: str) -> None:
    try:
        parse_source(sequence)
    except DiagnosticError:
        pass
