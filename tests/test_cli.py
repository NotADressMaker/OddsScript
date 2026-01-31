#!/usr/bin/env python3
"""CLI smoke tests."""

import subprocess
import sys
import unittest


class TestCLI(unittest.TestCase):
    def test_example_program_runs(self):
        result = subprocess.run(
            [sys.executable, "sportsbetlang.py", "examples/01_basic_bet.odds"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Basic Sports Betting", result.stdout)


if __name__ == "__main__":
    unittest.main()
