#!/usr/bin/env python3
"""Tests for NHL Analytics Library"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
from lib.nhl_analytics import (
    NHLAdvancedAnalytics, NHLAnalytics,
    TeamMetrics, GoaltenderStats, ShotQuality, Situation,
    ReverseLineMovement, prob_to_american, american_to_implied_prob,
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


class TestAdjustedGoalieSavePct(unittest.TestCase):
    """Test goalie adjusted save % calculation"""

    def test_basic_adjusted_save_pct(self):
        """Should compute weighted save % from zone-based metrics"""
        goalie = GoaltenderStats(
            save_percentage=0.910,
            high_danger_save_pct=0.830,
            medium_danger_save_pct=0.920,
            low_danger_save_pct=0.985,
        )
        result = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(goalie)
        self.assertIn("adjusted_save_pct", result)
        self.assertGreater(result["adjusted_save_pct"], 0.8)
        self.assertLess(result["adjusted_save_pct"], 1.0)

    def test_sustainability_high(self):
        """Goalie way above career norms should be unsustainable_high"""
        goalie = GoaltenderStats(
            save_percentage=0.940,
            high_danger_save_pct=0.870,
            medium_danger_save_pct=0.950,
            low_danger_save_pct=0.995,
            career_save_pct=0.905,
        )
        result = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(goalie)
        self.assertEqual(result["sustainability"], "unsustainable_high")

    def test_sustainability_low(self):
        """Goalie way below career norms should be unsustainable_low"""
        goalie = GoaltenderStats(
            save_percentage=0.880,
            high_danger_save_pct=0.780,
            medium_danger_save_pct=0.880,
            low_danger_save_pct=0.960,
            career_save_pct=0.915,
        )
        result = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(goalie)
        self.assertEqual(result["sustainability"], "unsustainable_low")

    def test_sustainability_stable(self):
        """Goalie near career norms should be sustainable"""
        goalie = GoaltenderStats(
            save_percentage=0.910,
            high_danger_save_pct=0.830,
            medium_danger_save_pct=0.920,
            low_danger_save_pct=0.985,
            career_save_pct=0.900,
        )
        result = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(goalie)
        self.assertEqual(result["sustainability"], "sustainable")


class TestPPPKEfficiency(unittest.TestCase):
    """Test PP/PK efficiency matchup calculations"""

    def test_basic_pp_pk(self):
        """Should calculate PP expected goals from matchup"""
        home = TeamMetrics(goals_for=3.0, goals_against=2.5, pp_pct=25.0, pk_pct=82.0)
        away = TeamMetrics(goals_for=2.8, goals_against=3.0, pp_pct=18.0, pk_pct=78.0)
        result = NHLAdvancedAnalytics.calculate_pp_pk_efficiency(home, away)
        self.assertIn("home_pp_expected_goals", result)
        self.assertIn("away_pp_expected_goals", result)
        self.assertIn("total_pp_expected_goals", result)
        self.assertGreater(result["total_pp_expected_goals"], 0)

    def test_strong_pp_vs_weak_pk(self):
        """Strong PP vs weak PK should produce more PP goals"""
        strong_home = TeamMetrics(goals_for=3.0, goals_against=2.5, pp_pct=30.0, pk_pct=85.0)
        weak_away = TeamMetrics(goals_for=2.5, goals_against=3.0, pp_pct=15.0, pk_pct=72.0)
        avg_home = TeamMetrics(goals_for=3.0, goals_against=3.0, pp_pct=20.0, pk_pct=80.0)
        avg_away = TeamMetrics(goals_for=3.0, goals_against=3.0, pp_pct=20.0, pk_pct=80.0)

        strong_result = NHLAdvancedAnalytics.calculate_pp_pk_efficiency(strong_home, weak_away)
        avg_result = NHLAdvancedAnalytics.calculate_pp_pk_efficiency(avg_home, avg_away)

        self.assertGreater(
            strong_result["home_pp_expected_goals"],
            avg_result["home_pp_expected_goals"]
        )

    def test_pp_pk_differential(self):
        """Home with better special teams should have positive differential"""
        home = TeamMetrics(goals_for=3.0, goals_against=2.5, pp_pct=28.0, pk_pct=84.0)
        away = TeamMetrics(goals_for=2.8, goals_against=3.0, pp_pct=16.0, pk_pct=76.0)
        result = NHLAdvancedAnalytics.calculate_pp_pk_efficiency(home, away)
        self.assertGreater(result["pp_pk_differential"], 0)


class TestEnhancedTotal(unittest.TestCase):
    """Test the enhanced O/U total calculation"""

    def _make_teams_and_goalies(self):
        home = TeamMetrics(
            goals_for=3.2, goals_against=2.5, xg_for=3.1, xg_against=2.4,
            corsi_pct=54.0, fenwick_for=40.0, fenwick_against=35.0,
            pp_pct=24.0, pk_pct=82.0, save_percentage=0.920,
            shooting_percentage=0.10,
        )
        away = TeamMetrics(
            goals_for=2.8, goals_against=3.0, xg_for=2.7, xg_against=2.9,
            corsi_pct=48.0, fenwick_for=33.0, fenwick_against=37.0,
            pp_pct=18.0, pk_pct=78.0, save_percentage=0.905,
            shooting_percentage=0.09,
        )
        home_g = GoaltenderStats(
            save_percentage=0.920, high_danger_save_pct=0.850,
            medium_danger_save_pct=0.930, low_danger_save_pct=0.990,
            games_saved_above_expected=5.0,
        )
        away_g = GoaltenderStats(
            save_percentage=0.905, high_danger_save_pct=0.810,
            medium_danger_save_pct=0.900, low_danger_save_pct=0.975,
            games_saved_above_expected=-2.0,
        )
        return home, away, home_g, away_g

    def test_returns_all_fields(self):
        """Should return all expected fields"""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_enhanced_total(home, away, hg, ag, 6.5)
        self.assertIn("expected_total", result)
        self.assertIn("over_probability", result)
        self.assertIn("under_probability", result)
        self.assertIn("over_true_odds", result)
        self.assertIn("under_true_odds", result)
        self.assertIn("components", result)
        self.assertIn("goalie_sustainability", result)

    def test_probabilities_sum_to_one(self):
        """Over + under + push should approximate 1"""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_enhanced_total(home, away, hg, ag, 6.5)
        total = result["over_probability"] + result["under_probability"] + result["push_probability"]
        self.assertAlmostEqual(total, 1.0, delta=0.02)

    def test_expected_total_reasonable(self):
        """Expected total should be in reasonable range"""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_enhanced_total(home, away, hg, ag, 6.5)
        self.assertGreater(result["expected_total"], 3.5)
        self.assertLess(result["expected_total"], 9.0)

    def test_b2b_goalie_affects_total(self):
        """B2B goalie start should increase expected goals"""
        home, away, hg, ag = self._make_teams_and_goalies()
        normal = NHLAdvancedAnalytics.calculate_enhanced_total(home, away, hg, ag, 6.5)

        ag_b2b = GoaltenderStats(
            save_percentage=0.905, high_danger_save_pct=0.810,
            medium_danger_save_pct=0.900, low_danger_save_pct=0.975,
            games_saved_above_expected=-2.0, is_back_to_back=True,
        )
        b2b = NHLAdvancedAnalytics.calculate_enhanced_total(home, away, hg, ag_b2b, 6.5)
        # B2B goalie should adjust total
        self.assertNotEqual(normal["expected_total"], b2b["expected_total"])


class TestCompareVsSportsbook(unittest.TestCase):
    """Test true odds vs sportsbook comparison"""

    def test_positive_ev_detection(self):
        """Should detect +EV when model probability exceeds implied"""
        result = NHLAdvancedAnalytics.compare_vs_sportsbook(0.60, 110)
        self.assertTrue(result["is_positive_ev"])
        self.assertGreater(result["ev_per_dollar"], 0)

    def test_negative_ev_detection(self):
        """Should detect -EV when model probability below implied"""
        result = NHLAdvancedAnalytics.compare_vs_sportsbook(0.40, -150)
        self.assertFalse(result["is_positive_ev"])
        self.assertLess(result["ev_per_dollar"], 0)

    def test_strong_bet_signal(self):
        """Large edge should produce strong_bet signal"""
        result = NHLAdvancedAnalytics.compare_vs_sportsbook(0.65, 110)
        self.assertEqual(result["signal"], "strong_bet")

    def test_no_edge_signal(self):
        """When model probability is below sportsbook implied, should be no_edge"""
        result = NHLAdvancedAnalytics.compare_vs_sportsbook(0.45, -110)
        self.assertEqual(result["signal"], "no_edge")

    def test_true_odds_returned(self):
        """Should return valid true odds"""
        result = NHLAdvancedAnalytics.compare_vs_sportsbook(0.55, -110)
        self.assertIsInstance(result["true_odds"], int)
        self.assertIsInstance(result["implied_probability"], float)


class TestPaceTempo(unittest.TestCase):
    """Test pace & tempo calculations"""

    def test_high_tempo(self):
        """Two high-pace teams should classify as high tempo"""
        home = TeamMetrics(
            goals_for=3.5, goals_against=3.0,
            shot_attempts_per_60=72.0, rush_chances_per_60=8.0,
            neutral_zone_transition_pct=58.0,
        )
        away = TeamMetrics(
            goals_for=3.3, goals_against=3.2,
            shot_attempts_per_60=70.0, rush_chances_per_60=7.5,
            neutral_zone_transition_pct=56.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo(home, away)
        self.assertEqual(result["tempo"], "high")
        self.assertEqual(result["lean"], "over")
        self.assertGreater(result["pace_goal_adjustment"], 0)

    def test_low_tempo(self):
        """Two slow defensive teams should classify as low tempo"""
        home = TeamMetrics(
            goals_for=2.2, goals_against=2.0,
            shot_attempts_per_60=48.0, rush_chances_per_60=2.5,
            neutral_zone_transition_pct=40.0,
        )
        away = TeamMetrics(
            goals_for=2.3, goals_against=2.1,
            shot_attempts_per_60=50.0, rush_chances_per_60=3.0,
            neutral_zone_transition_pct=42.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo(home, away)
        self.assertEqual(result["tempo"], "low")
        self.assertEqual(result["lean"], "under")
        self.assertLess(result["pace_goal_adjustment"], 0)

    def test_average_tempo(self):
        """Average teams should be neutral"""
        home = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            shot_attempts_per_60=60.0, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
        )
        away = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            shot_attempts_per_60=60.0, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo(home, away)
        self.assertEqual(result["tempo"], "average")
        self.assertEqual(result["lean"], "neutral")
        self.assertAlmostEqual(result["pace_goal_adjustment"], 0.0, places=2)

    def test_derivative_signal_low_pace(self):
        """Very low pace should signal 1P under / team total under"""
        home = TeamMetrics(
            goals_for=2.0, goals_against=1.8,
            shot_attempts_per_60=45.0, rush_chances_per_60=2.0,
            neutral_zone_transition_pct=38.0,
        )
        away = TeamMetrics(
            goals_for=2.1, goals_against=2.0,
            shot_attempts_per_60=47.0, rush_chances_per_60=2.5,
            neutral_zone_transition_pct=40.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo(home, away)
        self.assertEqual(result["derivative_signal"], "1p_under_team_total_under")


class TestRestTravelModifier(unittest.TestCase):
    """Test rest vs travel modifier"""

    def test_b2b_road_fade(self):
        """B2B on road with backup goalie should be a fade spot"""
        result = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=0, is_road=True, is_back_to_back=True,
            goalie_is_backup=True, travel_zones=2,
        )
        self.assertEqual(result["spot"], "fade")
        self.assertLess(result["modifier"], -0.2)
        self.assertIn("back_to_back", result["flags"])
        self.assertIn("b2b_on_road", result["flags"])
        self.assertIn("goalie_rotation", result["flags"])

    def test_rested_at_home_fire(self):
        """3+ rest days at home should be a bet-on spot"""
        result = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=4, is_road=False, is_back_to_back=False,
        )
        self.assertEqual(result["spot"], "bet_on")
        self.assertGreater(result["modifier"], 0)
        self.assertIn("well_rested", result["flags"])
        self.assertIn("rested_at_home", result["flags"])

    def test_neutral_spot(self):
        """Normal rest, normal travel should be neutral"""
        result = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=1, is_road=False, is_back_to_back=False,
        )
        self.assertEqual(result["spot"], "neutral")

    def test_cross_country_travel(self):
        """3+ timezone travel should add penalty"""
        result = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=1, is_road=True, is_back_to_back=False,
            travel_zones=3,
        )
        self.assertLess(result["modifier"], 0)
        self.assertIn("cross_country_travel", result["flags"])

    def test_rest_differential(self):
        """Large rest differential should affect modifier"""
        rested = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=3, is_road=False, is_back_to_back=False,
            opponent_rest_days=0,
        )
        tired = NHLAdvancedAnalytics.calculate_rest_travel_modifier(
            rest_days=0, is_road=True, is_back_to_back=True,
            opponent_rest_days=3,
        )
        self.assertGreater(rested["modifier"], tired["modifier"])


class TestReverseLineMovement(unittest.TestCase):
    """Test RLM and public splits detection"""

    def test_rlm_detected(self):
        """Public on A but line moves to B = RLM"""
        result = ReverseLineMovement.detect_rlm(
            bet_pct_side_a=70.0,
            money_pct_side_a=45.0,
            opening_odds_a=-110,
            current_odds_a=-105,  # line got cheaper = moved away from A
            opening_odds_b=-110,
            current_odds_b=-115,  # line got more expensive = moved toward B
            total_bets=3000,
            side_a_label="Home",
            side_b_label="Away",
        )
        self.assertTrue(result["rlm_detected"])
        self.assertEqual(result["rlm_side"], "Away")

    def test_no_rlm(self):
        """Public on A and line moves toward A = no RLM"""
        result = ReverseLineMovement.detect_rlm(
            bet_pct_side_a=70.0,
            money_pct_side_a=72.0,
            opening_odds_a=-110,
            current_odds_a=-130,  # got more expensive = line moved toward A
            opening_odds_b=-110,
            current_odds_b=110,
            total_bets=10000,
            side_a_label="Home",
            side_b_label="Away",
        )
        self.assertFalse(result["rlm_detected"])

    def test_sharp_money_detection(self):
        """Big money divergence from bet count = sharp money"""
        result = ReverseLineMovement.detect_rlm(
            bet_pct_side_a=40.0,
            money_pct_side_a=65.0,  # 25% divergence
            opening_odds_a=-110,
            current_odds_a=-110,
            opening_odds_b=-110,
            current_odds_b=-110,
            total_bets=8000,
            side_a_label="Home",
            side_b_label="Away",
        )
        self.assertEqual(result["sharp_side"], "Home")

    def test_low_volume_flag(self):
        """RLM on low volume game = market inefficiency flag"""
        result = ReverseLineMovement.detect_rlm(
            bet_pct_side_a=65.0,
            money_pct_side_a=40.0,
            opening_odds_a=-110,
            current_odds_a=-105,
            opening_odds_b=-110,
            current_odds_b=-115,
            total_bets=2000,
            side_a_label="Over",
            side_b_label="Under",
        )
        self.assertTrue(result["sharp_low_volume_flag"])
        self.assertEqual(result["signal"], "market_inefficiency")

    def test_totals_rlm_under(self):
        """Public on Over but total drops = sharp Under"""
        result = ReverseLineMovement.detect_totals_rlm(
            bet_pct_over=72.0,
            money_pct_over=48.0,
            opening_total=6.5,
            current_total=6.0,
            total_bets=4000,
        )
        self.assertTrue(result["rlm_detected"])
        self.assertEqual(result["rlm_lean"], "under")

    def test_totals_rlm_over(self):
        """Public on Under but total rises = sharp Over"""
        result = ReverseLineMovement.detect_totals_rlm(
            bet_pct_over=30.0,
            money_pct_over=55.0,
            opening_total=5.5,
            current_total=6.0,
            total_bets=6000,
        )
        self.assertTrue(result["rlm_detected"])
        self.assertEqual(result["rlm_lean"], "over")

    def test_totals_no_rlm(self):
        """No significant movement = no RLM"""
        result = ReverseLineMovement.detect_totals_rlm(
            bet_pct_over=55.0,
            money_pct_over=52.0,
            opening_total=6.5,
            current_total=6.5,
            total_bets=10000,
        )
        self.assertFalse(result["rlm_detected"])
        self.assertEqual(result["signal"], "no_signal")


class TestGoalieRegressionEnhanced(unittest.TestCase):
    """Test enhanced goalie regression detection with medium danger"""

    def test_heater_detection(self):
        """Goalie playing well above career should be flagged heater"""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.870,
            low_danger_save_pct=0.990,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            recent_high_danger_save_pct=0.870,
            recent_low_danger_save_pct=0.990,
            is_starter=True,
            starts_last_7=3,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression(goalie)
        self.assertEqual(result["signal"], "heater")

    def test_slump_detection(self):
        """Goalie playing well below career should be flagged slump"""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.780,
            low_danger_save_pct=0.950,
            career_high_danger_save_pct=0.830,
            career_low_danger_save_pct=0.980,
            recent_high_danger_save_pct=0.780,
            recent_low_danger_save_pct=0.950,
            is_starter=True,
            starts_last_7=3,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression(goalie)
        self.assertEqual(result["signal"], "slump")

    def test_b2b_strength_penalty(self):
        """B2B goalie should reduce team strength"""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.830,
            low_danger_save_pct=0.980,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            is_starter=True,
            back_to_back_starts=1,
            starts_last_7=3,
        )
        result = NHLAdvancedAnalytics.adjust_team_strength_for_goalie(50.0, goalie)
        self.assertLess(result["adjusted_strength"], result["base_strength"])
        self.assertLess(result["fatigue_penalty"], 0)


class TestGoalieRegressionV2(unittest.TestCase):
    """Test goalie regression detection v2 with shrinkage and goals impact."""

    def test_heater_produces_positive_xga(self):
        """Goalie on a heater should produce positive goalie_effect_xGA (more goals expected)."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.870,
            low_danger_save_pct=0.990,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            season_high_danger_save_pct=0.840,
            season_low_danger_save_pct=0.980,
            recent_high_danger_save_pct=0.870,
            recent_low_danger_save_pct=0.990,
            is_starter=True,
            starts_last_7=2,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertGreater(result["goalie_effect_xGA"], 0)
        self.assertEqual(result["signal"], "heater_regression_expected")
        self.assertIn("regress_score", result)
        self.assertIn("goalie_variance", result)

    def test_slump_produces_negative_xga(self):
        """Goalie in a slump should produce negative goalie_effect_xGA (fewer goals expected)."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.780,
            low_danger_save_pct=0.955,
            career_high_danger_save_pct=0.830,
            career_low_danger_save_pct=0.980,
            season_high_danger_save_pct=0.820,
            season_low_danger_save_pct=0.978,
            recent_high_danger_save_pct=0.780,
            recent_low_danger_save_pct=0.955,
            is_starter=True,
            starts_last_7=2,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertLess(result["goalie_effect_xGA"], 0)
        self.assertEqual(result["signal"], "slump_rebound_expected")

    def test_stable_goalie_near_zero(self):
        """Goalie near career norms should produce near-zero effect."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.825,
            low_danger_save_pct=0.978,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            season_high_danger_save_pct=0.822,
            season_low_danger_save_pct=0.976,
            recent_high_danger_save_pct=0.825,
            recent_low_danger_save_pct=0.978,
            is_starter=True,
            starts_last_7=2,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertAlmostEqual(result["goalie_effect_xGA"], 0.0, delta=0.1)
        self.assertEqual(result["signal"], "stable")

    def test_b2b_pulls_score_toward_zero(self):
        """B2B start should reduce regress_score magnitude and increase variance."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.870,
            low_danger_save_pct=0.990,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            recent_high_danger_save_pct=0.870,
            recent_low_danger_save_pct=0.990,
            is_starter=True,
            is_back_to_back=True,
            starts_last_7=2,
        )
        result_b2b = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertTrue(result_b2b["fatigue_penalty_applied"])

        goalie_normal = GoaltenderStats(
            high_danger_save_pct=0.870,
            low_danger_save_pct=0.990,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.975,
            recent_high_danger_save_pct=0.870,
            recent_low_danger_save_pct=0.990,
            is_starter=True,
            is_back_to_back=False,
            starts_last_7=2,
        )
        result_normal = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie_normal)

        # B2B should have smaller absolute regress_score
        self.assertLess(
            abs(result_b2b["regress_score"]),
            abs(result_normal["regress_score"]),
        )
        # B2B should have higher variance
        self.assertGreater(result_b2b["goalie_variance"], result_normal["goalie_variance"])

    def test_heavy_workload_triggers_penalty(self):
        """starts_last_7 >= 3 should trigger fatigue penalty."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.850,
            career_high_danger_save_pct=0.820,
            is_starter=True,
            starts_last_7=4,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertTrue(result["fatigue_penalty_applied"])

    def test_regress_score_clamped(self):
        """regress_score should be clamped to [-1, +1]."""
        # Extreme heater
        goalie = GoaltenderStats(
            high_danger_save_pct=0.950,
            low_danger_save_pct=0.999,
            career_high_danger_save_pct=0.800,
            career_low_danger_save_pct=0.960,
            recent_high_danger_save_pct=0.950,
            recent_low_danger_save_pct=0.999,
            is_starter=True,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertLessEqual(result["regress_score"], 1.0)
        self.assertGreaterEqual(result["regress_score"], -1.0)

    def test_non_starter_high_variance(self):
        """Non-starter should have elevated variance."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.820,
            career_high_danger_save_pct=0.820,
            is_starter=False,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        self.assertGreater(result["goalie_variance"], 0.4)

    def test_shrinkage_blends_all_three(self):
        """adj_hds should blend last10, season, and career values."""
        goalie = GoaltenderStats(
            high_danger_save_pct=0.820,
            career_high_danger_save_pct=0.800,
            season_high_danger_save_pct=0.810,
            recent_high_danger_save_pct=0.850,
            is_starter=True,
        )
        result = NHLAdvancedAnalytics.detect_goalie_regression_v2(goalie)
        expected_adj_hds = 0.50 * 0.850 + 0.30 * 0.810 + 0.20 * 0.800
        self.assertAlmostEqual(result["adj_hds"], expected_adj_hds, places=4)


class TestPaceTempoV2(unittest.TestCase):
    """Test pace & tempo 2.0 with z-score based tempo index."""

    def test_high_tempo_classification(self):
        """Two fast teams should produce high tempo label."""
        home = TeamMetrics(
            goals_for=3.5, goals_against=3.0,
            xg_for_per_60=3.2, rush_chances_per_60=7.5,
            neutral_zone_transition_pct=58.0,
            pp_opportunities_per_game=3.8,
        )
        away = TeamMetrics(
            goals_for=3.3, goals_against=3.2,
            xg_for_per_60=3.0, rush_chances_per_60=7.0,
            neutral_zone_transition_pct=56.0,
            pp_opportunities_per_game=3.5,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        self.assertEqual(result["tempo_label"], "high")
        self.assertGreater(result["tempo_delta"], 0)
        self.assertIn("z_scores", result)

    def test_low_tempo_classification(self):
        """Two slow defensive teams should produce low tempo label."""
        home = TeamMetrics(
            goals_for=2.2, goals_against=2.0,
            xg_for_per_60=1.8, rush_chances_per_60=3.0,
            neutral_zone_transition_pct=42.0,
            pp_opportunities_per_game=2.2,
        )
        away = TeamMetrics(
            goals_for=2.1, goals_against=2.1,
            xg_for_per_60=1.9, rush_chances_per_60=3.2,
            neutral_zone_transition_pct=43.0,
            pp_opportunities_per_game=2.3,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        self.assertEqual(result["tempo_label"], "low")
        self.assertLess(result["tempo_delta"], 0)

    def test_neutral_tempo(self):
        """Average teams should produce neutral tempo."""
        home = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            xg_for_per_60=2.5, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
            pp_opportunities_per_game=3.0,
        )
        away = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            xg_for_per_60=2.5, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
            pp_opportunities_per_game=3.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        self.assertEqual(result["tempo_label"], "neutral")
        self.assertAlmostEqual(result["tempo_delta"], 0.0, delta=0.01)

    def test_mismatch_detection(self):
        """High offense vs weak defense should flag mismatch."""
        home = TeamMetrics(
            goals_for=3.8, goals_against=2.5,
            xg_for_per_60=3.5, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
            pp_opportunities_per_game=3.0,
        )
        away = TeamMetrics(
            goals_for=2.5, goals_against=3.8,  # weak defense
            xg_for_per_60=2.0, rush_chances_per_60=5.0,
            neutral_zone_transition_pct=50.0,
            pp_opportunities_per_game=3.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        self.assertGreater(result["mismatch_score"], 0)
        self.assertTrue(len(result["mismatch_tags"]) > 0)

    def test_z_scores_returned(self):
        """Should return all four z-score components."""
        home = TeamMetrics(goals_for=3.0, goals_against=3.0)
        away = TeamMetrics(goals_for=3.0, goals_against=3.0)
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        self.assertIn("xg60", result["z_scores"])
        self.assertIn("rush", result["z_scores"])
        self.assertIn("nz_speed", result["z_scores"])
        self.assertIn("pp_opp", result["z_scores"])

    def test_xg_for_fallback(self):
        """Should fall back to xg_for when xg_for_per_60 is 0."""
        home = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            xg_for=3.0, xg_for_per_60=0.0,
        )
        away = TeamMetrics(
            goals_for=3.0, goals_against=3.0,
            xg_for=2.8, xg_for_per_60=0.0,
        )
        result = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home, away)
        # Should use xg_for values as fallback
        self.assertAlmostEqual(result["raw_averages"]["avg_xg60"], 2.9, places=1)


class TestFatigueSeverity(unittest.TestCase):
    """Test fatigue severity score (rest vs travel 2.0)."""

    def test_b2b_away_unconfirmed_avoid(self):
        """B2B on road with unconfirmed goalie should flag as avoid spot."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=True, is_road=True, goalie_confirmed=False,
            travel_km=500, time_zones_crossed=1,
        )
        self.assertTrue(result["is_avoid_spot"])
        self.assertIn("away_b2b_unconfirmed_goalie_avoid", result["tags"])
        self.assertIn("away_b2b_fade_spot", result["tags"])

    def test_well_rested_home_boost(self):
        """3+ rest days at home should produce rest boost."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=False, home_rest_days=4, is_road=False,
        )
        self.assertGreater(result["rest_boost"], 0)
        self.assertIn("well_rested_at_home", result["tags"])
        self.assertGreater(result["fatigue_effect_team"], 0)

    def test_fatigue_formula(self):
        """Fatigue score should follow the specified formula."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=True, travel_km=1500, time_zones_crossed=3,
        )
        # fatigue = 0.50*1 + 0.25*min(1500/1000,1) + 0.25*min(3/2,1)
        # fatigue = 0.50 + 0.25*1.0 + 0.25*1.0 = 1.0
        self.assertAlmostEqual(result["fatigue_score"], 1.0, places=2)

    def test_3_in_4_penalty(self):
        """3 games in 4 nights should add heavy schedule penalty."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=False, games_4_nights=3,
        )
        self.assertIn("3_in_4_heavy_schedule", result["tags"])
        self.assertGreater(result["fatigue_score"], 0.2)

    def test_no_fatigue_neutral(self):
        """Normal rest, no travel should produce minimal fatigue."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=False, travel_km=0, time_zones_crossed=0,
            home_rest_days=1, is_road=False,
        )
        self.assertAlmostEqual(result["fatigue_score"], 0.0, places=2)
        self.assertFalse(result["is_avoid_spot"])
        self.assertEqual(len(result["tags"]), 0)

    def test_long_travel_tagged(self):
        """Travel > 2000km should be tagged."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=False, travel_km=2500, is_road=True,
        )
        self.assertIn("long_travel", result["tags"])

    def test_timezone_change_tagged(self):
        """2+ timezone changes should be tagged."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=False, time_zones_crossed=2, is_road=True,
        )
        self.assertIn("significant_timezone_change", result["tags"])

    def test_fatigue_effect_total_positive_when_tired(self):
        """Tired team should push total slightly over (defensive breakdowns)."""
        result = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=True, travel_km=1000, is_road=True,
        )
        self.assertGreater(result["fatigue_effect_total"], 0)


