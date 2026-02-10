from __future__ import annotations

import pytest

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.interpreter import Interpreter, LanguageRuntimeError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser
from sportsbetlang.lang.limits import SAFE_LIMITS, RuntimeLimits, parse_limits_pragma, resolve_runtime_limits


def _interpret(code: str, limits: RuntimeLimits) -> None:
    lexer = Lexer(code, limits=limits)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code, limits=limits)
    program = parser.parse()
    interpreter = Interpreter(limits=limits, source=code)
    interpreter.interpret(program)


def test_token_limit_triggers() -> None:
    code = "let a = 1\nlet b = 2\n"
    limits = RuntimeLimits(max_tokens=5)
    with pytest.raises(DiagnosticError):
        Lexer(code, limits=limits).tokenize()


def test_ast_node_limit_triggers() -> None:
    code = "let a = 1\nlet b = 2\nlet c = 3\n"
    limits = RuntimeLimits(max_ast_nodes=3)
    lexer = Lexer(code, limits=limits)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code, limits=limits)
    with pytest.raises(DiagnosticError):
        parser.parse()


def test_recursion_limit_triggers() -> None:
    code = """
    func recurse(n) {
      if n {
        return recurse(n - 1)
      }
      return 0
    }
    recurse(50)
    """
    limits = RuntimeLimits(max_recursion_depth=20, max_steps=10_000)
    with pytest.raises(LanguageRuntimeError):
        _interpret(code, limits)


def test_string_limit_triggers() -> None:
    code = "let a = \"abcd\""
    limits = RuntimeLimits(max_string_length=3)
    with pytest.raises(LanguageRuntimeError):
        _interpret(code, limits)


def test_list_limit_triggers() -> None:
    code = "let a = [1, 2, 3]"
    limits = RuntimeLimits(max_list_length=2)
    with pytest.raises(LanguageRuntimeError):
        _interpret(code, limits)


def test_for_loop_iteration_limit_triggers() -> None:
    code = """
    for i in range(0, 10) {
    }
    """
    limits = RuntimeLimits(max_loop_iterations=3, max_steps=10_000)
    with pytest.raises(LanguageRuntimeError):
        _interpret(code, limits)


def test_limits_pragma_parsed() -> None:
    source = "#limits max_steps=50000 max_loop=900 max_recursion=70\nlet x = 1\n"
    pragma = parse_limits_pragma(source)
    assert pragma == {"max_steps": 50000, "max_loop": 900, "max_recursion": 70}


def test_limits_resolution_precedence() -> None:
    source = "#limits max_steps=50000 max_loop=900\nlet x = 1\n"
    limits = resolve_runtime_limits(
        source,
        base_limits=SAFE_LIMITS,
        max_steps=123,
        max_loop=None,
        max_recursion=77,
    )
    assert limits.max_steps == 123
    assert limits.max_loop_iterations == 900
    assert limits.max_recursion_depth == 77


def test_runtime_error_includes_hint_and_snippet() -> None:
    code = """
    const bankroll = 100
    bankroll = 50
    """
    limits = RuntimeLimits(max_steps=10_000)
    with pytest.raises(LanguageRuntimeError) as exc:
        _interpret(code, limits)
    text = exc.value.format()
    assert "line" in text
    assert "^" in text
    assert "Hint:" in text
