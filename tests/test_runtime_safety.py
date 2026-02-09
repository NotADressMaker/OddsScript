#!/usr/bin/env python3
"""Safety guardrail tests for the interpreter."""

import unittest

from sportsbetlang.core.interpreter import Interpreter, LanguageRuntimeError
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser


class TestRuntimeSafety(unittest.TestCase):
    def run_code(self, code: str, max_steps: int):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, code)
        ast = parser.parse()
        interpreter = Interpreter(max_steps=max_steps)
        return interpreter.interpret(ast)

    def test_step_limit(self):
        code = """
        while 1 {
        }
        """
        with self.assertRaises(LanguageRuntimeError):
            self.run_code(code, max_steps=50)


if __name__ == "__main__":
    unittest.main()
