#!/usr/bin/env python3
"""Tests for shared betting math utilities."""

import unittest

from lib.betting_core import (
    american_to_implied_prob,
    expected_value_per_1_risk,
    payout_per_1_risk,
    prob_to_american,
)


class TestBettingCoreMath(unittest.TestCase):
    def test_american_to_implied_prob(self):
        self.assertAlmostEqual(american_to_implied_prob(-110), 0.5238095, places=6)
        self.assertAlmostEqual(american_to_implied_prob(150), 0.4, places=6)

    def test_prob_to_american(self):
        self.assertEqual(prob_to_american(0.6), -150)
        self.assertEqual(prob_to_american(0.4), 150)

    def test_payout_per_1_risk(self):
        self.assertAlmostEqual(payout_per_1_risk(-120), 100 / 120, places=6)
        self.assertAlmostEqual(payout_per_1_risk(200), 2.0, places=6)

    def test_expected_value_per_1_risk(self):
        ev = expected_value_per_1_risk(0.55, -110)
        self.assertGreater(ev, 0)


if __name__ == "__main__":
    unittest.main()
