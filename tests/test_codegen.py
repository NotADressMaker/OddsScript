"""Tests for SportsBetLang code generation."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sportsbetlang.core.codegen import generate_code


class TestCodegen(unittest.TestCase):
    def setUp(self):
        self.source = """
        let odds_val = -110
        let stake_val = 100
        bet moneyline "Lakers" odds odds_val stake stake_val
        parlay [{"odds": -110}, {"odds": 120}] stake 50
        print(implied_probability(odds_val))
        let nums = [1, 2, 3]
        nums[1]
        range(0, 3)
        """

    def test_generate_python(self):
        code = generate_code(self.source, language="python")
        self.assertIn("def american_to_decimal", code)
        self.assertIn("American odds cannot be 0", code)
        self.assertIn("Decimal odds must be greater than 1.0", code)
        self.assertIn("sbl_create_bet", code)
        self.assertIn("sbl_create_parlay", code)
        self.assertIn("nums[1]", code)

    def test_generate_r(self):
        code = generate_code(self.source, language="r")
        self.assertIn("sbl_create_bet", code)
        self.assertIn("sbl_create_parlay", code)
        self.assertIn("sbl_index", code)
        self.assertIn("sbl_range", code)

    def test_generate_julia(self):
        code = generate_code(self.source, language="julia")
        self.assertIn("function sbl_create_bet", code)
        self.assertIn("function sbl_create_parlay", code)
        self.assertIn("function sbl_index", code)
        self.assertIn("function sbl_range", code)


if __name__ == "__main__":
    unittest.main()
