"""Regression coverage for parser/interpreter behavior."""

import json
import unittest
from pathlib import Path

from sportsbetlang.core.diagnostics import DiagnosticError
from sportsbetlang.core.interpreter import Bet, Interpreter, LanguageRuntimeError, TaggedNumber
from sportsbetlang.core.lexer import Lexer
from sportsbetlang.core.parser import Parser


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



    def test_tagged_number_prevents_mixed_units(self):
        with self.assertRaises(LanguageRuntimeError) as context:
            self.run_code("implied_probability(-110) + calculate_ev(0.55, -110, 100)")
        self.assertIn("Cannot add", str(context.exception))

    def test_calculate_ev_returns_money_tag(self):
        result = self.run_code("calculate_ev(0.55, -110, 100)")
        self.assertIsInstance(result, TaggedNumber)
        self.assertEqual(result.tag, "money")
    def test_odds_conversion_rejects_zero_american(self):
        interpreter = Interpreter()
        american_to_decimal = interpreter.global_env.get("american_to_decimal")
        with self.assertRaises(ValueError):
            american_to_decimal(0)

    def test_odds_conversion_rejects_invalid_decimal(self):
        interpreter = Interpreter()
        decimal_to_american = interpreter.global_env.get("decimal_to_american")
        for decimal_odds in (1.0, 0.95):
            with self.assertRaises(ValueError):
                decimal_to_american(decimal_odds)

    def test_bet_repr_formats_float_odds(self):
        bet = Bet("moneyline", "Lakers", -110.0, 100)
        self.assertIn("@ -110", repr(bet))



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
