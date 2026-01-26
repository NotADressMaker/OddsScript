#!/usr/bin/env python3
"""
Test suite for College Football (CFB) analytics library
"""

import unittest
import sys
import os

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from cfb_analytics import CFBAnalytics, Conference, calculate_cfb_sp_plus_probability


class TestCFBSpreadProbability(unittest.TestCase):
    """Test CFB spread probability calculations"""

    def test_basic_spread_calculation(self):
        result = CFBAnalytics.calculate_spread_probability(
            team_rating=35.0,
            opponent_rating=28.0,
            spread=-7.0,
            is_home=True
        )

        self.assertIn('cover_probability', result)
        self.assertIn('expected_margin', result)
        self.assertGreater(result['cover_probability'], 0.0)
        self.assertLess(result['cover_probability'], 1.0)

    def test_home_advantage_impact(self):
        # Home team should have better cover probability
        home_result = CFBAnalytics.calculate_spread_probability(
            team_rating=30.0,
            opponent_rating=30.0,
            spread=-3.0,
            is_home=True
        )

        away_result = CFBAnalytics.calculate_spread_probability(
            team_rating=30.0,
            opponent_rating=30.0,
            spread=-3.0,
            is_home=False
        )

        self.assertGreater(home_result['cover_probability'],
                          away_result['cover_probability'])

    def test_conference_adjustment(self):
        # SEC team vs FCS team should have bigger expected margin
        result = CFBAnalytics.calculate_spread_probability(
            team_rating=35.0,
            opponent_rating=20.0,
            spread=-40.0,
            is_home=True,
            team_conference=Conference.SEC,
            opponent_conference=Conference.FCS
        )

        self.assertGreater(result['conference_adjustment'], 0)
        self.assertGreater(result['expected_margin'], 15)

    def test_rivalry_game_adjustment(self):
        # Rivalry game should reduce home advantage
        normal = CFBAnalytics.calculate_spread_probability(
            team_rating=32.0,
            opponent_rating=28.0,
            spread=-4.0,
            is_home=True,
            rivalry_game=False
        )

        rivalry = CFBAnalytics.calculate_spread_probability(
            team_rating=32.0,
            opponent_rating=28.0,
            spread=-4.0,
            is_home=True,
            rivalry_game=True
        )

        # Rivalry should have lower home advantage
        self.assertLess(rivalry['home_advantage_used'],
                       normal['home_advantage_used'])

    def test_key_number_detection(self):
        result = CFBAnalytics.calculate_spread_probability(
            team_rating=30.0,
            opponent_rating=23.0,
            spread=-7.0,
            is_home=True
        )

        self.assertTrue(result['is_key_number'])


class TestCFBTotalProbability(unittest.TestCase):
    """Test CFB total probability calculations"""

    def test_basic_total_calculation(self):
        result = CFBAnalytics.calculate_total_probability(
            team1_avg=32.0,
            team2_avg=28.0,
            total_line=58.5
        )

        self.assertIn('over_probability', result)
        self.assertIn('under_probability', result)
        self.assertAlmostEqual(
            result['over_probability'] + result['under_probability'],
            1.0,
            places=5
        )

    def test_conference_game_adjustment(self):
        # Conference games should have lower expected totals
        non_conf = CFBAnalytics.calculate_total_probability(
            team1_avg=35.0,
            team2_avg=32.0,
            total_line=65.0,
            is_conference_game=False
        )

        conf = CFBAnalytics.calculate_total_probability(
            team1_avg=35.0,
            team2_avg=32.0,
            total_line=65.0,
            is_conference_game=True
        )

        self.assertLess(conf['expected_total'], non_conf['expected_total'])

    def test_weather_impact(self):
        # Weather should reduce expected total
        no_weather = CFBAnalytics.calculate_total_probability(
            team1_avg=30.0,
            team2_avg=28.0,
            total_line=56.0,
            weather_impact=None
        )

        heavy_wind = CFBAnalytics.calculate_total_probability(
            team1_avg=30.0,
            team2_avg=28.0,
            total_line=56.0,
            weather_impact="heavy_wind"
        )

        self.assertLess(heavy_wind['expected_total'],
                       no_weather['expected_total'])


