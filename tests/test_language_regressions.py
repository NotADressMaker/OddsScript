"""Regression coverage for parser/interpreter behavior."""

import json
import unittest
from pathlib import Path

from diagnostics import DiagnosticError
from interpreter import Interpreter, TaggedNumber
from lexer import Lexer
from parser import Parser


class TestParserErrors(unittest.TestCase):
    """Parser tests for success and diagnostic failures."""

    def parse(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, code)
        return parser.parse()

    def test_parses_simple_block(self):
        """This code parses."""
        ast = self.parse("if true { let x = 1 }")
        self.assertIsNotNone(ast)

    def test_missing_identifier_in_assignment(self):
        """This fails with this error."""
        with self.assertRaises(DiagnosticError) as context:
            self.parse("let = 10")
        self.assertIn("Expected IDENTIFIER", str(context.exception))

    def test_missing_block_closure(self):
        """This fails with this error."""
        with self.assertRaises(DiagnosticError) as context:
            self.parse("if true { let x = 1")
        self.assertIn("Unexpected token EOF", str(context.exception))


class TestInterpreterBehavior(unittest.TestCase):
    """Interpreter behavior coverage."""

    def run_code(self, code: str):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, code)
        ast = parser.parse()
        interpreter = Interpreter()
        return interpreter.interpret(ast)

    def test_deterministic_evaluation(self):
        code = """
        let x = 2 + 3 * 4
        x + 1
        """
        first = self.run_code(code)
        second = self.run_code(code)
        self.assertEqual(first, second)

    def test_function_scope_does_not_leak(self):
        code = """
        let x = 10
        func add(x) {
            return x + 1
        }
        add(5)
        x
        """
        self.assertEqual(self.run_code(code), 10)

    def test_loop_variable_does_not_escape(self):
        code = """
        let i = 42
        for i in [1, 2] {
            let x = i
        }
        i
        """
        self.assertEqual(self.run_code(code), 42)

    def test_import_module_call(self):
        result = self.run_code("import betting as bet_mod\n bet_mod.implied_probability(-110)")
        self.assertIsInstance(result, TaggedNumber)
        self.assertAlmostEqual(result.value, 0.523809, places=5)

    def test_from_import_alias(self):
        result = self.run_code("from betting import implied_probability as ip\n ip(-110)")
        self.assertIsInstance(result, TaggedNumber)
        self.assertAlmostEqual(result.value, 0.523809, places=5)

    def test_floating_point_stability(self):
        result = self.run_code("0.1 + 0.2")
        self.assertAlmostEqual(result, 0.3, places=7)

    def test_implied_probability_bounds(self):
        interpreter = Interpreter()
        implied_probability = interpreter.global_env.get("implied_probability")
        for odds in (-300, -110, -105, 100, 150, 250):
            prob = implied_probability(odds)
            self.assertGreaterEqual(prob.value, 0)
            self.assertLessEqual(prob.value, 1)


class TestFixtures(unittest.TestCase):
    """Repro fixtures for slates and line sets."""

    def test_tiny_slate_fixture(self):
        fixture_path = Path("tests/fixtures/slates/tiny_slate.json")
        data = json.loads(fixture_path.read_text())
        self.assertEqual(data["sport"], "NBA")
        self.assertGreaterEqual(len(data["games"]), 1)

    def test_tiny_lines_fixture(self):
        fixture_path = Path("tests/fixtures/line_sets/tiny_lines.csv")
        lines = fixture_path.read_text().strip().splitlines()
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual(lines[0].split(","), ["market", "team", "odds", "stake"])


if __name__ == "__main__":
    unittest.main()
