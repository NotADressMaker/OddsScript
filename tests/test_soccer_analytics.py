#!/usr/bin/env python3
"""
Test suite for Soccer analytics library
"""

import unittest
import sys
import os

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from soccer_analytics import SoccerAnalytics, League


class TestSoccer3WayMoneyline(unittest.TestCase):
    """Test 3-way moneyline calculations"""

    def test_basic_3way_calculation(self):
        result = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('home_win_probability', result)
        self.assertIn('draw_probability', result)
        self.assertIn('away_win_probability', result)

        # Probabilities should sum to 1
        total = (result['home_win_probability'] +
                result['draw_probability'] +
                result['away_win_probability'])
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_home_advantage_impact(self):
        # Home team should have better odds
        result = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg=1.8,
            away_goals_avg=1.8,
            league=League.PREMIER_LEAGUE
        )

        # Home should be favored due to home advantage
        self.assertGreater(result['home_win_probability'],
                          result['away_win_probability'])

    def test_heavy_favorite(self):
        # Strong favorite should have high win probability
        result = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg=2.5,
            away_goals_avg=0.8,
            league=League.PREMIER_LEAGUE
        )

        self.assertGreater(result['home_win_probability'], 0.6)
        self.assertLess(result['away_win_probability'], 0.15)

    def test_league_differences(self):
        # Bundesliga has different characteristics than Serie A
        bundesliga = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            league=League.BUNDESLIGA
        )

        serie_a = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            league=League.SERIE_A
        )

        # Results should differ due to league characteristics
        self.assertNotAlmostEqual(
            bundesliga['home_win_probability'],
            serie_a['home_win_probability'],
            places=2
        )