class TestSharpMovement(unittest.TestCase):
    """Test RLM & Public Splits 2.0 sharp movement detection."""

    def test_full_sharpness_score(self):
        """All three sharp indicators should produce score of 3."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": -1}, {"direction": -1}],
            is_pinnacle_moved_first=True,
            move_sustained=True,
            low_volume_significant_move=True,
        )
        self.assertEqual(result["sharp_move_score"], 3)

    def test_steam_flag_detection(self):
        """Multiple books moving same direction should flag steam."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": 1}, {"direction": 1}, {"direction": 1}],
        )
        self.assertTrue(result["steam_flag"])

    def test_no_steam_mixed_directions(self):
        """Mixed directions should not flag steam."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": 1}, {"direction": -1}],
        )
        self.assertFalse(result["steam_flag"])

    def test_rlm_direction_over(self):
        """Positive average direction should indicate over."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": 0.5}, {"direction": 1.0}],
        )
        self.assertEqual(result["rlm_direction"], "over")

    def test_rlm_direction_under(self):
        """Negative average direction should indicate under."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": -0.5}, {"direction": -1.0}],
        )
        self.assertEqual(result["rlm_direction"], "under")

    def test_empty_moves_no_signal(self):
        """No line moves should produce neutral output."""
        result = ReverseLineMovement.detect_sharp_movement()
        self.assertFalse(result["steam_flag"])
        self.assertEqual(result["sharp_move_score"], 0)
        self.assertEqual(result["rlm_direction"], "none")
        self.assertAlmostEqual(result["market_delta"], 0.0)

    def test_market_delta_with_steam_over(self):
        """Steam move toward over should produce positive market_delta."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": 1}, {"direction": 1}],
            is_pinnacle_moved_first=True,
            move_sustained=True,
        )
        self.assertGreater(result["market_delta"], 0)

    def test_market_delta_with_steam_under(self):
        """Steam move toward under should produce negative market_delta."""
        result = ReverseLineMovement.detect_sharp_movement(
            line_moves=[{"direction": -1}, {"direction": -1}],
            is_pinnacle_moved_first=True,
        )
        self.assertLess(result["market_delta"], 0)