class TestCFBRivalryAnalysis(unittest.TestCase):
    """Test rivalry game analysis"""

    def test_rivalry_compression(self):
        result = CFBAnalytics.analyze_rivalry_game(
            team1_rating=35.0,
            team2_rating=25.0,
            spread=-10.0
        )

        self.assertIn('rivalry_adjusted_margin', result)
        self.assertIn('compression_factor', result)

        # Rivalry should compress expected margin
        self.assertLess(
            abs(result['rivalry_adjusted_margin']),
            abs(result['normal_expected_margin'])
        )

    def test_historical_momentum(self):
        # Team dominating historically should get slight boost
        dominant = CFBAnalytics.analyze_rivalry_game(
            team1_rating=32.0,
            team2_rating=28.0,
            spread=-5.0,
            historical_record={'team1_wins': 15, 'team2_wins': 5}
        )

        self.assertGreater(dominant['momentum_adjustment'], 0)


class TestCFBChampionshipGame(unittest.TestCase):
    """Test conference championship game analysis"""

    def test_neutral_site(self):
        result = CFBAnalytics.calculate_conference_championship_probability(
            team_rating=35.0,
            opponent_rating=32.0,
            spread=-3.0,
            neutral_site=True
        )

        self.assertTrue(result['neutral_site'])
        self.assertEqual(result['variance'], 'lower')

    def test_lower_variance(self):
        # Championship games should have lower variance
        result = CFBAnalytics.calculate_conference_championship_probability(
            team_rating=35.0,
            opponent_rating=32.0,
            spread=-3.0
        )

        self.assertIn('variance', result)
        self.assertEqual(result['variance'], 'lower')


class TestCFBSimulation(unittest.TestCase):
    """Test game and season simulations"""

    def test_simulate_game(self):
        result = CFBAnalytics.simulate_game(
            home_rating=30.0,
            away_rating=28.0,
            seed=42
        )

        self.assertIn('home_score', result)
        self.assertIn('away_score', result)
        self.assertIn('result', result)
        self.assertGreaterEqual(result['home_score'], 0)
        self.assertGreaterEqual(result['away_score'], 0)

    def test_simulate_game_deterministic(self):
        # Same seed should produce same result
        result1 = CFBAnalytics.simulate_game(
            home_rating=30.0,
            away_rating=28.0,
            seed=42
        )

        result2 = CFBAnalytics.simulate_game(
            home_rating=30.0,
            away_rating=28.0,
            seed=42
        )

        self.assertEqual(result1['home_score'], result2['home_score'])
        self.assertEqual(result1['away_score'], result2['away_score'])

    def test_simulate_season(self):
        teams = {
            'Team A': 35.0,
            'Team B': 32.0,
            'Team C': 28.0,
            'Team D': 25.0
        }

        result = CFBAnalytics.simulate_season(
            teams,
            games_per_team=12,
            seed=42
        )

        self.assertIn('standings', result)
        self.assertIn('matches', result)
        self.assertEqual(len(result['standings']), 4)


class TestCFBKeyNumbers(unittest.TestCase):
    """Test key number analysis"""

    def test_key_number_3(self):
        result = CFBAnalytics.analyze_key_numbers(-3.0)

        self.assertTrue(result['is_key_number'])
        self.assertGreater(result['frequency'], 0)

    def test_key_number_7(self):
        result = CFBAnalytics.analyze_key_numbers(-7.0)

        self.assertTrue(result['is_key_number'])
        self.assertGreater(result['frequency'], 0)

    def test_non_key_number(self):
        result = CFBAnalytics.analyze_key_numbers(-8.5)

        self.assertFalse(result['is_key_number'])
        self.assertEqual(result['frequency'], 0.0)

    def test_key_number_advice(self):
        result = CFBAnalytics.analyze_key_numbers(-3.0)

        self.assertIn('advice', result)
        self.assertIsInstance(result['advice'], str)


