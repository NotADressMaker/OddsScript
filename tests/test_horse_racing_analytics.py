#!/usr/bin/env python3
"""
Test suite for horse racing analytics library
"""

import unittest
import sys
import os

# Add lib directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))

from horse_racing_analytics import (
    Horse, JockeyStats, TrainerStats,
    SpeedRatingModel, PostPositionAnalysis, ExoticBetCalculator,
    DistanceSurfaceModel, HorseRacingAnalyzer,
    TrackSurface, TrackCondition
)


class TestHorse(unittest.TestCase):
    """Test Horse dataclass"""

    def test_win_percentage(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[95, 92, 90],
            best_speed_figure=95,
            days_since_last_race=14,
            career_starts=10,
            career_wins=3,
            career_places=2,
            career_shows=1
        )
        self.assertEqual(horse.win_percentage(), 30.0)

    def test_distance_win_percentage(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[95],
            best_speed_figure=95,
            days_since_last_race=14,
            career_starts=10,
            career_wins=3,
            career_places=2,
            career_shows=1,
            distance_starts=5,
            distance_wins=2
        )
        self.assertEqual(horse.distance_win_percentage(), 40.0)

    def test_zero_starts(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[],
            best_speed_figure=0,
            days_since_last_race=0,
            career_starts=0,
            career_wins=0,
            career_places=0,
            career_shows=0
        )
        self.assertEqual(horse.win_percentage(), 0.0)


class TestJockeyStats(unittest.TestCase):
    """Test JockeyStats dataclass"""

    def test_win_percentage(self):
        jockey = JockeyStats(
            name="J. Smith",
            starts=100,
            wins=20,
            places=15,
            shows=10,
            earnings=500000
        )
        self.assertEqual(jockey.win_percentage(), 20.0)

    def test_roi(self):
        jockey = JockeyStats(
            name="J. Smith",
            starts=100,
            wins=20,
            places=15,
            shows=10,
            earnings=120000
        )
        roi = jockey.roi(total_bet=100000)
        self.assertEqual(roi, 20.0)


class TestSpeedRatingModel(unittest.TestCase):
    """Test speed rating calculations"""

    def test_calculate_speed_figure_at_par(self):
        # Horse runs exactly at par
        speed_fig = SpeedRatingModel.calculate_speed_figure(
            final_time=96.0,  # 8 furlongs at 12 sec/furlong
            distance_furlongs=8.0,
            track_surface=TrackSurface.DIRT,
            track_condition=TrackCondition.FAST,
            par_time=96.0
        )
        self.assertEqual(speed_fig, 100)

    def test_calculate_speed_figure_above_par(self):
        # Horse runs faster than par (1 second = 5 lengths = 10 points)
        speed_fig = SpeedRatingModel.calculate_speed_figure(
            final_time=95.0,  # 1 second faster
            distance_furlongs=8.0,
            track_surface=TrackSurface.DIRT,
            track_condition=TrackCondition.FAST,
            par_time=96.0
        )
        self.assertEqual(speed_fig, 110)  # 100 + (5 lengths * 2 points)

    def test_calculate_speed_figure_below_par(self):
        # Horse runs slower than par
        speed_fig = SpeedRatingModel.calculate_speed_figure(
            final_time=97.0,  # 1 second slower
            distance_furlongs=8.0,
            track_surface=TrackSurface.DIRT,
            track_condition=TrackCondition.FAST,
            par_time=96.0
        )
        self.assertEqual(speed_fig, 90)

    def test_track_condition_adjustment(self):
        # Muddy track should reduce speed figure
        speed_fig = SpeedRatingModel.calculate_speed_figure(
            final_time=96.0,
            distance_furlongs=8.0,
            track_surface=TrackSurface.DIRT,
            track_condition=TrackCondition.MUDDY,
            par_time=96.0
        )
        self.assertEqual(speed_fig, 96)  # 100 - 4 for muddy

    def test_average_speed_figure(self):
        figures = [100, 95, 90, 85, 80]
        avg = SpeedRatingModel.calculate_average_speed_figure(figures, num_races=3)
        self.assertEqual(avg, 95.0)  # (100 + 95 + 90) / 3

    def test_form_trend_improving(self):
        figures = [100, 95, 90]
        trend = SpeedRatingModel.calculate_form_trend(figures)
        self.assertEqual(trend, "improving")

    def test_form_trend_declining(self):
        figures = [90, 95, 100]
        trend = SpeedRatingModel.calculate_form_trend(figures)
        self.assertEqual(trend, "declining")

    def test_form_trend_consistent(self):
        figures = [95, 96, 94]
        trend = SpeedRatingModel.calculate_form_trend(figures)
        self.assertEqual(trend, "consistent")


