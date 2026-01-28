#!/usr/bin/env python3
"""
Test suite for College Basketball (CBB) analytics library
"""

import unittest
import sys
import os

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from cbb_analytics import CBBAnalytics, CBBConference, calculate_cbb_kenpom_probability


class TestCBBSpreadProbability(unittest.TestCase):
    """Test CBB spread probability calculations"""

    def test_basic_spread_calculation(self):
        result = CBBAnalytics.calculate_spread_probability(
            team_rating=78.0,
            opponent_rating=70.0,
            spread=-6.5,
            is_home=True
        )

        self.assertIn('cover_probability', result)
        self.assertIn('expected_margin', result)
        self.assertGreater(result['cover_probability'], 0.0)
        self.assertLess(result['cover_probability'], 1.0)

    def test_home_advantage_impact(self):
        # Home team should have better cover probability
        home_result = CBBAnalytics.calculate_spread_probability(
            team_rating=75.0,
            opponent_rating=75.0,
            spread=-4.0,
            is_home=True
        )

        away_result = CBBAnalytics.calculate_spread_probability(
            team_rating=75.0,
            opponent_rating=75.0,
            spread=-4.0,
            is_home=False
        )

        self.assertGreater(home_result['cover_probability'],
                          away_result['cover_probability'])

    def test_conference_adjustment(self):
        # Big East vs mid-major should have adjustment
        result = CBBAnalytics.calculate_spread_probability(
            team_rating=80.0,
            opponent_rating=70.0,
            spread=-12.0,
            is_home=True,
            team_conference=CBBConference.BIG_EAST,
            opponent_conference=CBBConference.MAC
        )

        self.assertGreater(result['conference_adjustment'], 0)

    def test_conference_game_no_adjustment(self):
        # Conference games shouldn't have conference adjustment
        result = CBBAnalytics.calculate_spread_probability(
            team_rating=78.0,
            opponent_rating=72.0,
            spread=-6.0,
            is_home=True,
            team_conference=CBBConference.BIG_TEN,
            opponent_conference=CBBConference.BIG_TEN,
            is_conference_game=True
        )

        self.assertEqual(result['conference_adjustment'], 0.0)

    def test_neutral_site_removes_home_advantage(self):
        result = CBBAnalytics.calculate_spread_probability(
            team_rating=78.0,
            opponent_rating=72.0,
            spread=-6.0,
            is_home=True,
            neutral_site=True
        )

        self.assertEqual(result['home_advantage_used'], 0.0)

    def test_home_advantage_is_capped(self):
        result = CBBAnalytics.calculate_spread_probability(
            team_rating=78.0,
            opponent_rating=72.0,
            spread=-6.0,
            is_home=True,
            home_advantage=20.0
        )

        self.assertEqual(result['home_advantage_used'], CBBAnalytics.MAX_HOME_ADVANTAGE)


