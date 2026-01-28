#!/usr/bin/env python3
"""Tests for NHL Analytics Library"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lib.nhl_analytics import (
    NHLAdvancedAnalytics, NHLAnalytics,
    TeamMetrics, GoaltenderStats, ShotQuality, Situation
)


class TestNHLExpectedGoals(unittest.TestCase):
    """Test expected goals calculations"""

    def test_xg_basic(self):
        """Basic shot should produce valid xG"""
        xg = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=20.0, shot_angle=45.0, shot_type='wrist'
        )
        self.assertGreater(xg, 0)
        self.assertLess(xg, 1)

    def test_xg_close_range_higher(self):
        """Close-range shot should have higher xG"""
        close = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=10.0, shot_angle=60.0,
            shot_quality=ShotQuality.HIGH_DANGER
        )
        far = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=50.0, shot_angle=20.0,
            shot_quality=ShotQuality.LOW_DANGER
        )
        self.assertGreater(close, far)

    def test_xg_rebound_bonus(self):
        """Rebound shots should have higher xG"""
        normal = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=20.0, shot_angle=45.0, rebound=False
        )
        rebound = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=20.0, shot_angle=45.0, rebound=True
        )
        self.assertGreater(rebound, normal)

    def test_xg_rush_bonus(self):
        """Rush shots should have higher xG"""
        normal = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=25.0, shot_angle=30.0, rush_shot=False
        )
        rush = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=25.0, shot_angle=30.0, rush_shot=True
        )
        self.assertGreater(rush, normal)

    def test_xg_capped_at_065(self):
        """xG should never exceed 0.65"""
        xg = NHLAdvancedAnalytics.calculate_expected_goals(
            shot_distance=2.0, shot_angle=0.0, shot_type='tip',
            shot_quality=ShotQuality.HIGH_DANGER, rebound=True, rush_shot=True
        )
        self.assertLessEqual(xg, 0.65)

    def test_xg_shot_types(self):
        """Different shot types should produce different xG values"""
        wrist = NHLAdvancedAnalytics.calculate_expected_goals(20.0, 30.0, 'wrist')
        slap = NHLAdvancedAnalytics.calculate_expected_goals(20.0, 30.0, 'slap')
        tip = NHLAdvancedAnalytics.calculate_expected_goals(20.0, 30.0, 'tip')
        self.assertGreater(tip, wrist)
        self.assertGreater(tip, slap)

    def test_xg_unknown_shot_type(self):
        """Unknown shot type should use default rate"""
        xg = NHLAdvancedAnalytics.calculate_expected_goals(20.0, 30.0, 'unknown_type')
        self.assertGreater(xg, 0)

    def test_team_xg(self):
        """Team xG should be reasonable"""
        xg = NHLAdvancedAnalytics.calculate_team_expected_goals(
            shots_for=30, high_danger_shots=10,
            medium_danger_shots=12, rebounds=5, rush_shots=3
        )
        self.assertGreater(xg, 1.0)
        self.assertLess(xg, 6.0)

    def test_team_xg_more_dangerous_shots(self):
        """More high danger shots should increase team xG"""
        low_danger = NHLAdvancedAnalytics.calculate_team_expected_goals(
            shots_for=30, high_danger_shots=3,
            medium_danger_shots=7, rebounds=1, rush_shots=1
        )
        high_danger = NHLAdvancedAnalytics.calculate_team_expected_goals(
            shots_for=30, high_danger_shots=15,
            medium_danger_shots=10, rebounds=5, rush_shots=3
        )
        self.assertGreater(high_danger, low_danger)


class TestNHLCorsiFenwick(unittest.TestCase):
    """Test Corsi and Fenwick calculations"""

    def test_corsi_calculation(self):
        """Corsi should be calculated correctly"""
        result = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for=30, shots_against=25,
            blocked_shots_for=10, blocked_shots_against=8,
            missed_shots_for=5, missed_shots_against=7
        )
        self.assertIn('corsi_percentage', result)
        self.assertIn('fenwick_percentage', result)
        self.assertGreater(result['corsi_percentage'], 0)
        self.assertLess(result['corsi_percentage'], 100)

    def test_corsi_values(self):
        """Corsi for/against should be shot attempts sum"""
        result = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for=30, shots_against=25,
            blocked_shots_for=10, blocked_shots_against=8,
            missed_shots_for=5, missed_shots_against=7
        )
        self.assertEqual(result['corsi_for'], 30 + 10 + 5)
        self.assertEqual(result['corsi_against'], 25 + 8 + 7)

    def test_fenwick_excludes_blocks(self):
        """Fenwick should exclude blocked shots"""
        result = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for=30, shots_against=25,
            blocked_shots_for=10, blocked_shots_against=8,
            missed_shots_for=5, missed_shots_against=7
        )
        self.assertEqual(result['fenwick_for'], 30 + 5)
        self.assertEqual(result['fenwick_against'], 25 + 7)

    def test_dominant_possession(self):
        """Team with more shot attempts should have >50% Corsi"""
        result = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for=35, shots_against=20,
            blocked_shots_for=12, blocked_shots_against=6,
            missed_shots_for=8, missed_shots_against=4
        )
        self.assertGreater(result['corsi_percentage'], 50)
        self.assertGreater(result['corsi_differential'], 0)

    def test_equal_possession(self):
        """Equal shot attempts should give ~50% Corsi"""
        result = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for=30, shots_against=30,
            blocked_shots_for=10, blocked_shots_against=10,
            missed_shots_for=5, missed_shots_against=5
        )
        self.assertAlmostEqual(result['corsi_percentage'], 50.0, places=1)


class TestNHLPDO(unittest.TestCase):
    """Test PDO calculation"""

    def test_average_pdo(self):
        """Average save% and shooting% should give ~100 PDO"""
        pdo = NHLAdvancedAnalytics.calculate_pdo(
            save_percentage=0.910, shooting_percentage=0.090
        )
        self.assertAlmostEqual(pdo, 100.0, places=0)

    def test_lucky_team_high_pdo(self):
        """High save% and shooting% should give high PDO"""
        pdo = NHLAdvancedAnalytics.calculate_pdo(
            save_percentage=0.930, shooting_percentage=0.120
        )
        self.assertGreater(pdo, 100.0)

    def test_unlucky_team_low_pdo(self):
        """Low save% and shooting% should give low PDO"""
        pdo = NHLAdvancedAnalytics.calculate_pdo(
            save_percentage=0.890, shooting_percentage=0.070
        )
        self.assertLess(pdo, 100.0)


class TestNHLGoaltenderAnalysis(unittest.TestCase):
    """Test goaltender performance analysis"""

    def test_goaltender_stats(self):
        """Should return comprehensive goaltender analysis"""
        result = NHLAdvancedAnalytics.analyze_goaltender_performance(
            saves=900, shots_against=980, goals_against=80,
            games_played=35, high_danger_saves=250,
            high_danger_shots=300, expected_goals_against=85.0
        )
        self.assertIn('save_percentage', result)
        self.assertIn('goals_against_average', result)
        self.assertIn('high_danger_save_pct', result)
        self.assertIn('goals_saved_above_expected', result)
        self.assertGreater(result['save_percentage'], 0.8)
        self.assertLess(result['save_percentage'], 1.0)

    def test_gaa_calculation(self):
        """GAA should be goals per game, not multiplied by 60"""
        result = NHLAdvancedAnalytics.analyze_goaltender_performance(
            saves=900, shots_against=980, goals_against=80,
            games_played=40, high_danger_saves=250,
            high_danger_shots=300, expected_goals_against=85.0
        )
        expected_gaa = 80 / 40  # 2.0
        self.assertAlmostEqual(result['goals_against_average'], expected_gaa, places=2)

    def test_elite_goaltender(self):
        """Elite goaltender should be rated accordingly"""
        result = NHLAdvancedAnalytics.analyze_goaltender_performance(
            saves=950, shots_against=1000, goals_against=50,
            games_played=40, high_danger_saves=280,
            high_danger_shots=300, expected_goals_against=75.0
        )
        self.assertGreater(result['save_percentage'], 0.920)
        self.assertEqual(result['performance_vs_expected'], 'elite')

    def test_gsax_positive_for_good_goalie(self):
        """GSAx should be positive when goalie beats expected"""
        result = NHLAdvancedAnalytics.analyze_goaltender_performance(
            saves=920, shots_against=980, goals_against=60,
            games_played=35, high_danger_saves=250,
            high_danger_shots=300, expected_goals_against=75.0
        )
        self.assertGreater(result['goals_saved_above_expected'], 0)

    def test_zero_games_safety(self):
        """Should handle zero games without error"""
        result = NHLAdvancedAnalytics.analyze_goaltender_performance(
            saves=0, shots_against=0, goals_against=0,
            games_played=0, high_danger_saves=0,
            high_danger_shots=0, expected_goals_against=0.0
        )
        self.assertEqual(result['goals_against_average'], 0)


class TestNHLTeamStrength(unittest.TestCase):
    """Test team strength calculations"""

    def test_strong_team(self):
        """Good team metrics should produce high strength"""
        result = NHLAdvancedAnalytics.calculate_team_strength(
            goals_for=3.5, goals_against=2.5,
            xg_for=3.2, xg_against=2.3,
            corsi_pct=55.0, pdo=101.0,
            recent_form=[1, 1, 1, 0, 1, 1, 0, 1, 1, 1]
        )
        self.assertIn('strength_rating', result)
        self.assertIn('tier', result)
        self.assertGreater(result['strength_rating'], 50)

    def test_weak_team(self):
        """Poor team metrics should produce low strength"""
        result = NHLAdvancedAnalytics.calculate_team_strength(
            goals_for=2.0, goals_against=3.5,
            xg_for=2.0, xg_against=3.5,
            corsi_pct=42.0, pdo=97.0,
            recent_form=[0, 0, 1, 0, 0, 0, 1, 0, 0, 0]
        )
        self.assertLess(result['strength_rating'], 50)

    def test_tier_classification(self):
        """Team tiers should be assigned correctly"""
        elite = NHLAdvancedAnalytics.calculate_team_strength(
            goals_for=4.0, goals_against=2.0,
            xg_for=3.5, xg_against=2.0,
            corsi_pct=58.0, pdo=102.0,
            recent_form=[1, 1, 1, 1, 1, 1, 1, 1, 0, 1]
        )
        self.assertEqual(elite['tier'], 'elite')

    def test_empty_recent_form(self):
        """Should handle empty recent form"""
        result = NHLAdvancedAnalytics.calculate_team_strength(
            goals_for=3.0, goals_against=3.0,
            xg_for=3.0, xg_against=3.0,
            corsi_pct=50.0, pdo=100.0,
            recent_form=[]
        )
        self.assertIn('strength_rating', result)

    def test_pdo_regression_adjustment(self):
        """High PDO should predict regression"""
        result = NHLAdvancedAnalytics.calculate_team_strength(
            goals_for=3.0, goals_against=2.5,
            xg_for=3.0, xg_against=2.5,
            corsi_pct=52.0, pdo=104.0,
            recent_form=[1, 1, 0, 1, 0]
        )
        self.assertGreater(result['pdo_regression_expected'], 0)


class TestNHLFirstPeriod(unittest.TestCase):
    """Test first period probability calculations"""

    def test_first_period_probabilities(self):
        """Should return valid first period probabilities"""
        result = NHLAdvancedAnalytics.calculate_first_period_probability(
            home_goals_avg=3.2, away_goals_avg=2.8, total_line=1.5
        )
        self.assertIn('home_win_1p', result)
        self.assertIn('away_win_1p', result)
        self.assertIn('draw_1p', result)
        self.assertIn('scoreless_probability', result)
        # Probabilities should sum to ~1
        total = result['home_win_1p'] + result['away_win_1p'] + result['draw_1p']
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_scoreless_probability_reasonable(self):
        """Scoreless first period should be a plausible percentage"""
        result = NHLAdvancedAnalytics.calculate_first_period_probability(
            home_goals_avg=3.0, away_goals_avg=3.0
        )
        # Typically 30-50% of first periods are scoreless
        self.assertGreater(result['scoreless_probability'], 0.15)
        self.assertLess(result['scoreless_probability'], 0.70)

    def test_expected_goals_fraction(self):
        """First period expected goals should be ~30% of game total"""
        result = NHLAdvancedAnalytics.calculate_first_period_probability(
            home_goals_avg=3.0, away_goals_avg=3.0
        )
        # Expected goals should be roughly 30% of full game rate
        self.assertLess(result['expected_goals_1p'], 3.0)
        self.assertGreater(result['expected_goals_1p'], 1.0)

    def test_over_under_probabilities(self):
        """Over/under should sum to ~1"""
        result = NHLAdvancedAnalytics.calculate_first_period_probability(
            home_goals_avg=3.5, away_goals_avg=3.0, total_line=1.5
        )
        total = result['over_total'] + result['under_total']
        self.assertAlmostEqual(total, 1.0, places=2)


class TestNHLScoreAdjustedCorsi(unittest.TestCase):
    """Test score-adjusted Corsi calculations"""

    def test_tied_game_no_adjustment(self):
        """Tied game should have no score adjustment"""
        result = NHLAdvancedAnalytics.calculate_score_adjusted_corsi(
            shots_for=30, shots_against=25,
            blocked_for=10, blocked_against=8,
            missed_for=5, missed_against=7,
            goal_differential=0,
            time_trailing=0.0, time_leading=0.0, time_tied=60.0
        )
        self.assertAlmostEqual(result['score_effect'], 0.0, places=1)
        self.assertAlmostEqual(result['raw_corsi_pct'], result['adjusted_corsi_pct'], places=1)

    def test_leading_team_adjustment(self):
        """Leading team should get upward Corsi adjustment"""
        result = NHLAdvancedAnalytics.calculate_score_adjusted_corsi(
            shots_for=25, shots_against=30,
            blocked_for=8, blocked_against=10,
            missed_for=4, missed_against=8,
            goal_differential=2,
            time_trailing=0.0, time_leading=40.0, time_tied=20.0
        )
        # Leading team often has fewer shots; adjustment should boost their Corsi
        self.assertGreater(result['adjusted_corsi_pct'], result['raw_corsi_pct'])

    def test_trailing_team_adjustment(self):
        """Trailing team should get downward Corsi adjustment"""
        result = NHLAdvancedAnalytics.calculate_score_adjusted_corsi(
            shots_for=35, shots_against=20,
            blocked_for=12, blocked_against=6,
            missed_for=8, missed_against=4,
            goal_differential=-2,
            time_trailing=40.0, time_leading=0.0, time_tied=20.0
        )
        # Trailing team inflates shots; adjustment should reduce their Corsi
        self.assertLess(result['adjusted_corsi_pct'], result['raw_corsi_pct'])

    def test_zero_time_defaults(self):
        """Zero time should default without crashing"""
        result = NHLAdvancedAnalytics.calculate_score_adjusted_corsi(
            shots_for=30, shots_against=25,
            blocked_for=10, blocked_against=8,
            missed_for=5, missed_against=7,
            goal_differential=1
        )
        self.assertIn('adjusted_corsi_pct', result)


class TestNHLPlayerProps(unittest.TestCase):
    """Test NHL player prop probability calculations"""

    def test_goals_prop(self):
        """Should calculate goals prop probability"""
        result = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=0.45, prop_line=0.5, stat_type='goals'
        )
        self.assertIn('over_probability', result)
        self.assertIn('under_probability', result)
        self.assertGreater(result['over_probability'], 0)
        self.assertLess(result['over_probability'], 1)

    def test_points_prop(self):
        """Should calculate points prop probability"""
        result = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=1.2, prop_line=0.5, stat_type='points'
        )
        # High average vs low line should favor over
        self.assertGreater(result['over_probability'], 0.5)

    def test_saves_prop_uses_normal(self):
        """Saves prop should use normal distribution"""
        result = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=28.0, prop_line=27.5, stat_type='saves'
        )
        self.assertIn('over_probability', result)
        # Push probability should be 0 for normal distribution
        self.assertEqual(result['push_probability'], 0.0)

    def test_opponent_adjustment(self):
        """Weaker opponent should boost expected stats"""
        normal = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=0.5, prop_line=0.5, stat_type='goals',
            opponent_adjustment=1.0
        )
        weak_opp = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=0.5, prop_line=0.5, stat_type='goals',
            opponent_adjustment=1.3
        )
        self.assertGreater(weak_opp['over_probability'], normal['over_probability'])

    def test_home_ice_advantage(self):
        """Home ice should slightly boost stats"""
        home = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=0.8, prop_line=0.5, stat_type='points', home_ice=True
        )
        away = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=0.8, prop_line=0.5, stat_type='points', home_ice=False
        )
        self.assertGreater(home['adjusted_average'], away['adjusted_average'])

    def test_recommendation_over(self):
        """Strong over edge should recommend over"""
        result = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=1.5, prop_line=0.5, stat_type='shots'
        )
        self.assertEqual(result['recommendation'], 'over')

    def test_recommendation_no_edge(self):
        """No edge should recommend no_edge"""
        result = NHLAdvancedAnalytics.calculate_player_prop_probability(
            player_avg=28.0, prop_line=28.0, stat_type='saves'
        )
        self.assertEqual(result['recommendation'], 'no_edge')


class TestNHLBettingEdge(unittest.TestCase):
    """Test betting edge analysis"""

    def test_positive_edge(self):
        """Should detect positive edge"""
        result = NHLAdvancedAnalytics.analyze_betting_edge(
            predicted_probability=0.60,
            offered_odds=2.2,
            confidence_interval=(0.55, 0.65),
            bankroll=1000
        )
        self.assertGreater(result['edge_percentage'], 0)
        self.assertGreater(result['expected_value_pct'], 0)

    def test_no_edge(self):
        """Should detect no edge when probability matches odds"""
        result = NHLAdvancedAnalytics.analyze_betting_edge(
            predicted_probability=0.50,
            offered_odds=2.0,
            confidence_interval=(0.45, 0.55),
            bankroll=1000
        )
        self.assertAlmostEqual(result['edge_percentage'], 0, places=0)

    def test_kelly_fraction_without_kelly(self):
        """Kelly fraction should be 0 when use_kelly=False"""
        result = NHLAdvancedAnalytics.analyze_betting_edge(
            predicted_probability=0.60,
            offered_odds=2.2,
            confidence_interval=(0.55, 0.65),
            bankroll=1000,
            use_kelly=False
        )
        self.assertEqual(result['kelly_fraction'], 0.0)

    def test_bet_recommendation_tiers(self):
        """Should produce valid bet recommendations"""
        strong = NHLAdvancedAnalytics.analyze_betting_edge(
            predicted_probability=0.70,
            offered_odds=2.0,
            confidence_interval=(0.65, 0.75),
            bankroll=1000
        )
        self.assertEqual(strong['bet_recommendation'], 'strong_bet')

        no_bet = NHLAdvancedAnalytics.analyze_betting_edge(
            predicted_probability=0.50,
            offered_odds=2.0,
            confidence_interval=(0.45, 0.55),
            bankroll=1000
        )
        self.assertEqual(no_bet['bet_recommendation'], 'pass')


class TestNHLLiveBetting(unittest.TestCase):
    """Test live betting edge calculations"""

    def test_home_leading(self):
        """Home team leading should have higher win probability"""
        result = NHLAdvancedAnalytics.calculate_live_betting_edge(
            current_score_home=3, current_score_away=1,
            time_remaining_mins=20.0,
            home_team_strength=0.55, away_team_strength=0.50,
            live_odds={'home': 1.3, 'away': 4.0}
        )
        self.assertGreater(result['home_win_probability'], 0.5)
        self.assertIn('best_bet', result)

    def test_tied_game(self):
        """Tied game should have more balanced probabilities"""
        result = NHLAdvancedAnalytics.calculate_live_betting_edge(
            current_score_home=2, current_score_away=2,
            time_remaining_mins=30.0,
            home_team_strength=0.50, away_team_strength=0.50,
            live_odds={'home': 1.9, 'away': 1.9}
        )
        self.assertAlmostEqual(
            result['home_win_probability'], 0.5, delta=0.15
        )


class TestNHLBasicAnalytics(unittest.TestCase):
    """Test backward-compatible NHLAnalytics class"""

    def test_moneyline_probability(self):
        """Should calculate valid moneyline probabilities"""
        result = NHLAnalytics.calculate_moneyline_probability(
            team_goals_avg=3.2, opponent_goals_avg=2.8, is_home=True
        )
        self.assertIn('win_probability', result)
        self.assertGreater(result['win_probability'], 0)
        self.assertLess(result['win_probability'], 1)

    def test_moneyline_probabilities_valid(self):
        """Win and loss probabilities should be valid"""
        result = NHLAnalytics.calculate_moneyline_probability(
            team_goals_avg=3.0, opponent_goals_avg=3.0, is_home=True
        )
        self.assertGreater(result['win_probability'], 0)
        self.assertLess(result['win_probability'], 1)
        self.assertGreater(result['loss_probability'], 0)
        # OT probability should be included
        self.assertIn('overtime_probability', result)

    def test_puckline_probability(self):
        """Should calculate puck line cover probability"""
        result = NHLAnalytics.calculate_puckline_probability(
            team_goals_avg=3.5, opponent_goals_avg=2.5, puckline=-1.5, is_home=True
        )
        self.assertIn('cover_probability', result)
        self.assertGreater(result['cover_probability'], 0)
        self.assertLess(result['cover_probability'], 1)

    def test_puckline_harder_than_moneyline(self):
        """Puck line -1.5 should be harder to cover than moneyline"""
        ml = NHLAnalytics.calculate_moneyline_probability(
            team_goals_avg=3.5, opponent_goals_avg=2.5, is_home=True
        )
        pl = NHLAnalytics.calculate_puckline_probability(
            team_goals_avg=3.5, opponent_goals_avg=2.5, puckline=-1.5, is_home=True
        )
        self.assertGreater(ml['win_probability'], pl['cover_probability'])

    def test_total_probability(self):
        """Should calculate over/under probability"""
        result = NHLAnalytics.calculate_total_probability(
            team1_goals_avg=3.0, team2_goals_avg=2.8, total_line=5.5
        )
        self.assertIn('over_probability', result)
        self.assertIn('under_probability', result)
        self.assertGreater(result['over_probability'], 0)
        self.assertGreater(result['under_probability'], 0)
        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, delta=0.02)

    def test_simulate_game(self):
        """Should simulate valid game"""
        result = NHLAnalytics.simulate_game(
            home_goals_avg=3.0, away_goals_avg=2.8, seed=42
        )
        self.assertIn('home_score', result)
        self.assertIn('away_score', result)
        self.assertGreaterEqual(result['home_score'], 0)
        self.assertIn('overtime', result)

    def test_simulate_game_reproducible(self):
        """Same seed should produce same result"""
        r1 = NHLAnalytics.simulate_game(3.0, 2.8, seed=123)
        r2 = NHLAnalytics.simulate_game(3.0, 2.8, seed=123)
        self.assertEqual(r1['home_score'], r2['home_score'])
        self.assertEqual(r1['away_score'], r2['away_score'])

    def test_home_advantage_effect(self):
        """Home team should have advantage with equal averages"""
        home = NHLAnalytics.calculate_moneyline_probability(
            team_goals_avg=3.0, opponent_goals_avg=3.0, is_home=True
        )
        away = NHLAnalytics.calculate_moneyline_probability(
            team_goals_avg=3.0, opponent_goals_avg=3.0, is_home=False
        )
        self.assertGreater(home['win_probability'], away['win_probability'])

    def test_goalie_adjustment_on_total(self):
        """Lower goalie adjustment should reduce expected total"""
        normal = NHLAnalytics.calculate_total_probability(
            team1_goals_avg=3.0, team2_goals_avg=3.0,
            total_line=5.5, goalie_adjustment=1.0
        )
        elite_goalie = NHLAnalytics.calculate_total_probability(
            team1_goals_avg=3.0, team2_goals_avg=3.0,
            total_line=5.5, goalie_adjustment=0.85
        )
        self.assertGreater(
            normal['expected_total'], elite_goalie['expected_total']
        )


class TestNHLPowerPlay(unittest.TestCase):
    """Test power play analysis"""

    def test_power_play_value(self):
        """Should calculate PP metrics"""
        result = NHLAdvancedAnalytics.calculate_power_play_value(
            pp_opportunities=100, pp_goals=25
        )
        self.assertIn('pp_percentage', result)
        self.assertAlmostEqual(result['pp_percentage'], 25.0, places=0)

    def test_above_average_pp(self):
        """Above average PP should have positive differential"""
        result = NHLAdvancedAnalytics.calculate_power_play_value(
            pp_opportunities=100, pp_goals=30, league_avg_pp_pct=0.20
        )
        self.assertGreater(result['pp_differential'], 0)


class TestNHLGamePrediction(unittest.TestCase):
    """Test game prediction with team metrics"""

    def test_predict_game(self):
        """Should predict game outcome"""
        home = TeamMetrics(
            goals_for=3.2, goals_against=2.5, shots_for=32.0, shots_against=28.0,
            corsi_for=55.0, corsi_against=45.0, fenwick_for=40.0, fenwick_against=35.0,
            save_percentage=0.920, shooting_percentage=0.10, pdo=102.0,
            power_play_pct=0.22, penalty_kill_pct=0.82, faceoff_win_pct=0.52
        )
        away = TeamMetrics(
            goals_for=2.8, goals_against=3.0, shots_for=28.0, shots_against=30.0,
            corsi_for=48.0, corsi_against=52.0, fenwick_for=33.0, fenwick_against=37.0,
            save_percentage=0.905, shooting_percentage=0.09, pdo=99.5,
            power_play_pct=0.18, penalty_kill_pct=0.79, faceoff_win_pct=0.48
        )
        home_goalie = GoaltenderStats(
            save_percentage=0.920, goals_against_average=2.3,
            high_danger_save_pct=0.850, games_started=30,
            quality_starts=20, games_saved_above_expected=5.0
        )
        away_goalie = GoaltenderStats(
            save_percentage=0.905, goals_against_average=2.8,
            high_danger_save_pct=0.810, games_started=28,
            quality_starts=15, games_saved_above_expected=-2.0
        )

        result = NHLAdvancedAnalytics.predict_game_ml(
            home, away, home_goalie, away_goalie
        )
        self.assertIn('home_win_probability', result)
        self.assertIn('away_win_probability', result)
        total = result['home_win_probability'] + result['away_win_probability']
        self.assertAlmostEqual(total, 1.0, places=2)


if __name__ == '__main__':
    unittest.main()