class TestPostPositionAnalysis(unittest.TestCase):
    """Test post position bias calculations"""

    def test_inside_post_sprint_advantage(self):
        # Inside post in sprint should have advantage
        bias = PostPositionAnalysis.calculate_post_bias(
            post_position=2,
            num_horses=10,
            distance_furlongs=6.0
        )
        self.assertEqual(bias, 1.15)

    def test_outside_post_sprint_disadvantage(self):
        # Outside post in sprint should have disadvantage
        bias = PostPositionAnalysis.calculate_post_bias(
            post_position=9,
            num_horses=10,
            distance_furlongs=6.0
        )
        self.assertEqual(bias, 0.85)

    def test_middle_post_neutral(self):
        # Middle posts should be neutral
        bias = PostPositionAnalysis.calculate_post_bias(
            post_position=5,
            num_horses=10,
            distance_furlongs=6.0
        )
        self.assertEqual(bias, 1.0)

    def test_route_race_less_bias(self):
        # Route races have less post bias
        bias = PostPositionAnalysis.calculate_post_bias(
            post_position=2,
            num_horses=10,
            distance_furlongs=10.0
        )
        self.assertEqual(bias, 1.05)  # Less than 1.15 for sprint

    def test_optimal_post_range_sprint(self):
        min_post, max_post = PostPositionAnalysis.get_optimal_post_range(
            distance_furlongs=6.0,
            num_horses=10
        )
        self.assertEqual(min_post, 1)
        self.assertEqual(max_post, 4)

    def test_optimal_post_range_route(self):
        min_post, max_post = PostPositionAnalysis.get_optimal_post_range(
            distance_furlongs=10.0,
            num_horses=10
        )
        self.assertEqual(min_post, 1)
        self.assertEqual(max_post, 6)


class TestExoticBetCalculator(unittest.TestCase):
    """Test exotic bet probability calculations"""

    def test_american_to_decimal_positive(self):
        decimal = ExoticBetCalculator.american_to_decimal(300)
        self.assertEqual(decimal, 4.0)

    def test_american_to_decimal_negative(self):
        decimal = ExoticBetCalculator.american_to_decimal(-200)
        self.assertEqual(decimal, 1.5)

    def test_american_to_probability(self):
        prob = ExoticBetCalculator.american_to_probability(300)
        self.assertAlmostEqual(prob, 0.25, places=2)

    def test_exacta_probability(self):
        prob = ExoticBetCalculator.calculate_exacta_probability(
            horse1_prob=0.30,
            horse2_prob=0.20
        )
        self.assertAlmostEqual(prob, 0.06, places=2)

    def test_trifecta_probability(self):
        prob = ExoticBetCalculator.calculate_trifecta_probability(
            horse1_prob=0.30,
            horse2_prob=0.20,
            horse3_prob=0.15
        )
        self.assertAlmostEqual(prob, 0.009, places=3)

    def test_superfecta_probability(self):
        prob = ExoticBetCalculator.calculate_superfecta_probability(
            horse1_prob=0.30,
            horse2_prob=0.20,
            horse3_prob=0.15,
            horse4_prob=0.10
        )
        self.assertAlmostEqual(prob, 0.0009, places=4)

    def test_exacta_expected_value(self):
        result = ExoticBetCalculator.calculate_exacta_expected_value(
            horse1_odds=300,
            horse2_odds=400,
            horse1_true_prob=0.30,
            horse2_true_prob=0.25,
            bet_amount=2.0
        )
        self.assertIn('probability', result)
        self.assertIn('payout', result)
        self.assertIn('expected_value', result)
        self.assertIn('roi', result)
        self.assertEqual(result['bet_amount'], 2.0)