class TestCompositeEdge(unittest.TestCase):
    """Test Composite Edge 2.0 (projected total pipeline)."""

    def _make_teams_and_goalies(self):
        home = TeamMetrics(
            goals_for=3.2, goals_against=2.5, xg_for=3.1, xg_against=2.4,
            corsi_pct=54.0, pp_pct=24.0, pk_pct=82.0,
            xg_for_per_60=3.0, rush_chances_per_60=5.5,
            neutral_zone_transition_pct=52.0, pp_opportunities_per_game=3.2,
        )
        away = TeamMetrics(
            goals_for=2.8, goals_against=3.0, xg_for=2.7, xg_against=2.9,
            corsi_pct=48.0, pp_pct=18.0, pk_pct=78.0,
            xg_for_per_60=2.5, rush_chances_per_60=4.8,
            neutral_zone_transition_pct=48.0, pp_opportunities_per_game=2.8,
        )
        home_g = GoaltenderStats(
            save_percentage=0.920, high_danger_save_pct=0.850,
            medium_danger_save_pct=0.930, low_danger_save_pct=0.990,
            career_high_danger_save_pct=0.830,
            career_low_danger_save_pct=0.980,
            is_starter=True, starts_last_7=2,
        )
        away_g = GoaltenderStats(
            save_percentage=0.905, high_danger_save_pct=0.810,
            medium_danger_save_pct=0.900, low_danger_save_pct=0.975,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.978,
            is_starter=True, starts_last_7=2,
        )
        return home, away, home_g, away_g

    def test_returns_all_required_fields(self):
        """Should return all spec'd output fields."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertIn("projected_total", result)
        self.assertIn("line_total", result)
        self.assertIn("edge_points", result)
        self.assertIn("prob_over", result)
        self.assertIn("confidence", result)
        self.assertIn("tags", result)
        self.assertIn("recommendation", result)
        self.assertIn("derivatives", result)
        self.assertIn("components", result)

    def test_projected_total_reasonable(self):
        """Projected total should be in 3.5-9.0 range."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertGreaterEqual(result["projected_total"], 3.5)
        self.assertLessEqual(result["projected_total"], 9.0)

    def test_prob_over_between_0_and_1(self):
        """prob_over should be a valid probability."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertGreaterEqual(result["prob_over"], 0.0)
        self.assertLessEqual(result["prob_over"], 1.0)

    def test_over_recommendation_when_projected_high(self):
        """When projected total > line total, should lean Over."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=5.0,
            model_total_mean=7.0,
        )
        self.assertGreater(result["prob_over"], 0.5)

    def test_under_recommendation_when_projected_low(self):
        """When projected total < line total, should lean Under."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=8.0,
            model_total_mean=5.5,
        )
        self.assertLess(result["prob_over"], 0.5)

    def test_edge_points_calculation(self):
        """edge_points should equal projected_total - line_total."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertAlmostEqual(
            result["edge_points"],
            result["projected_total"] - result["line_total"],
            places=4,
        )

    def test_fatigue_affects_total(self):
        """Fatigue input should shift projected total."""
        home, away, hg, ag = self._make_teams_and_goalies()
        no_fatigue = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        fatigue = NHLAdvancedAnalytics.calculate_fatigue_severity(
            is_b2b=True, travel_km=1500, is_road=True,
        )
        with_fatigue = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
            away_fatigue=fatigue,
        )
        # Fatigue pushes total slightly up (defensive breakdowns)
        self.assertNotEqual(
            no_fatigue["projected_total"], with_fatigue["projected_total"]
        )

    def test_market_data_affects_total(self):
        """Market data should shift projected total."""
        home, away, hg, ag = self._make_teams_and_goalies()
        no_market = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        market = {"market_delta": 0.3, "steam_flag": True}
        with_market = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
            market_data=market,
        )
        self.assertGreater(
            with_market["projected_total"], no_market["projected_total"]
        )

    def test_non_starter_reduces_confidence(self):
        """Non-starter goalie should reduce confidence."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result_confirmed = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        ag_unconfirmed = GoaltenderStats(
            save_percentage=0.905, high_danger_save_pct=0.810,
            career_high_danger_save_pct=0.820,
            career_low_danger_save_pct=0.978,
            is_starter=False,
        )
        result_unconfirmed = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag_unconfirmed, line_total=6.5,
        )
        self.assertLess(
            result_unconfirmed["confidence"], result_confirmed["confidence"]
        )

    def test_components_sum_to_projection(self):
        """Components should add up to projected total (before clamping)."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5, model_total_mean=6.2,
        )
        c = result["components"]
        raw_total = c["baseline"] + c["goalie_delta"] + c["tempo_delta"] + c["fatigue_delta"] + c["market_delta"]
        # Projected total is clamped, so raw should be close if not at boundary
        if 3.5 < raw_total < 9.0:
            self.assertAlmostEqual(result["projected_total"], raw_total, places=4)

    def test_tags_populated(self):
        """Tags should be a list of strings."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertIsInstance(result["tags"], list)

    def test_goalie_detail_included(self):
        """Should include detailed goalie regression info for both goalies."""
        home, away, hg, ag = self._make_teams_and_goalies()
        result = NHLAdvancedAnalytics.calculate_composite_edge(
            home, away, hg, ag, line_total=6.5,
        )
        self.assertIn("home", result["goalie_detail"])
        self.assertIn("away", result["goalie_detail"])
        self.assertIn("goalie_effect_xGA", result["goalie_detail"]["home"])
        self.assertIn("goalie_effect_xGA", result["goalie_detail"]["away"])


if __name__ == '__main__':
    unittest.main()
