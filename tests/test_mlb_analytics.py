#!/usr/bin/env python3
"""Tests for MLB Analytics Library"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lib.mlb_analytics import MLBAnalytics


class TestMLBMoneyline(unittest.TestCase):
    """Test moneyline probability calculations"""

    def test_better_team_favored(self):
        """Team with higher run average should be favored"""
        result = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=5.0, opponent_runs_avg=3.5, is_home=True
        )
        self.assertGreater(result['win_probability'], 0.5)

    def test_home_advantage(self):
        """Home team should have slight advantage"""
        home = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=4.5, opponent_runs_avg=4.5, is_home=True
        )
        away = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=4.5, opponent_runs_avg=4.5, is_home=False
        )
        self.assertGreater(home['win_probability'], away['win_probability'])

    def test_probability_bounds(self):
        """Win probability should be between 0 and 1"""
        result = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=4.5, opponent_runs_avg=4.0, is_home=True
        )
        self.assertGreater(result['win_probability'], 0)
        self.assertLess(result['win_probability'], 1)

    def test_expected_runs(self):
        """Expected runs should reflect input with home advantage"""
        result = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=5.0, opponent_runs_avg=3.0, is_home=True
        )
        self.assertAlmostEqual(
            result['expected_runs'], 5.0 + MLBAnalytics.AVG_HOME_ADVANTAGE, places=1
        )

    def test_result_fields(self):
        """Should return all expected fields"""
        result = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=4.5, opponent_runs_avg=4.0, is_home=True
        )
        for key in ['win_probability', 'tie_probability', 'loss_probability',
                     'expected_runs', 'opponent_expected_runs']:
            self.assertIn(key, result)

    def test_strong_favorite(self):
        """Large run differential should produce high win probability"""
        result = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=6.0, opponent_runs_avg=3.0, is_home=True
        )
        self.assertGreater(result['win_probability'], 0.6)


class TestMLBRunLine(unittest.TestCase):
    """Test run line calculations"""

    def test_favorite_cover_runline(self):
        """Strong favorite should have reasonable chance of covering -1.5"""
        result = MLBAnalytics.calculate_runline_probability(
            team_runs_avg=5.5, opponent_runs_avg=3.0, runline=-1.5, is_home=True
        )
        self.assertIn('cover_probability', result)
        self.assertGreater(result['cover_probability'], 0.3)

    def test_underdog_plus_runline(self):
        """Underdog +1.5 should have higher cover probability than ML"""
        ml = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=3.5, opponent_runs_avg=4.5, is_home=False
        )
        rl = MLBAnalytics.calculate_runline_probability(
            team_runs_avg=3.5, opponent_runs_avg=4.5, runline=1.5, is_home=False
        )
        self.assertGreater(rl['cover_probability'], ml['win_probability'])

    def test_runline_probability_bounds(self):
        """Cover probability should be between 0 and 1"""
        result = MLBAnalytics.calculate_runline_probability(
            team_runs_avg=4.5, opponent_runs_avg=4.0, runline=-1.5, is_home=True
        )
        self.assertGreater(result['cover_probability'], 0)
        self.assertLess(result['cover_probability'], 1)

    def test_expected_margin(self):
        """Expected margin should reflect run averages"""
        result = MLBAnalytics.calculate_runline_probability(
            team_runs_avg=5.0, opponent_runs_avg=3.5, runline=-1.5, is_home=True
        )
        # Home team has run avg + home advantage vs opponent
        self.assertGreater(result['expected_margin'], 0)

    def test_minus_runline_harder_than_moneyline(self):
        """Covering -1.5 should be harder than winning outright"""
        ml = MLBAnalytics.calculate_moneyline_probability(
            team_runs_avg=5.0, opponent_runs_avg=4.0, is_home=True
        )
        rl = MLBAnalytics.calculate_runline_probability(
            team_runs_avg=5.0, opponent_runs_avg=4.0, runline=-1.5, is_home=True
        )
        self.assertGreater(ml['win_probability'], rl['cover_probability'])


class TestMLBTotals(unittest.TestCase):
    """Test totals probability calculations"""

    def test_high_scoring_favors_over(self):
        """High-scoring teams should favor the over"""
        result = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=5.5, team2_runs_avg=5.0, total_line=8.5
        )
        self.assertGreater(result['over_probability'], 0.5)

    def test_low_scoring_favors_under(self):
        """Low-scoring teams should favor the under"""
        result = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=3.0, team2_runs_avg=3.0, total_line=8.5
        )
        self.assertLess(result['over_probability'], 0.5)

    def test_probabilities_sum_to_one(self):
        """Over + under should approximately sum to 1"""
        result = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.0, total_line=8.5
        )
        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_pitcher_adjustment(self):
        """Good pitcher (lower adjustment) should decrease total"""
        normal = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.5, total_line=8.5,
            pitcher_adjustment=1.0
        )
        ace = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.5, total_line=8.5,
            pitcher_adjustment=0.8
        )
        self.assertGreater(normal['expected_total'], ace['expected_total'])

    def test_park_factor(self):
        """Higher park factor should increase scoring"""
        neutral = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.5, total_line=8.5,
            park_factor=1.0
        )
        hitter_park = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.5, total_line=8.5,
            park_factor=1.15
        )
        self.assertGreater(hitter_park['expected_total'], neutral['expected_total'])

    def test_expected_total_with_adjustments(self):
        """Expected total should reflect all adjustments"""
        result = MLBAnalytics.calculate_total_probability(
            team1_runs_avg=4.5, team2_runs_avg=4.5, total_line=8.5,
            pitcher_adjustment=0.9, park_factor=1.1
        )
        expected = (4.5 + 4.5) * 0.9 * 1.1
        self.assertAlmostEqual(result['expected_total'], expected, places=1)


class TestMLBSimulation(unittest.TestCase):
    """Test game simulation"""

    def test_simulate_game(self):
        """Simulated game should return valid scores"""
        result = MLBAnalytics.simulate_game(
            home_runs_avg=4.5, away_runs_avg=4.0, seed=42
        )
        self.assertIn('home_score', result)
        self.assertIn('away_score', result)
        self.assertGreaterEqual(result['home_score'], 0)
        self.assertGreaterEqual(result['away_score'], 0)

    def test_reproducible_simulation(self):
        """Same seed should produce same result"""
        r1 = MLBAnalytics.simulate_game(home_runs_avg=4.5, away_runs_avg=4.0, seed=55)
        r2 = MLBAnalytics.simulate_game(home_runs_avg=4.5, away_runs_avg=4.0, seed=55)
        self.assertEqual(r1['home_score'], r2['home_score'])
        self.assertEqual(r1['away_score'], r2['away_score'])

    def test_result_field(self):
        """Should include result field"""
        result = MLBAnalytics.simulate_game(
            home_runs_avg=4.5, away_runs_avg=4.0, seed=42
        )
        self.assertIn('result', result)
        self.assertIn(result['result'], ['home_win', 'away_win', 'draw'])

    def test_total_runs(self):
        """Total runs should equal sum of scores"""
        result = MLBAnalytics.simulate_game(4.5, 4.0, seed=42)
        self.assertEqual(result['total_runs'], result['home_score'] + result['away_score'])

    def test_margin(self):
        """Margin should equal home - away"""
        result = MLBAnalytics.simulate_game(4.5, 4.0, seed=42)
        self.assertEqual(result['margin'], result['home_score'] - result['away_score'])


if __name__ == '__main__':
    unittest.main()