class TestCBBTotalProbability(unittest.TestCase):
    """Test CBB total probability calculations"""

    def test_basic_total_calculation(self):
        result = CBBAnalytics.calculate_total_probability(
            team1_avg=75.0,
            team2_avg=70.0,
            total_line=145.0
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
        non_conf = CBBAnalytics.calculate_total_probability(
            team1_avg=78.0,
            team2_avg=74.0,
            total_line=150.0,
            is_conference_game=False
        )

        conf = CBBAnalytics.calculate_total_probability(
            team1_avg=78.0,
            team2_avg=74.0,
            total_line=150.0,
            is_conference_game=True
        )

        self.assertLess(conf['expected_total'], non_conf['expected_total'])


class TestCBBPaceAdjusted(unittest.TestCase):
    """Test pace-adjusted calculations"""

    def test_pace_adjusted_total(self):
        result = CBBAnalytics.calculate_pace_adjusted_total(
            team1_pace=72.0,
            team2_pace=68.0,
            team1_off_rating=108.0,
            team2_off_rating=105.0,
            team1_def_rating=98.0,
            team2_def_rating=100.0
        )

        self.assertIn('team1_expected', result)
        self.assertIn('team2_expected', result)
        self.assertIn('total_expected', result)
        self.assertIn('game_pace', result)

        # Total should be sum of team expectations
        self.assertAlmostEqual(
            result['total_expected'],
            result['team1_expected'] + result['team2_expected'],
            places=2
        )

    def test_pace_impact(self):
        # Faster pace should lead to higher scoring
        fast = CBBAnalytics.calculate_pace_adjusted_total(
            team1_pace=75.0,
            team2_pace=75.0,
            team1_off_rating=105.0,
            team2_off_rating=105.0,
            team1_def_rating=100.0,
            team2_def_rating=100.0
        )

        slow = CBBAnalytics.calculate_pace_adjusted_total(
            team1_pace=65.0,
            team2_pace=65.0,
            team1_off_rating=105.0,
            team2_off_rating=105.0,
            team1_def_rating=100.0,
            team2_def_rating=100.0
        )

        self.assertGreater(fast['total_expected'], slow['total_expected'])


class TestCBBMarchMadness(unittest.TestCase):
    """Test March Madness-specific calculations"""

    def test_classic_upset_5_vs_12(self):
        result = CBBAnalytics.calculate_march_madness_upset_probability(
            higher_seed=5,
            lower_seed=12,
            rating_diff=10.0
        )

        # 5 vs 12 is one of the most common upsets
        self.assertGreater(result['adjusted_upset_probability'], 0.3)
        self.assertEqual(result['seed_difference'], 7)

    def test_rare_upset_1_vs_16(self):
        result = CBBAnalytics.calculate_march_madness_upset_probability(
            higher_seed=1,
            lower_seed=16,
            rating_diff=25.0
        )

        # 1 vs 16 upset is extremely rare
        self.assertLess(result['adjusted_upset_probability'], 0.05)
        self.assertEqual(result['seed_difference'], 15)

    def test_rating_adjustment(self):
        # Close rating difference should increase upset probability
        close_rating = CBBAnalytics.calculate_march_madness_upset_probability(
            higher_seed=4,
            lower_seed=13,
            rating_diff=5.0  # Close game
        )

        wide_rating = CBBAnalytics.calculate_march_madness_upset_probability(
            higher_seed=4,
            lower_seed=13,
            rating_diff=18.0  # Blowout expected
        )

        self.assertGreater(
            close_rating['adjusted_upset_probability'],
            wide_rating['adjusted_upset_probability']
        )

    def test_8_vs_9_even(self):
        result = CBBAnalytics.calculate_march_madness_upset_probability(
            higher_seed=8,
            lower_seed=9,
            rating_diff=1.0
        )

        # 8 vs 9 should be close to 50/50
        self.assertAlmostEqual(result['adjusted_upset_probability'], 0.5, delta=0.1)


class TestCBBTournamentProbability(unittest.TestCase):
    """Test tournament advancement probabilities"""

    def test_1_seed_probabilities(self):
        result = CBBAnalytics.calculate_tournament_probability(
            team_seed=1,
            team_rating=30.0,
            bracket_region="East"
        )

        # 1 seed should have high probability in early rounds
        self.assertGreater(result['round_of_32'], 0.95)
        self.assertGreater(result['sweet_16'], 0.75)
        self.assertGreater(result['elite_8'], 0.45)

    def test_16_seed_probabilities(self):
        result = CBBAnalytics.calculate_tournament_probability(
            team_seed=16,
            team_rating=5.0,
            bracket_region="West"
        )

        # 16 seed should have very low probabilities
        self.assertLess(result['round_of_32'], 0.05)
        self.assertLess(result['sweet_16'], 0.01)
        self.assertEqual(result['elite_8'], 0.0)

    def test_5_seed_typical(self):
        result = CBBAnalytics.calculate_tournament_probability(
            team_seed=5,
            team_rating=20.0,
            bracket_region="Midwest"
        )

        # 5 seed should have moderate probabilities
        self.assertGreater(result['round_of_32'], 0.60)
        self.assertGreater(result['sweet_16'], 0.20)
        self.assertLess(result['final_4'], 0.10)

    def test_rating_impact(self):
        # Higher rating should improve probabilities
        strong_5 = CBBAnalytics.calculate_tournament_probability(
            team_seed=5,
            team_rating=25.0,  # Strong
            bracket_region="East"
        )

        weak_5 = CBBAnalytics.calculate_tournament_probability(
            team_seed=5,
            team_rating=15.0,  # Weak
            bracket_region="East"
        )

        self.assertGreater(strong_5['sweet_16'], weak_5['sweet_16'])
        self.assertGreater(strong_5['elite_8'], weak_5['elite_8'])


class TestCBBFirstHalf(unittest.TestCase):
    """Test first half betting analysis"""

    def test_first_half_calculation(self):
        result = CBBAnalytics.calculate_first_half_probability(
            team_rating=78.0,
            opponent_rating=72.0,
            first_half_spread=-3.0,
            is_home=True
        )

        self.assertIn('cover_probability', result)
        self.assertIn('expected_margin', result)

    def test_first_half_scaled(self):
        # First half margin should be roughly 48% of full game
        full_game = CBBAnalytics.calculate_spread_probability(
            team_rating=80.0,
            opponent_rating=70.0,
            spread=-10.0,
            is_home=True
        )

        first_half = CBBAnalytics.calculate_first_half_probability(
            team_rating=80.0,
            opponent_rating=70.0,
            first_half_spread=-5.0,
            is_home=True
        )

        expected_first_half_margin = full_game['expected_margin'] * 0.48
        self.assertAlmostEqual(
            first_half['expected_margin'],
            expected_first_half_margin,
            delta=1.0
        )


class TestCBBSimulation(unittest.TestCase):
    """Test game and season simulations"""

    def test_simulate_game(self):
        result = CBBAnalytics.simulate_game(
            home_rating=75.0,
            away_rating=70.0,
            seed=42
        )

        self.assertIn('home_score', result)
        self.assertIn('away_score', result)
        self.assertIn('result', result)
        self.assertGreaterEqual(result['home_score'], 0)
        self.assertGreaterEqual(result['away_score'], 0)

    def test_simulate_game_deterministic(self):
        # Same seed should produce same result
        result1 = CBBAnalytics.simulate_game(
            home_rating=75.0,
            away_rating=72.0,
            seed=42
        )

        result2 = CBBAnalytics.simulate_game(
            home_rating=75.0,
            away_rating=72.0,
            seed=42
        )

        self.assertEqual(result1['home_score'], result2['home_score'])
        self.assertEqual(result1['away_score'], result2['away_score'])

    def test_simulate_season(self):
        teams = {
            'Team A': 80.0,
            'Team B': 75.0,
            'Team C': 70.0,
            'Team D': 65.0
        }

        result = CBBAnalytics.simulate_season(
            teams,
            games_per_team=30,
            seed=42
        )

        self.assertIn('standings', result)
        self.assertIn('matches', result)
        self.assertEqual(len(result['standings']), 4)

    def test_season_with_conferences(self):
        teams = {
            'Team A': 80.0,
            'Team B': 75.0,
            'Team C': 70.0,
            'Team D': 65.0
        }

        conferences = {
            'Team A': CBBConference.BIG_EAST,
            'Team B': CBBConference.BIG_EAST,
            'Team C': CBBConference.BIG_TEN,
            'Team D': CBBConference.BIG_TEN
        }

        result = CBBAnalytics.simulate_season(
            teams,
            games_per_team=30,
            conference_teams=conferences,
            seed=42
        )

        # Check conference wins are tracked
        for team, stats in result['standings'].items():
            self.assertIn('conf_wins', stats)
            self.assertIn('conf_losses', stats)


class TestKenPomProbability(unittest.TestCase):
    """Test KenPom probability calculations"""

    def test_kenpom_probability(self):
        prob = calculate_cbb_kenpom_probability(
            kenpom_1=25.0,
            kenpom_2=20.0,
            home_advantage=4.0
        )

        self.assertGreater(prob, 0.5)  # Team 1 should be favored
        self.assertLess(prob, 1.0)

    def test_even_matchup(self):
        prob = calculate_cbb_kenpom_probability(
            kenpom_1=20.0,
            kenpom_2=16.0,  # Exactly home advantage
            home_advantage=4.0
        )

        # Should be roughly 50/50
        self.assertAlmostEqual(prob, 0.5, delta=0.1)

    def test_heavy_favorite(self):
        prob = calculate_cbb_kenpom_probability(
            kenpom_1=35.0,
            kenpom_2=15.0,
            home_advantage=4.0
        )

        # Heavy favorite
        self.assertGreater(prob, 0.9)


class TestConferenceRatings(unittest.TestCase):
    """Test conference strength ratings"""

    def test_major_conferences_positive(self):
        # Major conferences should have positive ratings
        majors = [CBBConference.BIG_EAST, CBBConference.BIG_TEN,
                 CBBConference.BIG_12, CBBConference.ACC, CBBConference.SEC]

        for conf in majors:
            rating = CBBAnalytics.CONFERENCE_RATINGS[conf]
            self.assertGreaterEqual(rating, 0)

    def test_mid_major_conferences_lower(self):
        # Mid-majors should have lower ratings
        mid_majors = [CBBConference.MAC, CBBConference.SUN_BELT]

        for conf in mid_majors:
            rating = CBBAnalytics.CONFERENCE_RATINGS[conf]
            self.assertLess(rating, 0)


class TestCBBIntegration(unittest.TestCase):
    """Integration tests"""

    def test_complete_game_analysis(self):
        # Simulate a complete game analysis workflow
        team1_rating = 80.0
        team2_rating = 72.0
        spread = -6.5
        total = 145.5

        # Analyze spread
        spread_result = CBBAnalytics.calculate_spread_probability(
            team_rating=team1_rating,
            opponent_rating=team2_rating,
            spread=spread,
            is_home=True
        )

        # Analyze total
        total_result = CBBAnalytics.calculate_total_probability(
            team1_avg=team1_rating,
            team2_avg=team2_rating,
            total_line=total
        )

        # Both should return valid results
        self.assertIsNotNone(spread_result['cover_probability'])
        self.assertIsNotNone(total_result['over_probability'])

    def test_tournament_bracket_simulation(self):
        # Simulate a simplified tournament bracket
        seeds_and_ratings = {
            1: 30.0,
            16: 5.0,
            8: 18.0,
            9: 17.0
        }

        for seed, rating in seeds_and_ratings.items():
            result = CBBAnalytics.calculate_tournament_probability(
                team_seed=seed,
                team_rating=rating,
                bracket_region="East"
            )

            # All seeds should have probabilities
            self.assertIsNotNone(result['round_of_32'])
            self.assertIsNotNone(result['sweet_16'])


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