class TestCFBPlayoffProbability(unittest.TestCase):
    """Test College Football Playoff probability calculations"""

    def test_undefeated_team(self):
        result = CFBAnalytics.calculate_playoff_probability(
            team_rating=38.0,
            current_record=(10, 0),
            games_remaining=2,
            conference_rank=1,
            strength_of_schedule=75.0
        )

        # Undefeated team should have high playoff probability
        self.assertGreater(result['playoff_probability'], 0.5)

    def test_two_loss_team(self):
        result = CFBAnalytics.calculate_playoff_probability(
            team_rating=32.0,
            current_record=(9, 2),
            games_remaining=1,
            conference_rank=3,
            strength_of_schedule=65.0
        )

        # Two losses significantly hurts playoff chances
        self.assertLess(result['playoff_probability'], 0.3)

    def test_factors_breakdown(self):
        result = CFBAnalytics.calculate_playoff_probability(
            team_rating=35.0,
            current_record=(10, 1),
            games_remaining=1,
            conference_rank=2,
            strength_of_schedule=70.0
        )

        self.assertIn('factors', result)
        self.assertIn('base', result['factors'])
        self.assertIn('conference_rank_adj', result['factors'])


class TestCFBFirstHalf(unittest.TestCase):
    """Test first half betting analysis"""

    def test_first_half_calculation(self):
        result = CFBAnalytics.calculate_first_half_probability(
            team_rating=32.0,
            opponent_rating=28.0,
            first_half_spread=-3.0,
            is_home=True
        )

        self.assertIn('cover_probability', result)
        self.assertIn('expected_margin', result)

    def test_first_half_closer_than_full_game(self):
        # First half margin should be less than full game
        full_game = CFBAnalytics.calculate_spread_probability(
            team_rating=35.0,
            opponent_rating=25.0,
            spread=-10.0,
            is_home=True
        )

        first_half = CFBAnalytics.calculate_first_half_probability(
            team_rating=35.0,
            opponent_rating=25.0,
            first_half_spread=-5.0,
            is_home=True
        )

        # First half expected margin should be roughly 45% of full game
        expected_first_half_margin = full_game['expected_margin'] * 0.45
        self.assertAlmostEqual(
            first_half['expected_margin'],
            expected_first_half_margin,
            delta=1.0
        )


class TestSPPlusProbability(unittest.TestCase):
    """Test SP+ probability calculations"""

    def test_sp_plus_probability(self):
        prob = calculate_cfb_sp_plus_probability(
            sp_plus_1=25.0,
            sp_plus_2=20.0,
            home_advantage=3.5
        )

        self.assertGreater(prob, 0.5)  # Team 1 should be favored
        self.assertLess(prob, 1.0)

    def test_even_matchup(self):
        prob = calculate_cfb_sp_plus_probability(
            sp_plus_1=20.0,
            sp_plus_2=16.5,  # Exactly home advantage
            home_advantage=3.5
        )

        # Should be roughly 50/50
        self.assertAlmostEqual(prob, 0.5, delta=0.1)


class TestConferenceRatings(unittest.TestCase):
    """Test conference strength ratings"""

    def test_sec_highest_rated(self):
        sec_rating = CFBAnalytics.CONFERENCE_RATINGS[Conference.SEC]
        self.assertGreater(sec_rating, 0)

    def test_fcs_lowest_rated(self):
        fcs_rating = CFBAnalytics.CONFERENCE_RATINGS[Conference.FCS]
        self.assertLess(fcs_rating, 0)

    def test_power_5_conferences(self):
        # Power 5 conferences should all be positive
        power_5 = [Conference.SEC, Conference.BIG_TEN, Conference.BIG_12,
                   Conference.ACC, Conference.PAC_12]

        for conf in power_5:
            rating = CFBAnalytics.CONFERENCE_RATINGS[conf]
            self.assertGreaterEqual(rating, 0)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