class TestDistanceSurfaceModel(unittest.TestCase):
    """Test distance and surface suitability models"""

    def test_classify_distance_sprint(self):
        classification = DistanceSurfaceModel.classify_distance(6.0)
        self.assertEqual(classification, "sprint")

    def test_classify_distance_middle(self):
        classification = DistanceSurfaceModel.classify_distance(8.5)
        self.assertEqual(classification, "middle")

    def test_classify_distance_route(self):
        classification = DistanceSurfaceModel.classify_distance(10.0)
        self.assertEqual(classification, "route")

    def test_distance_suitability_no_data(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[95],
            best_speed_figure=95,
            days_since_last_race=14,
            career_starts=10,
            career_wins=3,
            career_places=2,
            career_shows=1,
            distance_starts=0,
            distance_wins=0
        )
        suitability = DistanceSurfaceModel.calculate_distance_suitability(
            horse,
            race_distance_furlongs=8.0
        )
        # Should default to career win rate
        self.assertAlmostEqual(suitability, 0.30, places=2)

    def test_distance_suitability_with_data(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[95],
            best_speed_figure=95,
            days_since_last_race=14,
            career_starts=10,
            career_wins=3,
            career_places=2,
            career_shows=1,
            distance_starts=5,
            distance_wins=3  # 60% at this distance vs 30% overall
        )
        suitability = DistanceSurfaceModel.calculate_distance_suitability(
            horse,
            race_distance_furlongs=8.0
        )
        # Should be between 30% and 60%
        self.assertGreater(suitability, 0.30)
        self.assertLess(suitability, 0.60)

    def test_surface_suitability(self):
        horse = Horse(
            name="Test Horse",
            odds=300,
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[95],
            best_speed_figure=95,
            days_since_last_race=14,
            career_starts=10,
            career_wins=3,
            career_places=2,
            career_shows=1,
            surface_starts=8,
            surface_wins=4  # 50% on this surface vs 30% overall
        )
        suitability = DistanceSurfaceModel.calculate_surface_suitability(
            horse,
            race_surface=TrackSurface.DIRT
        )
        # Should be close to 50% with high confidence
        self.assertGreater(suitability, 0.40)
        self.assertLess(suitability, 0.60)


