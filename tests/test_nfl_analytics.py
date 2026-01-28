#!/usr/bin/env python3
"""Tests for NFL Analytics Library"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lib.nfl_analytics import NFLAnalytics, calculate_nfl_elo_probability


class TestNFLSpreadProbability(unittest.TestCase):
    """Test spread probability calculations"""

    def test_favorite_at_home(self):
        """Home favorite should have high cover probability"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=26.0, opponent_rating=20.0, spread=-3.5, is_home=True
        )
        self.assertIn('cover_probability', result)
        self.assertGreater(result['cover_probability'], 0.5)

    def test_underdog_away(self):
        """Away underdog should have valid cover probability"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=20.0, opponent_rating=26.0, spread=7.5, is_home=False
        )
        self.assertGreater(result['cover_probability'], 0)
        self.assertLess(result['cover_probability'], 1)

    def test_home_advantage_matters(self):
        """Home team should have better cover probability than away"""
        home = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=24.0, spread=-3.0, is_home=True
        )
        away = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=24.0, spread=-3.0, is_home=False
        )
        self.assertGreater(home['cover_probability'], away['cover_probability'])

    def test_expected_margin_includes_home_advantage(self):
        """Expected margin should include home advantage"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=20.0, spread=-3.0, is_home=True
        )
        expected = (24.0 - 20.0) + NFLAnalytics.AVG_HOME_ADVANTAGE
        self.assertAlmostEqual(result['expected_margin'], expected, places=1)

    def test_key_number_detection(self):
        """Should detect key numbers (3, 7)"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=21.0, spread=-3.0, is_home=True
        )
        self.assertTrue(result['is_key_number'])

    def test_push_probability_on_key_number(self):
        """Key numbers should have non-zero push probability"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=21.0, spread=-3.0, is_home=True
        )
        self.assertGreater(result['push_probability'], 0)

    def test_result_fields(self):
        """Result should contain all expected fields"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=20.0, spread=-3.5, is_home=True
        )
        for key in ['cover_probability', 'push_probability', 'lose_probability',
                     'expected_margin', 'spread', 'is_key_number']:
            self.assertIn(key, result)

    def test_probabilities_valid(self):
        """Cover + push + lose should approximate 1"""
        result = NFLAnalytics.calculate_spread_probability(
            team_rating=24.0, opponent_rating=20.0, spread=-3.0, is_home=True
        )
        total = result['cover_probability'] + result['push_probability'] + result['lose_probability']
        self.assertAlmostEqual(total, 1.0, places=1)


class TestNFLTotalProbability(unittest.TestCase):
    """Test total (over/under) calculations"""

    def test_total_probabilities_sum(self):
        """Over + under should sum to 1"""
        result = NFLAnalytics.calculate_total_probability(
            team1_avg=24.0, team2_avg=21.0, total_line=45.5
        )
        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_high_scoring_teams_over(self):
        """High scoring teams should favor the over"""
        result = NFLAnalytics.calculate_total_probability(
            team1_avg=28.0, team2_avg=27.0, total_line=45.0
        )
        self.assertGreater(result['over_probability'], 0.5)

    def test_low_scoring_teams_under(self):
        """Low scoring teams should favor the under"""
        result = NFLAnalytics.calculate_total_probability(
            team1_avg=17.0, team2_avg=16.0, total_line=45.0
        )
        self.assertGreater(result['under_probability'], 0.5)

    def test_pace_factor_increases_total(self):
        """Higher pace factor should increase expected total"""
        normal = NFLAnalytics.calculate_total_probability(
            team1_avg=24.0, team2_avg=21.0, total_line=45.5, pace_factor=1.0
        )
        fast = NFLAnalytics.calculate_total_probability(
            team1_avg=24.0, team2_avg=21.0, total_line=45.5, pace_factor=1.1
        )
        self.assertGreater(fast['expected_total'], normal['expected_total'])

    def test_expected_total(self):
        """Expected total should be sum of averages"""
        result = NFLAnalytics.calculate_total_probability(
            team1_avg=24.0, team2_avg=21.0, total_line=45.5
        )
        self.assertAlmostEqual(result['expected_total'], 45.0, places=1)


class TestNFLSimulation(unittest.TestCase):
    """Test game and season simulation"""

    def test_simulate_game_structure(self):
        """Should return valid game result"""
        result = NFLAnalytics.simulate_game(
            home_rating=24.0, away_rating=21.0, seed=42
        )
        for key in ['home_score', 'away_score', 'margin', 'total', 'result']:
            self.assertIn(key, result)
        self.assertGreaterEqual(result['home_score'], 0)

    def test_simulate_game_reproducible(self):
        """Same seed should produce same result"""
        r1 = NFLAnalytics.simulate_game(24.0, 21.0, seed=100)
        r2 = NFLAnalytics.simulate_game(24.0, 21.0, seed=100)
        self.assertEqual(r1['home_score'], r2['home_score'])
        self.assertEqual(r1['away_score'], r2['away_score'])

    def test_simulate_game_margin(self):
        """Margin should equal home - away"""
        result = NFLAnalytics.simulate_game(24.0, 21.0, seed=42)
        self.assertEqual(result['margin'], result['home_score'] - result['away_score'])

    def test_simulate_game_total(self):
        """Total should equal sum of scores"""
        result = NFLAnalytics.simulate_game(24.0, 21.0, seed=42)
        self.assertEqual(result['total'], result['home_score'] + result['away_score'])

    def test_simulate_season(self):
        """Should simulate season with standings"""
        teams = {'TeamA': 24.0, 'TeamB': 22.0, 'TeamC': 20.0, 'TeamD': 18.0}
        result = NFLAnalytics.simulate_season(teams, games_per_team=4, seed=42)
        self.assertIn('standings', result)
        self.assertIn('matches', result)
        self.assertEqual(len(result['standings']), 4)

    def test_season_standings_have_win_pct(self):
        """Standings should include win percentage"""
        teams = {'A': 25.0, 'B': 20.0}
        result = NFLAnalytics.simulate_season(teams, games_per_team=4, seed=42)
        for team, stats in result['standings'].items():
            self.assertIn('win_pct', stats)
            self.assertGreaterEqual(stats['win_pct'], 0.0)
            self.assertLessEqual(stats['win_pct'], 1.0)

    def test_season_matches_generated(self):
        """Season should generate matches"""
        teams = {'A': 24.0, 'B': 22.0, 'C': 20.0}
        result = NFLAnalytics.simulate_season(teams, games_per_team=4, seed=42)
        self.assertGreater(len(result['matches']), 0)


class TestNFLKeyNumbers(unittest.TestCase):
    """Test key number analysis"""

    def test_key_number_3(self):
        """3 should be identified as key number"""
        result = NFLAnalytics.analyze_key_numbers(-3.0)
        self.assertTrue(result['is_key_number'])
        self.assertIn('CRITICAL', result['advice'])

    def test_key_number_7(self):
        """7 should be identified as key number"""
        result = NFLAnalytics.analyze_key_numbers(-7.0)
        self.assertTrue(result['is_key_number'])
        self.assertIn('CRITICAL', result['advice'])

    def test_key_number_10(self):
        """10 should be identified as key number"""
        result = NFLAnalytics.analyze_key_numbers(-10.0)
        self.assertTrue(result['is_key_number'])

    def test_non_key_number(self):
        """Non-key numbers should be identified"""
        result = NFLAnalytics.analyze_key_numbers(-5.5)
        self.assertFalse(result['is_key_number'])

    def test_frequency_for_key_numbers(self):
        """Key numbers should have non-zero frequency"""
        result = NFLAnalytics.analyze_key_numbers(-3.0)
        self.assertGreater(result['frequency'], 0)

    def test_nearest_key_numbers(self):
        """Should find nearest key numbers"""
        result = NFLAnalytics.analyze_key_numbers(-5.0)
        self.assertIn('nearest_key_below', result)
        self.assertIn('nearest_key_above', result)


class TestNFLElo(unittest.TestCase):
    """Test Elo probability calculations"""

    def test_equal_teams_no_home(self):
        """Equal Elo with no home advantage should give 50%"""
        prob = calculate_nfl_elo_probability(1500, 1500, home_advantage=0)
        self.assertAlmostEqual(prob, 0.5, places=2)

    def test_stronger_team_favored(self):
        """Higher Elo team should be favored"""
        prob = calculate_nfl_elo_probability(1600, 1400, home_advantage=0)
        self.assertGreater(prob, 0.5)

    def test_home_advantage(self):
        """Home advantage should boost win probability"""
        no_home = calculate_nfl_elo_probability(1500, 1500, home_advantage=0)
        with_home = calculate_nfl_elo_probability(1500, 1500, home_advantage=65)
        self.assertGreater(with_home, no_home)

    def test_probability_bounds(self):
        """Probability should be between 0 and 1"""
        prob = calculate_nfl_elo_probability(2000, 1000)
        self.assertGreater(prob, 0)
        self.assertLess(prob, 1)

    def test_symmetric(self):
        """Swapping teams should give complementary probability"""
        prob1 = calculate_nfl_elo_probability(1600, 1400, home_advantage=0)
        prob2 = calculate_nfl_elo_probability(1400, 1600, home_advantage=0)
        self.assertAlmostEqual(prob1 + prob2, 1.0, places=5)


if __name__ == '__main__':
    unittest.main()
