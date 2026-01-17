"""
Unit tests for SportsBetLang interpreter
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import Lexer
from parser import Parser
from interpreter import Interpreter


class TestInterpreter(unittest.TestCase):
    """Test SportsBetLang interpreter"""

    def run_code(self, code: str):
        """Helper to run SportsBetLang code"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        return interpreter.interpret(ast)

    def test_basic_arithmetic(self):
        """Test basic arithmetic operations"""
        self.assertEqual(self.run_code("2 + 3"), 5)
        self.assertEqual(self.run_code("10 - 4"), 6)
        self.assertEqual(self.run_code("5 * 6"), 30)
        self.assertEqual(self.run_code("20 / 4"), 5)

    def test_variables(self):
        """Test variable assignment and retrieval"""
        code = """
        let x = 10
        let y = 20
        x + y
        """
        self.assertEqual(self.run_code(code), 30)

    def test_functions(self):
        """Test function definition and calling"""
        code = """
        func add(a, b) {
            return a + b
        }
        add(5, 7)
        """
        self.assertEqual(self.run_code(code), 12)

    def test_if_statement(self):
        """Test if/else statements"""
        code = """
        let x = 10
        if x > 5 {
            let result = 1
            result
        } else {
            let result = 0
            result
        }
        """
        # Note: This won't work as written due to scope issues
        # Better test:
        code = """
        let x = 10
        let result = 0
        if x > 5 {
            result = 1
        }
        result
        """
        self.assertEqual(self.run_code(code), 1)

    def test_while_loop(self):
        """Test while loops"""
        code = """
        let i = 0
        let sum = 0
        while i < 5 {
            sum = sum + i
            i = i + 1
        }
        sum
        """
        self.assertEqual(self.run_code(code), 10)  # 0+1+2+3+4 = 10

    def test_for_loop(self):
        """Test for loops"""
        code = """
        let sum = 0
        for i in [1, 2, 3, 4, 5] {
            sum = sum + i
        }
        sum
        """
        self.assertEqual(self.run_code(code), 15)

    def test_arrays(self):
        """Test array operations"""
        code = """
        let arr = [1, 2, 3, 4, 5]
        len(arr)
        """
        self.assertEqual(self.run_code(code), 5)

    def test_american_to_decimal(self):
        """Test odds conversion"""
        interpreter = Interpreter()

        # Test negative odds
        self.assertAlmostEqual(
            interpreter.global_env.get('american_to_decimal')(-110),
            1.909090909,
            places=5
        )

        # Test positive odds
        self.assertAlmostEqual(
            interpreter.global_env.get('american_to_decimal')(150),
            2.5,
            places=5
        )

    def test_implied_probability(self):
        """Test implied probability calculation"""
        interpreter = Interpreter()

        # Test -110 odds
        self.assertAlmostEqual(
            interpreter.global_env.get('implied_probability')(-110),
            0.5238095238,
            places=5
        )

        # Test +150 odds
        self.assertAlmostEqual(
            interpreter.global_env.get('implied_probability')(150),
            0.4,
            places=5
        )

    def test_kelly_criterion(self):
        """Test Kelly criterion calculation"""
        interpreter = Interpreter()
        kelly_func = interpreter.global_env.get('kelly_criterion')

        # Edge case: no edge (true prob = implied prob)
        result = kelly_func(0.5238, -110)
        self.assertAlmostEqual(result, 0, places=2)

        # Positive edge case
        result = kelly_func(0.60, -110)
        self.assertGreater(result, 0)

    def test_calculate_ev(self):
        """Test expected value calculation"""
        interpreter = Interpreter()
        ev_func = interpreter.global_env.get('calculate_ev')

        # Positive EV case
        ev = ev_func(0.55, -110, 100)
        self.assertGreater(ev, 0)

        # Negative EV case
        ev = ev_func(0.45, -110, 100)
        self.assertLess(ev, 0)

    def test_parlay_odds(self):
        """Test parlay odds calculation"""
        interpreter = Interpreter()
        parlay_func = interpreter.global_env.get('parlay_odds')

        # 2-leg parlay at -110
        result = parlay_func(-110, -110)
        self.assertAlmostEqual(result, 264, delta=1)

    def test_vig_calculator(self):
        """Test vig calculation"""
        interpreter = Interpreter()
        vig_func = interpreter.global_env.get('vig_calculator')

        # Standard -110/-110 market
        vig = vig_func(-110, -110)
        self.assertAlmostEqual(vig, 4.76, places=1)


class TestLexer(unittest.TestCase):
    """Test SportsBetLang lexer"""

    def test_tokenize_numbers(self):
        """Test number tokenization"""
        lexer = Lexer("123 45.67 -89")
        tokens = lexer.tokenize()

        # Should have 3 numbers + EOF
        self.assertEqual(len(tokens), 5)  # number, number, minus, number, EOF

    def test_tokenize_strings(self):
        """Test string tokenization"""
        lexer = Lexer('"hello" \'world\'')
        tokens = lexer.tokenize()

        from lexer import TokenType
        self.assertEqual(tokens[0].type, TokenType.STRING)
        self.assertEqual(tokens[0].value, "hello")
        self.assertEqual(tokens[1].type, TokenType.STRING)
        self.assertEqual(tokens[1].value, "world")

    def test_tokenize_keywords(self):
        """Test keyword tokenization"""
        lexer = Lexer("let const if else while for")
        tokens = lexer.tokenize()

        from lexer import TokenType
        self.assertEqual(tokens[0].type, TokenType.LET)
        self.assertEqual(tokens[1].type, TokenType.CONST)
        self.assertEqual(tokens[2].type, TokenType.IF)
        self.assertEqual(tokens[3].type, TokenType.ELSE)

    def test_tokenize_operators(self):
        """Test operator tokenization"""
        lexer = Lexer("+ - * / == != < >")
        tokens = lexer.tokenize()

        from lexer import TokenType
        self.assertEqual(tokens[0].type, TokenType.PLUS)
        self.assertEqual(tokens[1].type, TokenType.MINUS)
        self.assertEqual(tokens[2].type, TokenType.MULTIPLY)
        self.assertEqual(tokens[3].type, TokenType.DIVIDE)


class TestParser(unittest.TestCase):
    """Test SportsBetLang parser"""

    def parse(self, code: str):
        """Helper to parse code"""
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        return parser.parse()

    def test_parse_assignment(self):
        """Test parsing variable assignment"""
        ast = self.parse("let x = 10")
        from parser import Program, Assignment
        self.assertIsInstance(ast, Program)
        self.assertIsInstance(ast.statements[0], Assignment)

    def test_parse_function_def(self):
        """Test parsing function definition"""
        ast = self.parse("func add(a, b) { return a + b }")
        from parser import Program, FunctionDef
        self.assertIsInstance(ast, Program)
        self.assertIsInstance(ast.statements[0], FunctionDef)
        self.assertEqual(ast.statements[0].name, "add")
        self.assertEqual(len(ast.statements[0].parameters), 2)

    def test_parse_if_statement(self):
        """Test parsing if statement"""
        ast = self.parse("if x > 5 { print(x) }")
        from parser import Program, IfStatement
        self.assertIsInstance(ast, Program)
        self.assertIsInstance(ast.statements[0], IfStatement)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