class TestSoccerDoubleChance(unittest.TestCase):
    """Test double chance calculations"""

    def test_double_chance_calculation(self):
        result = SoccerAnalytics.calculate_double_chance(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('home_or_draw', result)
        self.assertIn('away_or_draw', result)
        self.assertIn('home_or_away', result)

    def test_double_chance_probabilities(self):
        result = SoccerAnalytics.calculate_double_chance(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE
        )

        # All double chance bets should be > 0.5
        self.assertGreater(result['home_or_draw'], 0.5)
        self.assertGreater(result['away_or_draw'], 0.5)

        # Home or away (no draw) might be less than 0.5 depending on draw prob
        self.assertGreater(result['home_or_away'], 0.0)
        self.assertLess(result['home_or_away'], 1.0)


class TestAsianHandicap(unittest.TestCase):
    """Test Asian handicap calculations"""

    def test_basic_handicap(self):
        result = SoccerAnalytics.calculate_asian_handicap(
            home_goals_avg=2.2,
            away_goals_avg=1.3,
            handicap=-1.0,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('home_cover_probability', result)
        self.assertIn('away_cover_probability', result)
        self.assertIn('push_probability', result)

    def test_handicap_probabilities_sum(self):
        result = SoccerAnalytics.calculate_asian_handicap(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            handicap=-0.5,
            league=League.PREMIER_LEAGUE
        )

        # Should sum to 1 (no push with half goals)
        total = (result['home_cover_probability'] +
                result['away_cover_probability'] +
                result['push_probability'])
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_whole_goal_handicap_can_push(self):
        result = SoccerAnalytics.calculate_asian_handicap(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            handicap=-1.0,
            league=League.PREMIER_LEAGUE
        )

        # With whole number handicap, push is possible
        self.assertGreater(result['push_probability'], 0.0)

    def test_positive_handicap(self):
        # Underdog with positive handicap
        result = SoccerAnalytics.calculate_asian_handicap(
            home_goals_avg=1.2,
            away_goals_avg=2.0,
            handicap=1.5,
            league=League.PREMIER_LEAGUE
        )

        # Home (underdog) should have better chance with handicap
        self.assertGreater(result['home_cover_probability'], 0.5)


class TestTotalGoals(unittest.TestCase):
    """Test total goals over/under calculations"""

    def test_basic_total_calculation(self):
        result = SoccerAnalytics.calculate_total_goals(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            total_line=2.5,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('over_probability', result)
        self.assertIn('under_probability', result)
        self.assertIn('expected_total', result)

    def test_total_probabilities_sum(self):
        result = SoccerAnalytics.calculate_total_goals(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            total_line=2.5,
            league=League.PREMIER_LEAGUE
        )

        total = result['over_probability'] + result['under_probability']
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_high_scoring_match(self):
        result = SoccerAnalytics.calculate_total_goals(
            home_goals_avg=2.8,
            away_goals_avg=2.5,
            total_line=2.5,
            league=League.BUNDESLIGA  # High scoring league
        )

        # Should heavily favor over
        self.assertGreater(result['over_probability'], 0.7)

    def test_low_scoring_match(self):
        result = SoccerAnalytics.calculate_total_goals(
            home_goals_avg=1.0,
            away_goals_avg=0.9,
            total_line=2.5,
            league=League.SERIE_A
        )

        # Should heavily favor under
        self.assertGreater(result['under_probability'], 0.6)


class TestBothTeamsToScore(unittest.TestCase):
    """Test BTTS (both teams to score) calculations"""

    def test_basic_btts_calculation(self):
        result = SoccerAnalytics.calculate_both_teams_to_score(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            home_goals_against_avg=1.2,
            away_goals_against_avg=1.3,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('btts_yes_probability', result)
        self.assertIn('btts_no_probability', result)
        self.assertIn('home_clean_sheet_probability', result)
        self.assertIn('away_clean_sheet_probability', result)

    def test_btts_probabilities_sum(self):
        result = SoccerAnalytics.calculate_both_teams_to_score(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            home_goals_against_avg=1.2,
            away_goals_against_avg=1.3,
            league=League.PREMIER_LEAGUE
        )

        total = result['btts_yes_probability'] + result['btts_no_probability']
        self.assertAlmostEqual(total, 1.0, places=2)

    def test_high_scoring_teams_btts(self):
        # Both teams score a lot
        result = SoccerAnalytics.calculate_both_teams_to_score(
            home_goals_avg=2.5,
            away_goals_avg=2.3,
            home_goals_against_avg=1.8,
            away_goals_against_avg=1.9,
            league=League.BUNDESLIGA
        )

        # Should favor BTTS yes
        self.assertGreater(result['btts_yes_probability'], 0.6)

    def test_defensive_teams_btts(self):
        # Strong defenses
        result = SoccerAnalytics.calculate_both_teams_to_score(
            home_goals_avg=1.2,
            away_goals_avg=1.0,
            home_goals_against_avg=0.6,
            away_goals_against_avg=0.7,
            league=League.SERIE_A
        )

        # Should favor BTTS no (clean sheets likely)
        self.assertGreater(result['btts_no_probability'], result['btts_yes_probability'])


class TestCorrectScore(unittest.TestCase):
    """Test correct score probability calculations"""

    def test_correct_score_calculation(self):
        scores = SoccerAnalytics.calculate_correct_score_probabilities(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            top_n=5
        )

        self.assertEqual(len(scores), 5)

        for score in scores:
            self.assertIn('home_score', score)
            self.assertIn('away_score', score)
            self.assertIn('probability', score)
            self.assertIn('result', score)

    def test_scores_sorted_by_probability(self):
        scores = SoccerAnalytics.calculate_correct_score_probabilities(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            top_n=10
        )

        # Check scores are sorted (highest probability first)
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i]['probability'],
                scores[i + 1]['probability']
            )

    def test_most_likely_scores_reasonable(self):
        scores = SoccerAnalytics.calculate_correct_score_probabilities(
            home_goals_avg=1.8,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            top_n=5
        )

        # Most likely scores should be low (0-0, 1-0, 1-1, etc.)
        for score in scores:
            self.assertLessEqual(score['home_score'], 4)
            self.assertLessEqual(score['away_score'], 4)


class TestExpectedGoals(unittest.TestCase):
    """Test expected goals (xG) based calculations"""

    def test_xg_probability(self):
        result = SoccerAnalytics.calculate_expected_goals_probability(
            home_xg=2.3,
            away_xg=1.1,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('home_win_probability', result)
        self.assertIn('draw_probability', result)
        self.assertIn('away_win_probability', result)
        self.assertIn('home_xg', result)
        self.assertIn('away_xg', result)

    def test_xg_probabilities_sum(self):
        result = SoccerAnalytics.calculate_expected_goals_probability(
            home_xg=1.8,
            away_xg=1.5,
            league=League.PREMIER_LEAGUE
        )

        total = (result['home_win_probability'] +
                result['draw_probability'] +
                result['away_win_probability'])
        self.assertAlmostEqual(total, 1.0, places=2)


class TestFirstHalf(unittest.TestCase):
    """Test first half betting calculations"""

    def test_first_half_calculation(self):
        result = SoccerAnalytics.calculate_first_half_probability(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE
        )

        self.assertIn('home_win_probability', result)
        self.assertIn('draw_probability', result)
        self.assertIn('away_win_probability', result)
        self.assertIn('expected_total_goals', result)

    def test_first_half_lower_scoring(self):
        full_match = SoccerAnalytics.calculate_total_goals(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            total_line=2.5,
            league=League.PREMIER_LEAGUE
        )

        first_half = SoccerAnalytics.calculate_first_half_probability(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE
        )

        # First half should have lower expected goals
        self.assertLess(
            first_half['expected_total_goals'],
            full_match['expected_total']
        )

    def test_first_half_draw_more_likely(self):
        result = SoccerAnalytics.calculate_first_half_probability(
            home_goals_avg=2.0,
            away_goals_avg=1.8,
            league=League.PREMIER_LEAGUE
        )

        # Draw should be quite likely in first half
        self.assertGreater(result['draw_probability'], 0.3)


class TestLeagueCharacteristics(unittest.TestCase):
    """Test league characteristics analysis"""

    def test_league_analysis(self):
        result = SoccerAnalytics.analyze_league_characteristics(
            League.PREMIER_LEAGUE
        )

        self.assertIn('league', result)
        self.assertIn('avg_goals_per_game', result)
        self.assertIn('home_advantage', result)
        self.assertIn('draw_rate', result)
        self.assertIn('scoring_style', result)
        self.assertIn('betting_advice', result)

    def test_bundesliga_high_scoring(self):
        result = SoccerAnalytics.analyze_league_characteristics(
            League.BUNDESLIGA
        )

        # Bundesliga is known for high scoring
        self.assertGreater(result['avg_goals_per_game'], 3.0)
        self.assertEqual(result['scoring_style'], "High scoring")

    def test_serie_a_tactical(self):
        result = SoccerAnalytics.analyze_league_characteristics(
            League.SERIE_A
        )

        # Serie A is more defensive
        self.assertLess(result['avg_goals_per_game'], 2.75)

    def test_world_cup_characteristics(self):
        result = SoccerAnalytics.analyze_league_characteristics(
            League.WORLD_CUP
        )

        # World Cup has low scoring and high draw rate
        self.assertLess(result['avg_goals_per_game'], 2.60)
        self.assertGreater(result['draw_rate'], 0.28)


class TestSoccerSimulation(unittest.TestCase):
    """Test match and season simulations"""

    def test_simulate_match(self):
        result = SoccerAnalytics.simulate_match(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            seed=42
        )

        self.assertIn('home_goals', result)
        self.assertIn('away_goals', result)
        self.assertIn('result', result)
        self.assertIn('score', result)
        self.assertGreaterEqual(result['home_goals'], 0)
        self.assertGreaterEqual(result['away_goals'], 0)

    def test_simulate_match_deterministic(self):
        # Same seed should produce same result
        result1 = SoccerAnalytics.simulate_match(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            seed=42
        )

        result2 = SoccerAnalytics.simulate_match(
            home_goals_avg=2.0,
            away_goals_avg=1.5,
            league=League.PREMIER_LEAGUE,
            seed=42
        )

        self.assertEqual(result1['home_goals'], result2['home_goals'])
        self.assertEqual(result1['away_goals'], result2['away_goals'])

    def test_simulate_season(self):
        teams = {
            'Man City': 2.5,
            'Arsenal': 2.3,
            'Liverpool': 2.2,
            'Chelsea': 1.9
        }

        result = SoccerAnalytics.simulate_season(
            teams,
            league=League.PREMIER_LEAGUE,
            seed=42
        )

        self.assertIn('standings', result)
        self.assertIn('matches', result)
        self.assertEqual(len(result['standings']), 4)

        # Check standings have correct fields
        for team, stats in result['standings'].items():
            self.assertIn('wins', stats)
            self.assertIn('draws', stats)
            self.assertIn('losses', stats)
            self.assertIn('points', stats)
            self.assertIn('gf', stats)  # Goals for
            self.assertIn('ga', stats)  # Goals against

    def test_season_points_system(self):
        teams = {
            'Team A': 2.0,
            'Team B': 1.5
        }

        result = SoccerAnalytics.simulate_season(
            teams,
            league=League.PREMIER_LEAGUE,
            seed=42
        )

        # Check points calculation (3 for win, 1 for draw)
        for team, stats in result['standings'].items():
            expected_points = stats['wins'] * 3 + stats['draws'] * 1
            self.assertEqual(stats['points'], expected_points)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple features"""

    def test_complete_match_analysis(self):
        # Simulate complete pre-match analysis
        home_goals_avg = 2.1
        away_goals_avg = 1.6

        # 3-way moneyline
        moneyline = SoccerAnalytics.calculate_3way_moneyline(
            home_goals_avg,
            away_goals_avg,
            league=League.PREMIER_LEAGUE
        )

        # Total goals
        total = SoccerAnalytics.calculate_total_goals(
            home_goals_avg,
            away_goals_avg,
            total_line=2.5,
            league=League.PREMIER_LEAGUE
        )

        # BTTS
        btts = SoccerAnalytics.calculate_both_teams_to_score(
            home_goals_avg,
            away_goals_avg,
            home_goals_against_avg=1.1,
            away_goals_against_avg=1.3,
            league=League.PREMIER_LEAGUE
        )

        # All should return valid probabilities
        self.assertIsNotNone(moneyline['home_win_probability'])
        self.assertIsNotNone(total['over_probability'])
        self.assertIsNotNone(btts['btts_yes_probability'])

    def test_cross_league_comparison(self):
        # Same teams in different leagues should have different probabilities
        leagues = [League.PREMIER_LEAGUE, League.BUNDESLIGA, League.SERIE_A]

        results = []
        for league in leagues:
            result = SoccerAnalytics.calculate_3way_moneyline(
                home_goals_avg=2.0,
                away_goals_avg=1.8,
                league=league
            )
            results.append(result)

        # Results should differ across leagues
        self.assertNotAlmostEqual(
            results[0]['home_win_probability'],
            results[1]['home_win_probability'],
            places=2
        )


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
