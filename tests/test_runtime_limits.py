from __future__ import annotations

import pytest

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.interpreter import Interpreter, LanguageRuntimeError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser
from sportsbetlang.lang.limits import RuntimeLimits


def _interpret(code: str, limits: RuntimeLimits) -> None:
    lexer = Lexer(code, limits=limits)
    tokens = lexer.tokenize()
    parser = Parser(tokens, code, limits=limits)
    program = parser.parse()
    interpreter = Interpreter(limits=limits)
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
