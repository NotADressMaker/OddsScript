#!/usr/bin/env python3
"""Tests for NBA Analytics Library"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lib.nba_analytics import NBAAnalytics


class TestNBAPaceAdjustedTotal(unittest.TestCase):
    """Test pace-adjusted total calculations"""

    def test_expected_total_reasonable(self):
        """Should calculate reasonable expected total"""
        result = NBAAnalytics.calculate_pace_adjusted_total(
            team1_pace=100.0, team2_pace=98.0,
            team1_off_rating=115.0, team2_off_rating=112.0,
            team1_def_rating=108.0, team2_def_rating=110.0
        )
        self.assertIn('total_expected', result)
        self.assertGreater(result['total_expected'], 180)
        self.assertLess(result['total_expected'], 280)

    def test_faster_pace_higher_total(self):
        """Faster pace should produce higher total"""
        slow = NBAAnalytics.calculate_pace_adjusted_total(
            team1_pace=90.0, team2_pace=90.0,
            team1_off_rating=110.0, team2_off_rating=110.0,
            team1_def_rating=110.0, team2_def_rating=110.0
        )
        fast = NBAAnalytics.calculate_pace_adjusted_total(
            team1_pace=105.0, team2_pace=105.0,
            team1_off_rating=110.0, team2_off_rating=110.0,
            team1_def_rating=110.0, team2_def_rating=110.0
        )
        self.assertGreater(fast['total_expected'], slow['total_expected'])

    def test_game_pace_is_average(self):
        """Game pace should be average of both teams"""
        result = NBAAnalytics.calculate_pace_adjusted_total(
            team1_pace=100.0, team2_pace=96.0,
            team1_off_rating=110.0, team2_off_rating=110.0,
            team1_def_rating=110.0, team2_def_rating=110.0
        )
        self.assertEqual(result['game_pace'], 98.0)

    def test_better_offense_scores_more(self):
        """Team with better offense should score more"""
        result = NBAAnalytics.calculate_pace_adjusted_total(
            team1_pace=100.0, team2_pace=100.0,
            team1_off_rating=120.0, team2_off_rating=105.0,
            team1_def_rating=110.0, team2_def_rating=110.0
        )
        self.assertGreater(result['team1_expected'], result['team2_expected'])


class TestNBASpreadProbability(unittest.TestCase):
    """Test spread probability calculations"""

    def test_favorite_cover(self):
        """Better team should have higher cover probability"""
        result = NBAAnalytics.calculate_spread_probability(
            team_rating=115.0, opponent_rating=105.0, spread=-5.0, is_home=True
        )
        self.assertIn('cover_probability', result)
        self.assertGreater(result['cover_probability'], 0.5)

    def test_home_advantage(self):
        """Home team should have advantage"""
        home = NBAAnalytics.calculate_spread_probability(
            team_rating=110.0, opponent_rating=110.0, spread=-3.0, is_home=True
        )
        away = NBAAnalytics.calculate_spread_probability(
            team_rating=110.0, opponent_rating=110.0, spread=-3.0, is_home=False
        )
        self.assertGreater(home['cover_probability'], away['cover_probability'])

    def test_probability_bounds(self):
        """Cover probability should be between 0 and 1"""
        result = NBAAnalytics.calculate_spread_probability(
            team_rating=120.0, opponent_rating=100.0, spread=-10.0, is_home=True
        )
        self.assertGreater(result['cover_probability'], 0)
        self.assertLess(result['cover_probability'], 1)

    def test_confidence_levels(self):
        """Should assign confidence levels based on z-score"""
        strong = NBAAnalytics.calculate_spread_probability(
            team_rating=125.0, opponent_rating=100.0, spread=-3.0, is_home=True
        )
        self.assertEqual(strong['confidence'], 'high')

    def test_expected_margin(self):
        """Expected margin should reflect rating difference + home advantage"""
        result = NBAAnalytics.calculate_spread_probability(
            team_rating=115.0, opponent_rating=110.0, spread=-5.0, is_home=True
        )
        expected = (115.0 - 110.0) + NBAAnalytics.AVG_HOME_ADVANTAGE
        self.assertAlmostEqual(result['expected_margin'], expected, places=1)


class TestNBATotalProbability(unittest.TestCase):
    """Test total points probability"""

    def test_high_scoring_teams_favor_over(self):
        """High-scoring matchup should favor the over"""
        result = NBAAnalytics.calculate_total_probability(
            team1_avg=120.0, team2_avg=118.0, total_line=220.0
        )
        self.assertGreater(result['over_probability'], 0.5)

    def test_low_scoring_teams_favor_under(self):
        """Low-scoring matchup should favor the under"""
        result = NBAAnalytics.calculate_total_probability(
            team1_avg=100.0, team2_avg=98.0, total_line=220.0
        )
        self.assertLess(result['over_probability'], 0.5)

    def test_probabilities_sum_to_one(self):
        """Over + under should sum to 1"""
        result = NBAAnalytics.calculate_total_probability(
            team1_avg=115.0, team2_avg=112.0, total_line=230.0
        )
        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_edge_calculation(self):
        """Edge should be positive when expected differs from line"""
        result = NBAAnalytics.calculate_total_probability(
            team1_avg=120.0, team2_avg=118.0, total_line=230.0
        )
        self.assertGreater(result['edge'], 0)


class TestNBASimulation(unittest.TestCase):
    """Test game simulation"""

    def test_simulate_game(self):
        """Simulated game should return valid scores"""
        result = NBAAnalytics.simulate_game(
            home_rating=110.0, away_rating=105.0, seed=42
        )
        self.assertIn('home_score', result)
        self.assertIn('away_score', result)
        self.assertGreaterEqual(result['home_score'], 0)
        self.assertGreaterEqual(result['away_score'], 0)

    def test_simulation_reproducible(self):
        """Same seed should produce same result"""
        r1 = NBAAnalytics.simulate_game(home_rating=110.0, away_rating=105.0, seed=99)
        r2 = NBAAnalytics.simulate_game(home_rating=110.0, away_rating=105.0, seed=99)
        self.assertEqual(r1['home_score'], r2['home_score'])
        self.assertEqual(r1['away_score'], r2['away_score'])

    def test_game_result_valid(self):
        """Game result should be home_win, away_win, or overtime"""
        result = NBAAnalytics.simulate_game(110.0, 105.0, seed=42)
        self.assertIn(result['result'], ['home_win', 'away_win', 'overtime'])

    def test_margin_and_total(self):
        """Margin and total should be consistent with scores"""
        result = NBAAnalytics.simulate_game(110.0, 105.0, seed=42)
        self.assertEqual(result['margin'], result['home_score'] - result['away_score'])
        self.assertEqual(result['total'], result['home_score'] + result['away_score'])

    def test_simulate_season(self):
        """Season simulation should produce standings"""
        teams = {'Lakers': 110.0, 'Celtics': 112.0, 'Warriors': 108.0, 'Bucks': 111.0}
        result = NBAAnalytics.simulate_season(teams, games_per_team=10, seed=42)
        self.assertIn('standings', result)
        self.assertEqual(len(result['standings']), 4)

    def test_season_win_pct(self):
        """Season standings should have valid win percentages"""
        teams = {'A': 115.0, 'B': 105.0}
        result = NBAAnalytics.simulate_season(teams, games_per_team=10, seed=42)
        for team, stats in result['standings'].items():
            self.assertIn('win_pct', stats)
            self.assertGreaterEqual(stats['win_pct'], 0.0)
            self.assertLessEqual(stats['win_pct'], 1.0)


class TestNBAPlayerProps(unittest.TestCase):
    """Test player prop calculations"""

    def test_over_probability(self):
        """Player averaging above line should have >50% over probability"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=28.5, prop_line=25.5
        )
        self.assertIn('over_probability', result)
        self.assertGreater(result['over_probability'], 0.5)

    def test_under_probability(self):
        """Player averaging below line should have <50% over probability"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=20.0, prop_line=25.5
        )
        self.assertLess(result['over_probability'], 0.5)

    def test_usage_adjustment(self):
        """Higher usage adjustment should shift probabilities"""
        normal = NBAAnalytics.calculate_player_prop_probability(
            player_avg=25.0, prop_line=25.5, usage_adjustment=1.0
        )
        boosted = NBAAnalytics.calculate_player_prop_probability(
            player_avg=25.0, prop_line=25.5, usage_adjustment=1.2
        )
        self.assertGreater(boosted['over_probability'], normal['over_probability'])

    def test_custom_std_dev(self):
        """Custom std dev should be used when provided"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=25.0, prop_line=25.5, player_std_dev=5.0
        )
        self.assertEqual(result['std_dev'], 5.0)

    def test_estimated_std_dev(self):
        """Std dev should be estimated when not provided"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=20.0, prop_line=20.5
        )
        self.assertAlmostEqual(result['std_dev'], 20.0 * 0.25, places=1)

    def test_probabilities_sum_to_one(self):
        """Over + under should sum to 1"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=25.0, prop_line=24.5
        )
        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_edge_positive_when_avg_above_line(self):
        """Edge should be positive when average exceeds line"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=30.0, prop_line=25.0
        )
        self.assertGreater(result['edge'], 0)

    def test_adjusted_average(self):
        """Adjusted average should reflect usage adjustment"""
        result = NBAAnalytics.calculate_player_prop_probability(
            player_avg=25.0, prop_line=25.0, usage_adjustment=1.1
        )
        self.assertAlmostEqual(result['adjusted_average'], 27.5, places=1)


if __name__ == '__main__':
    unittest.main()