class TestHorseRacingAnalyzer(unittest.TestCase):
    """Test comprehensive race analyzer"""

    def setUp(self):
        """Create test horses for analysis"""
        self.horse1 = Horse(
            name="Favorite",
            odds=-200,  # Strong favorite
            post_position=3,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[105, 103, 100],
            best_speed_figure=105,
            days_since_last_race=14,
            career_starts=15,
            career_wins=8,
            career_places=3,
            career_shows=2,
            distance_starts=5,
            distance_wins=3,
            surface_starts=10,
            surface_wins=6
        )

        self.horse2 = Horse(
            name="Longshot",
            odds=1000,
            post_position=10,
            jockey="M. Johnson",
            trainer="B. Smith",
            recent_speed_figures=[85, 83, 82],
            best_speed_figure=88,
            days_since_last_race=30,
            career_starts=20,
            career_wins=2,
            career_places=3,
            career_shows=4,
            distance_starts=3,
            distance_wins=0,
            surface_starts=15,
            surface_wins=2
        )

        self.analyzer = HorseRacingAnalyzer()

    def test_analyze_horse(self):
        analysis = self.analyzer.analyze_horse(
            self.horse1,
            race_distance_furlongs=8.0,
            race_surface=TrackSurface.DIRT,
            num_horses=10
        )

        self.assertEqual(analysis['horse_name'], "Favorite")
        self.assertEqual(analysis['market_odds'], -200)
        self.assertIn('market_probability', analysis)
        self.assertIn('adjusted_probability', analysis)
        self.assertIn('average_speed_figure', analysis)
        self.assertIn('form_trend', analysis)
        self.assertIn('post_bias_multiplier', analysis)

    def test_analyze_race(self):
        horses = [self.horse1, self.horse2]
        analyses = self.analyzer.analyze_race(
            horses,
            race_distance_furlongs=8.0,
            race_surface=TrackSurface.DIRT
        )

        self.assertEqual(len(analyses), 2)
        # Should be sorted by adjusted probability
        self.assertGreater(
            analyses[0]['adjusted_probability'],
            analyses[1]['adjusted_probability']
        )

    def test_find_betting_opportunities(self):
        # Create a horse with value (higher true prob than market prob)
        value_horse = Horse(
            name="Value Horse",
            odds=500,  # 16.7% implied
            post_position=2,
            jockey="J. Smith",
            trainer="T. Jones",
            recent_speed_figures=[100, 98, 96],
            best_speed_figure=100,
            days_since_last_race=14,
            career_starts=10,
            career_wins=4,
            career_places=2,
            career_shows=1,
            distance_starts=5,
            distance_wins=3,
            surface_starts=8,
            surface_wins=4
        )

        horses = [value_horse]
        analyses = self.analyzer.analyze_race(
            horses,
            race_distance_furlongs=6.0,  # Sprint, good post position
            race_surface=TrackSurface.DIRT
        )

        opportunities = self.analyzer.find_betting_opportunities(
            analyses,
            min_edge=0.05
        )

        # Should find opportunities or not depending on adjustments
        self.assertIsInstance(opportunities, list)
        for opp in opportunities:
            self.assertIn('horse_name', opp)
            self.assertIn('edge', opp)
            self.assertGreater(opp['edge'], 0.05)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple models"""

    def test_complete_race_analysis_workflow(self):
        """Test complete workflow from horses to betting recommendations"""

        # Create a field of horses
        horses = [
            Horse(
                name="Speed Demon",
                odds=200,
                post_position=2,
                jockey="J. Velazquez",
                trainer="T. Pletcher",
                recent_speed_figures=[108, 105, 103],
                best_speed_figure=108,
                days_since_last_race=21,
                career_starts=12,
                career_wins=5,
                career_places=3,
                career_shows=2,
                distance_starts=4,
                distance_wins=3,
                surface_starts=10,
                surface_wins=5
            ),
            Horse(
                name="Steady Runner",
                odds=400,
                post_position=5,
                jockey="I. Ortiz",
                trainer="C. McGaughey",
                recent_speed_figures=[95, 96, 94],
                best_speed_figure=97,
                days_since_last_race=14,
                career_starts=20,
                career_wins=6,
                career_places=5,
                career_shows=4,
                distance_starts=8,
                distance_wins=3,
                surface_starts=18,
                surface_wins=6
            ),
            Horse(
                name="Late Closer",
                odds=800,
                post_position=8,
                jockey="M. Smith",
                trainer="B. Baffert",
                recent_speed_figures=[90, 92, 89],
                best_speed_figure=93,
                days_since_last_race=28,
                career_starts=15,
                career_wins=3,
                career_places=4,
                career_shows=3,
                distance_starts=5,
                distance_wins=1,
                surface_starts=12,
                surface_wins=3
            )
        ]

        # Analyze race
        analyzer = HorseRacingAnalyzer()
        analyses = analyzer.analyze_race(
            horses,
            race_distance_furlongs=8.0,
            race_surface=TrackSurface.DIRT
        )

        # Verify all horses analyzed
        self.assertEqual(len(analyses), 3)

        # Verify ranking
        for i in range(len(analyses) - 1):
            self.assertGreaterEqual(
                analyses[i]['adjusted_probability'],
                analyses[i + 1]['adjusted_probability']
            )

        # Find opportunities
        opportunities = analyzer.find_betting_opportunities(analyses)

        # Should return list (may be empty)
        self.assertIsInstance(opportunities, list)


def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
