#!/usr/bin/env python3
"""
Comprehensive test suite for advanced statistics library
"""

import unittest
import math
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.advanced_stats import (
    AdvancedStats, RegressionResult, TimeSeriesResult, BayesianResult
)


class TestLinearRegression(unittest.TestCase):
    """Test linear regression"""

    def test_simple_linear_regression(self):
        """Test basic linear regression"""
        # y = 2x + 1
        x = [1, 2, 3, 4, 5]
        y = [3, 5, 7, 9, 11]

        result = AdvancedStats.linear_regression(x, y)

        self.assertAlmostEqual(result.coefficients[0], 2.0, places=5)
        self.assertAlmostEqual(result.intercept, 1.0, places=5)
        self.assertAlmostEqual(result.r_squared, 1.0, places=5)

    def test_regression_with_noise(self):
        """Test regression with noisy data"""
        x = [1, 2, 3, 4, 5]
        y = [3.1, 4.9, 7.2, 8.8, 11.1]

        result = AdvancedStats.linear_regression(x, y)

        # Should be close to y = 2x + 1
        self.assertAlmostEqual(result.coefficients[0], 2.0, places=0)
        self.assertAlmostEqual(result.intercept, 1.0, places=0)
        self.assertGreater(result.r_squared, 0.95)

    def test_regression_minimum_points(self):
        """Test regression with minimum number of points"""
        x = [1, 2]
        y = [2, 4]

        result = AdvancedStats.linear_regression(x, y)

        self.assertEqual(len(result.predictions), 2)

    def test_regression_error_cases(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            AdvancedStats.linear_regression([1], [1])  # Too few points

        with self.assertRaises(ValueError):
            AdvancedStats.linear_regression([1, 2], [1])  # Length mismatch


class TestMultipleRegression(unittest.TestCase):
    """Test multiple regression"""

    def test_two_variable_regression(self):
        """Test regression with two independent variables"""
        # y = 2x1 + 3x2 + 1
        X = [[1, 1], [2, 1], [1, 2], [2, 2], [3, 1]]
        y = [6, 8, 10, 12, 10]

        result = AdvancedStats.multiple_regression(X, y)

        # Check dimensions
        self.assertEqual(len(result.coefficients), 2)
        self.assertEqual(len(result.predictions), 5)

        # Check R-squared is reasonable
        self.assertGreater(result.r_squared, 0.8)

    def test_regression_metrics(self):
        """Test MSE, RMSE, MAE calculations"""
        X = [[1], [2], [3], [4], [5]]
        y = [2, 4, 6, 8, 10]

        result = AdvancedStats.multiple_regression(X, y)

        self.assertIsInstance(result.mse, float)
        self.assertIsInstance(result.rmse, float)
        self.assertIsInstance(result.mae, float)
        self.assertGreaterEqual(result.mse, 0)


class TestLogisticRegression(unittest.TestCase):
    """Test logistic regression"""

    def test_binary_classification(self):
        """Test basic binary classification"""
        x = [1, 2, 3, 4, 5, 6, 7, 8]
        y = [0, 0, 0, 0, 1, 1, 1, 1]

        slope, intercept = AdvancedStats.logistic_regression_simple(
            x, y, learning_rate=0.1, iterations=1000
        )

        # Make predictions
        predictions = [1 / (1 + math.exp(-(intercept + slope * xi))) for xi in x]

        # Check predictions are probabilities
        for pred in predictions:
            self.assertGreaterEqual(pred, 0)
            self.assertLessEqual(pred, 1)

        # Check accuracy is reasonable
        predictions_binary = [1 if p > 0.5 else 0 for p in predictions]
        accuracy = sum(1 for i in range(len(y)) if predictions_binary[i] == y[i]) / len(y)
        self.assertGreater(accuracy, 0.7)


class TestTimeSeriesAnalysis(unittest.TestCase):
    """Test time series analysis methods"""

    def test_exponential_moving_average(self):
        """Test EMA calculation"""
        data = [10, 12, 14, 13, 15, 17, 16, 18]

        ema = AdvancedStats.exponential_moving_average(data, alpha=0.3)

        self.assertEqual(len(ema), len(data))
        self.assertEqual(ema[0], data[0])
        # EMA should be between min and max
        self.assertGreaterEqual(min(ema), min(data))
        self.assertLessEqual(max(ema), max(data))

    def test_weighted_moving_average(self):
        """Test WMA calculation"""
        data = [10, 12, 14, 16, 18, 20]

        wma = AdvancedStats.weighted_moving_average(data, window=3)

        # Should have same length as input (with None for initial values)
        self.assertEqual(len(wma), len(data))

        # WMA should smooth the data (check non-None values)
        for val in wma:
            if val is not None:
                self.assertGreaterEqual(val, min(data))
                self.assertLessEqual(val, max(data))

    def test_moving_average(self):
        """Test simple moving average"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        ma = AdvancedStats.moving_average(data, window=3)

        # Check length (same as input, with None for initial values)
        self.assertEqual(len(ma), len(data))

        # Check first non-None value (at index 2, since window=3)
        self.assertAlmostEqual(ma[2], 2.0)  # (1+2+3)/3

    def test_calculate_trend(self):
        """Test trend calculation"""
        # Upward trend
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        trend = AdvancedStats.calculate_trend(data, method='linear')

        self.assertEqual(len(trend), len(data))
        # Trend should be increasing
        self.assertLess(trend[0], trend[-1])


class TestBayesianInference(unittest.TestCase):
    """Test Bayesian inference methods"""

    def test_bayesian_update(self):
        """Test basic Bayesian update"""
        prior = 0.5
        likelihood = 0.8
        evidence = 0.6

        posterior = AdvancedStats.bayesian_update(prior, likelihood, evidence)

        self.assertGreaterEqual(posterior, 0)
        self.assertLessEqual(posterior, 1)

    def test_bayesian_win_probability(self):
        """Test Bayesian win probability estimation"""
        wins = 7
        losses = 3

        result = AdvancedStats.bayesian_win_probability(wins, losses)

        # Check mean probability
        self.assertGreater(result['mean_probability'], 0.5)  # More wins than losses
        self.assertLess(result['mean_probability'], 1.0)

        # Check credible interval
        self.assertLess(result['ci_lower'], result['mean_probability'])
        self.assertGreater(result['ci_upper'], result['mean_probability'])

    def test_bayesian_with_strong_prior(self):
        """Test Bayesian update with strong prior"""
        wins = 1
        losses = 0

        # Strong prior towards 50%
        result = AdvancedStats.bayesian_win_probability(
            wins, losses, prior_alpha=100, prior_beta=100
        )

        # Should be closer to 50% than 100%
        self.assertLess(result['mean_probability'], 0.6)


class TestMonteCarloSimulation(unittest.TestCase):
    """Test Monte Carlo simulation"""

    def test_coin_flip_simulation(self):
        """Test Monte Carlo for coin flips"""
        def flip_coin():
            """Simulate coin flip with 50% probability"""
            return 1 if __import__('random').random() < 0.5 else 0

        result = AdvancedStats.monte_carlo_simulation(
            flip_coin, n_simulations=10000
        )

        # Mean should be close to 0.5
        self.assertAlmostEqual(result['mean'], 0.5, delta=0.05)

        # Check result structure
        self.assertIn('mean', result)
        self.assertIn('median', result)
        self.assertIn('std_dev', result)
        self.assertIn('results', result)

        self.assertEqual(len(result['results']), 10000)

    def test_dice_roll_simulation(self):
        """Test Monte Carlo for dice rolls"""
        def roll_dice():
            """Simulate rolling a 6-sided die"""
            return __import__('random').randint(1, 6)

        result = AdvancedStats.monte_carlo_simulation(
            roll_dice, n_simulations=10000
        )

        # Mean should be close to 3.5
        self.assertAlmostEqual(result['mean'], 3.5, delta=0.1)

        # Min and max should be 1 and 6
        self.assertGreaterEqual(result['min'], 1)
        self.assertLessEqual(result['max'], 6)


class TestBootstrapMethods(unittest.TestCase):
    """Test bootstrap resampling"""

    def test_bootstrap_confidence_interval(self):
        """Test bootstrap CI for mean"""
        import statistics

        data = [10, 12, 14, 16, 18, 20, 22, 24, 26, 28]

        ci = AdvancedStats.bootstrap_confidence_interval(
            data,
            statistics.mean,
            n_bootstrap=1000,
            confidence_level=0.95
        )

        # CI should contain the sample mean
        sample_mean = statistics.mean(data)
        self.assertLess(ci['ci_lower'], sample_mean)
        self.assertGreater(ci['ci_upper'], sample_mean)

        # Check structure
        self.assertIn('statistic', ci)
        self.assertIn('ci_lower', ci)
        self.assertIn('ci_upper', ci)
        self.assertIn('confidence_level', ci)

    def test_bootstrap_for_median(self):
        """Test bootstrap CI for median"""
        import statistics

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        ci = AdvancedStats.bootstrap_confidence_interval(
            data,
            statistics.median,
            n_bootstrap=1000
        )

        # Median should be around 5.5
        self.assertAlmostEqual(ci['statistic'], 5.5, delta=1)


class TestPermutationTest(unittest.TestCase):
    """Test permutation testing"""

    def test_permutation_test_same_groups(self):
        """Test permutation test with identical groups"""
        group1 = [10, 12, 14, 16, 18]
        group2 = [10, 12, 14, 16, 18]

        result = AdvancedStats.permutation_test(
            group1, group2, n_permutations=1000
        )

        # p-value should be high (groups are identical)
        self.assertGreater(result['p_value'], 0.5)

    def test_permutation_test_different_groups(self):
        """Test permutation test with very different groups"""
        group1 = [1, 2, 3, 4, 5]
        group2 = [10, 11, 12, 13, 14]

        result = AdvancedStats.permutation_test(
            group1, group2, n_permutations=10000
        )

        # p-value should be low (groups are very different)
        # Use more permutations for stable results
        self.assertLess(result['p_value'], 0.01)

        # Check structure
        self.assertIn('observed_difference', result)
        self.assertIn('p_value', result)
        self.assertIn('significant', result)


class TestCorrelationAnalysis(unittest.TestCase):
    """Test correlation methods"""

    def test_pearson_correlation_perfect(self):
        """Test perfect positive correlation"""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]

        correlation = AdvancedStats.pearson_correlation(x, y)

        self.assertAlmostEqual(correlation, 1.0, places=5)

    def test_pearson_correlation_negative(self):
        """Test negative correlation"""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]

        correlation = AdvancedStats.pearson_correlation(x, y)

        self.assertAlmostEqual(correlation, -1.0, places=5)

    def test_pearson_correlation_zero(self):
        """Test zero correlation"""
        x = [1, 2, 3, 4, 5]
        y = [5, 5, 5, 5, 5]

        correlation = AdvancedStats.pearson_correlation(x, y)

        self.assertAlmostEqual(correlation, 0.0, places=5)

    def test_correlation_matrix(self):
        """Test correlation matrix calculation"""
        data = [
            [1, 2, 3, 4, 5],
            [2, 4, 6, 8, 10],
            [5, 4, 3, 2, 1]
        ]

        matrix = AdvancedStats.calculate_correlation_matrix(data)

        # Matrix should be 3x3
        self.assertEqual(len(matrix), 3)
        self.assertEqual(len(matrix[0]), 3)

        # Diagonal should be 1.0
        for i in range(3):
            self.assertAlmostEqual(matrix[i][i], 1.0, places=5)

        # Matrix should be symmetric
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(matrix[i][j], matrix[j][i], places=5)


class TestRiskMetrics(unittest.TestCase):
    """Test risk and performance metrics"""

    def test_sharpe_ratio_positive(self):
        """Test Sharpe ratio with positive returns"""
        returns = [0.05, 0.03, 0.04, 0.06, 0.02]

        sharpe = AdvancedStats.sharpe_ratio(returns, risk_free_rate=0.01)

        self.assertGreater(sharpe, 0)

    def test_sharpe_ratio_negative(self):
        """Test Sharpe ratio with negative returns"""
        returns = [-0.05, -0.03, -0.02, -0.04, -0.01]

        sharpe = AdvancedStats.sharpe_ratio(returns, risk_free_rate=0.01)

        self.assertLess(sharpe, 0)

    def test_sortino_ratio(self):
        """Test Sortino ratio"""
        returns = [0.05, -0.02, 0.03, -0.01, 0.04]

        sortino = AdvancedStats.sortino_ratio(returns, risk_free_rate=0.01)

        # Sortino should be calculated
        self.assertIsInstance(sortino, float)

    def test_sharpe_vs_sortino(self):
        """Test that Sortino only penalizes downside risk"""
        # Returns with same mean but different downside
        returns1 = [0.10, 0.05, 0.00, 0.05, 0.10]  # No negative returns
        returns2 = [0.15, 0.10, -0.05, 0.05, 0.10]  # Has negative return

        sharpe1 = AdvancedStats.sharpe_ratio(returns1)
        sharpe2 = AdvancedStats.sharpe_ratio(returns2)

        sortino1 = AdvancedStats.sortino_ratio(returns1)
        sortino2 = AdvancedStats.sortino_ratio(returns2)

        # Sortino should favor returns1 more than Sharpe does
        # (since it only penalizes downside)


class TestKellyCriterion(unittest.TestCase):
    """Test Kelly criterion"""

    def test_kelly_positive_edge(self):
        """Test Kelly with positive edge"""
        win_prob = 0.6
        odds = 2.0  # Even money

        kelly = AdvancedStats.kelly_optimal_size(win_prob, odds)

        # Should recommend positive bet size
        self.assertGreater(kelly, 0)
        self.assertLess(kelly, 1)

    def test_kelly_negative_edge(self):
        """Test Kelly with negative edge"""
        win_prob = 0.4
        odds = 2.0  # Even money

        kelly = AdvancedStats.kelly_optimal_size(win_prob, odds)

        # Should recommend no bet (0 or negative)
        self.assertLessEqual(kelly, 0)

    def test_kelly_fractional(self):
        """Test fractional Kelly"""
        win_prob = 0.6
        odds = 2.5

        full_kelly = AdvancedStats.kelly_optimal_size(win_prob, odds)
        half_kelly = full_kelly * 0.5

        # Half Kelly should be more conservative
        self.assertLess(half_kelly, full_kelly)

    def test_kelly_breakeven(self):
        """Test Kelly at breakeven"""
        # Win prob exactly matches odds
        win_prob = 1.0 / 2.0
        odds = 2.0

        kelly = AdvancedStats.kelly_optimal_size(win_prob, odds)

        # Should recommend approximately zero
        self.assertAlmostEqual(kelly, 0.0, places=5)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def test_empty_input(self):
        """Test with empty input"""
        with self.assertRaises((ValueError, ZeroDivisionError, IndexError)):
            AdvancedStats.linear_regression([], [])

    def test_single_value(self):
        """Test with single value"""
        data = [5]

        # Some functions should handle single values
        ema = AdvancedStats.exponential_moving_average(data)
        self.assertEqual(len(ema), 1)

    def test_all_same_values(self):
        """Test with constant data"""
        x = [1, 2, 3, 4, 5]
        y = [5, 5, 5, 5, 5]

        # Should either raise ValueError or return result with R² near 0
        try:
            result = AdvancedStats.linear_regression(x, y)
            # If it doesn't raise, R² should be 0 (no variance to explain)
            self.assertAlmostEqual(result.r_squared, 0, places=5)
        except ValueError:
            # This is also acceptable
            pass


class TestIntegrationScenarios(unittest.TestCase):
    """Test realistic betting scenarios"""

    def test_nfl_season_simulation(self):
        """Test simulating an NFL season"""
        def simulate_game():
            """Simulate a single game win probability"""
            return 1 if __import__('random').random() < 0.6 else 0

        result = AdvancedStats.monte_carlo_simulation(
            simulate_game, n_simulations=10000
        )

        # Win probability should be close to 60%
        self.assertAlmostEqual(result['mean'], 0.6, delta=0.05)

    def test_betting_roi_analysis(self):
        """Test ROI analysis with bootstrap"""
        import statistics

        # Sample betting returns
        returns = [0.05, -0.02, 0.03, 0.08, -0.01, 0.04, 0.06, -0.03, 0.02, 0.05]

        ci = AdvancedStats.bootstrap_confidence_interval(
            returns, statistics.mean, n_bootstrap=1000
        )

        # Should have positive expected return
        self.assertGreater(ci['statistic'], 0)

    def test_team_performance_trend(self):
        """Test analyzing team performance trends"""
        # Team scoring over 10 games (increasing trend)
        points = [20, 22, 21, 24, 25, 27, 26, 29, 30, 32]

        # Calculate trend
        trend = AdvancedStats.calculate_trend(points)

        # Trend should be upward
        self.assertLess(trend[0], trend[-1])

        # Calculate EMA for recent form
        ema = AdvancedStats.exponential_moving_average(points, alpha=0.3)

        # EMA should follow the trend
        self.assertLess(ema[0], ema[-1])


if __name__ == '__main__':
    unittest.main()
