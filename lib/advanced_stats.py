#!/usr/bin/env python3
"""
Advanced Statistics Library for Sports Betting

Sophisticated statistical techniques including:
- Machine learning models (regression, classification)
- Time series analysis
- Bayesian inference
- Monte Carlo simulation
- Bootstrap resampling
- Ensemble methods
- Feature engineering
- Model evaluation
"""

import math
import random
from typing import List, Tuple, Dict, Optional, Callable, Any
from dataclasses import dataclass
from collections import defaultdict
import statistics


@dataclass
class RegressionResult:
    """Results from regression analysis"""
    coefficients: List[float]
    intercept: float
    r_squared: float
    predictions: List[float]
    residuals: List[float]
    mse: float
    rmse: float
    mae: float


@dataclass
class TimeSeriesResult:
    """Results from time series analysis"""
    predictions: List[float]
    trend: List[float]
    seasonal: Optional[List[float]]
    residuals: List[float]
    forecast: List[float]


@dataclass
class BayesianResult:
    """Results from Bayesian analysis"""
    posterior_probability: float
    prior_probability: float
    likelihood: float
    evidence: float
    updated_beliefs: Dict[str, float]


class AdvancedStats:
    """Advanced statistical methods for sports betting analytics"""

    @staticmethod
    def linear_regression(x: List[float], y: List[float]) -> RegressionResult:
        """
        Simple linear regression: y = mx + b

        Args:
            x: Independent variable
            y: Dependent variable

        Returns:
            RegressionResult with coefficients and metrics
        """
        if len(x) != len(y):
            raise ValueError("x and y must have same length")

        if len(x) < 2:
            raise ValueError("Need at least 2 points for regression")

        n = len(x)
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        # Calculate slope (m)
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            raise ValueError("No variance in x values")

        slope = numerator / denominator
        intercept = mean_y - slope * mean_x

        # Make predictions
        predictions = [slope * x_i + intercept for x_i in x]
        residuals = [y[i] - predictions[i] for i in range(n)]

        # Calculate R-squared
        ss_res = sum(r ** 2 for r in residuals)
        ss_tot = sum((y_i - mean_y) ** 2 for y_i in y)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Error metrics
        mse = ss_res / n
        rmse = math.sqrt(mse)
        mae = sum(abs(r) for r in residuals) / n

        return RegressionResult(
            coefficients=[slope],
            intercept=intercept,
            r_squared=r_squared,
            predictions=predictions,
            residuals=residuals,
            mse=mse,
            rmse=rmse,
            mae=mae
        )

    @staticmethod
    def multiple_regression(X: List[List[float]], y: List[float]) -> RegressionResult:
        """
        Multiple linear regression: y = b0 + b1*x1 + b2*x2 + ... + bn*xn

        Uses normal equations: β = (X'X)^-1 X'y

        Args:
            X: Matrix of independent variables (samples x features)
            y: Dependent variable

        Returns:
            RegressionResult with coefficients and metrics
        """
        if len(X) != len(y):
            raise ValueError("X and y must have same number of samples")

        n_samples = len(X)
        n_features = len(X[0])

        # Add intercept column
        X_with_intercept = [[1.0] + row for row in X]

        # Calculate (X'X)^-1 X'y using simplified approach
        # For production, would use numpy or scipy
        XtX = [[0.0] * (n_features + 1) for _ in range(n_features + 1)]
        Xty = [0.0] * (n_features + 1)

        # Calculate X'X and X'y
        for i in range(n_samples):
            for j in range(n_features + 1):
                Xty[j] += X_with_intercept[i][j] * y[i]
                for k in range(n_features + 1):
                    XtX[j][k] += X_with_intercept[i][j] * X_with_intercept[i][k]

        # Solve using Gaussian elimination (simplified)
        coefficients = AdvancedStats._gaussian_elimination(XtX, Xty)

        intercept = coefficients[0]
        coefs = coefficients[1:]

        # Make predictions
        predictions = [intercept + sum(coefs[j] * X[i][j] for j in range(n_features))
                      for i in range(n_samples)]

        residuals = [y[i] - predictions[i] for i in range(n_samples)]

        # Calculate R-squared
        mean_y = statistics.mean(y)
        ss_res = sum(r ** 2 for r in residuals)
        ss_tot = sum((y_i - mean_y) ** 2 for y_i in y)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

        # Error metrics
        mse = ss_res / n_samples
        rmse = math.sqrt(mse)
        mae = sum(abs(r) for r in residuals) / n_samples

        return RegressionResult(
            coefficients=coefs,
            intercept=intercept,
            r_squared=r_squared,
            predictions=predictions,
            residuals=residuals,
            mse=mse,
            rmse=rmse,
            mae=mae
        )

    @staticmethod
    def _gaussian_elimination(A: List[List[float]], b: List[float]) -> List[float]:
        """Solve Ax = b using Gaussian elimination"""
        n = len(b)
        # Create augmented matrix
        aug = [A[i] + [b[i]] for i in range(n)]

        # Forward elimination
        for i in range(n):
            # Find pivot
            max_row = i
            for k in range(i + 1, n):
                if abs(aug[k][i]) > abs(aug[max_row][i]):
                    max_row = k

            aug[i], aug[max_row] = aug[max_row], aug[i]

            # Make all rows below this one 0 in current column
            for k in range(i + 1, n):
                if aug[i][i] == 0:
                    continue
                factor = aug[k][i] / aug[i][i]
                for j in range(i, n + 1):
                    aug[k][j] -= factor * aug[i][j]

        # Back substitution
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = aug[i][n]
            for j in range(i + 1, n):
                x[i] -= aug[i][j] * x[j]
            if aug[i][i] != 0:
                x[i] /= aug[i][i]

        return x

    @staticmethod
    def logistic_regression_simple(x: List[float], y: List[int],
                                   learning_rate: float = 0.01,
                                   iterations: int = 1000) -> Tuple[float, float]:
        """
        Simple logistic regression using gradient descent

        Args:
            x: Independent variable
            y: Binary dependent variable (0 or 1)
            learning_rate: Learning rate for gradient descent
            iterations: Number of iterations

        Returns:
            Tuple of (slope, intercept)
        """
        if len(x) != len(y):
            raise ValueError("x and y must have same length")

        # Initialize parameters
        theta0 = 0.0  # intercept
        theta1 = 0.0  # slope

        n = len(x)

        # Gradient descent
        for _ in range(iterations):
            predictions = [1 / (1 + math.exp(-(theta0 + theta1 * x_i))) for x_i in x]

            # Calculate gradients
            grad0 = sum(predictions[i] - y[i] for i in range(n)) / n
            grad1 = sum((predictions[i] - y[i]) * x[i] for i in range(n)) / n

            # Update parameters
            theta0 -= learning_rate * grad0
            theta1 -= learning_rate * grad1

        return theta1, theta0

    @staticmethod
    def exponential_moving_average(data: List[float], alpha: float = 0.3) -> List[float]:
        """
        Calculate exponential moving average (EMA)

        EMA gives more weight to recent observations

        Args:
            data: Time series data
            alpha: Smoothing factor (0 < alpha <= 1)

        Returns:
            List of EMA values
        """
        if not data:
            return []

        if not 0 < alpha <= 1:
            raise ValueError("Alpha must be between 0 and 1")

        ema = [data[0]]

        for i in range(1, len(data)):
            ema.append(alpha * data[i] + (1 - alpha) * ema[i - 1])

        return ema

    @staticmethod
    def weighted_moving_average(data: List[float], window: int) -> List[float]:
        """
        Calculate weighted moving average (WMA)

        Recent observations get linearly higher weights

        Args:
            data: Time series data
            window: Window size

        Returns:
            List of WMA values
        """
        if window <= 0:
            raise ValueError("Window must be positive")

        wma = []
        weights = list(range(1, window + 1))
        weight_sum = sum(weights)

        for i in range(len(data)):
            if i < window - 1:
                wma.append(None)
            else:
                weighted_sum = sum(data[i - window + 1 + j] * weights[j]
                                 for j in range(window))
                wma.append(weighted_sum / weight_sum)

        return wma

    @staticmethod
    def calculate_trend(data: List[float], method: str = 'linear') -> List[float]:
        """
        Calculate trend component of time series

        Args:
            data: Time series data
            method: 'linear' or 'polynomial'

        Returns:
            Trend values
        """
        x = list(range(len(data)))

        if method == 'linear':
            result = AdvancedStats.linear_regression(x, data)
            return result.predictions
        else:
            # For polynomial, use moving average as simple trend
            window = min(len(data) // 4, 7)
            return AdvancedStats.moving_average(data, window)

    @staticmethod
    def moving_average(data: List[float], window: int) -> List[float]:
        """Simple moving average"""
        if window <= 0:
            raise ValueError("Window must be positive")

        ma = []
        for i in range(len(data)):
            if i < window - 1:
                ma.append(None)
            else:
                ma.append(sum(data[i - window + 1:i + 1]) / window)

        return ma

    @staticmethod
    def bayesian_update(prior: float, likelihood: float, evidence: float) -> float:
        """
        Bayesian probability update using Bayes' theorem

        P(H|E) = P(E|H) * P(H) / P(E)

        Args:
            prior: Prior probability P(H)
            likelihood: Likelihood P(E|H)
            evidence: Evidence P(E)

        Returns:
            Posterior probability P(H|E)
        """
        if not 0 <= prior <= 1:
            raise ValueError("Prior must be between 0 and 1")

        if evidence == 0:
            raise ValueError("Evidence cannot be zero")

        posterior = (likelihood * prior) / evidence
        return min(1.0, max(0.0, posterior))

    @staticmethod
    def bayesian_win_probability(wins: int, losses: int,
                                 prior_alpha: float = 1.0,
                                 prior_beta: float = 1.0) -> Dict[str, float]:
        """
        Calculate Bayesian win probability using Beta distribution

        Beta distribution is conjugate prior for binomial likelihood

        Args:
            wins: Number of wins
            losses: Number of losses
            prior_alpha: Prior alpha parameter (pseudo-wins)
            prior_beta: Prior beta parameter (pseudo-losses)

        Returns:
            Dictionary with probability estimates
        """
        # Update parameters with observed data
        posterior_alpha = prior_alpha + wins
        posterior_beta = prior_beta + losses

        # Mean of Beta distribution is alpha / (alpha + beta)
        mean_prob = posterior_alpha / (posterior_alpha + posterior_beta)

        # Mode of Beta distribution (most likely value)
        if posterior_alpha > 1 and posterior_beta > 1:
            mode_prob = (posterior_alpha - 1) / (posterior_alpha + posterior_beta - 2)
        else:
            mode_prob = mean_prob

        # Credible interval (simplified 95%)
        # For exact calculation would use beta quantile function
        variance = (posterior_alpha * posterior_beta) / \
                  ((posterior_alpha + posterior_beta) ** 2 *
                   (posterior_alpha + posterior_beta + 1))
        std_dev = math.sqrt(variance)
        ci_lower = max(0, mean_prob - 1.96 * std_dev)
        ci_upper = min(1, mean_prob + 1.96 * std_dev)

        return {
            'mean_probability': mean_prob,
            'mode_probability': mode_prob,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'posterior_alpha': posterior_alpha,
            'posterior_beta': posterior_beta
        }

    @staticmethod
    def monte_carlo_simulation(simulation_func: Callable, n_simulations: int = 10000,
                              **kwargs) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation

        Args:
            simulation_func: Function that returns a single simulation result
            n_simulations: Number of simulations to run
            **kwargs: Parameters to pass to simulation function

        Returns:
            Dictionary with simulation results and statistics
        """
        results = []

        for _ in range(n_simulations):
            result = simulation_func(**kwargs)
            results.append(result)

        mean_result = statistics.mean(results)
        median_result = statistics.median(results)
        std_dev = statistics.stdev(results) if len(results) > 1 else 0

        # Percentiles
        sorted_results = sorted(results)
        p5 = sorted_results[int(0.05 * n_simulations)]
        p25 = sorted_results[int(0.25 * n_simulations)]
        p75 = sorted_results[int(0.75 * n_simulations)]
        p95 = sorted_results[int(0.95 * n_simulations)]

        return {
            'results': results,
            'mean': mean_result,
            'median': median_result,
            'std_dev': std_dev,
            'min': min(results),
            'max': max(results),
            'p5': p5,
            'p25': p25,
            'p75': p75,
            'p95': p95,
            'n_simulations': n_simulations
        }

    @staticmethod
    def bootstrap_confidence_interval(data: List[float], statistic_func: Callable,
                                     n_bootstrap: int = 1000,
                                     confidence_level: float = 0.95) -> Dict[str, float]:
        """
        Calculate confidence interval using bootstrap resampling

        Args:
            data: Original data
            statistic_func: Function to calculate statistic (e.g., mean, median)
            n_bootstrap: Number of bootstrap samples
            confidence_level: Confidence level (e.g., 0.95 for 95%)

        Returns:
            Dictionary with statistic and confidence interval
        """
        if not data:
            raise ValueError("Data cannot be empty")

        bootstrap_statistics = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            sample = [random.choice(data) for _ in range(len(data))]
            stat = statistic_func(sample)
            bootstrap_statistics.append(stat)

        bootstrap_statistics.sort()

        # Calculate confidence interval
        alpha = 1 - confidence_level
        lower_idx = int(alpha / 2 * n_bootstrap)
        upper_idx = int((1 - alpha / 2) * n_bootstrap)

        original_stat = statistic_func(data)

        return {
            'statistic': original_stat,
            'ci_lower': bootstrap_statistics[lower_idx],
            'ci_upper': bootstrap_statistics[upper_idx],
            'bootstrap_mean': statistics.mean(bootstrap_statistics),
            'bootstrap_std': statistics.stdev(bootstrap_statistics) if n_bootstrap > 1 else 0,
            'confidence_level': confidence_level
        }

    @staticmethod
    def permutation_test(group1: List[float], group2: List[float],
                        n_permutations: int = 10000) -> Dict[str, float]:
        """
        Permutation test to determine if two groups are significantly different

        Args:
            group1: First group of observations
            group2: Second group of observations
            n_permutations: Number of permutations

        Returns:
            Dictionary with test results
        """
        if not group1 or not group2:
            raise ValueError("Groups cannot be empty")

        # Calculate observed difference
        observed_diff = statistics.mean(group1) - statistics.mean(group2)

        # Combine groups
        combined = group1 + group2
        n1 = len(group1)

        # Count extreme differences
        extreme_count = 0

        for _ in range(n_permutations):
            # Shuffle and split
            shuffled = combined.copy()
            random.shuffle(shuffled)

            perm_group1 = shuffled[:n1]
            perm_group2 = shuffled[n1:]

            perm_diff = statistics.mean(perm_group1) - statistics.mean(perm_group2)

            if abs(perm_diff) >= abs(observed_diff):
                extreme_count += 1

        p_value = extreme_count / n_permutations

        return {
            'observed_difference': observed_diff,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'n_permutations': n_permutations
        }

    @staticmethod
    def calculate_correlation_matrix(data: List[List[float]]) -> List[List[float]]:
        """
        Calculate correlation matrix for multiple variables

        Args:
            data: List of variables (each variable is a list of observations)

        Returns:
            Correlation matrix
        """
        n_vars = len(data)

        if n_vars == 0:
            return []

        # Check all variables have same length
        length = len(data[0])
        if not all(len(var) == length for var in data):
            raise ValueError("All variables must have same length")

        corr_matrix = [[0.0] * n_vars for _ in range(n_vars)]

        for i in range(n_vars):
            for j in range(n_vars):
                if i == j:
                    corr_matrix[i][j] = 1.0
                else:
                    corr_matrix[i][j] = AdvancedStats.pearson_correlation(data[i], data[j])

        return corr_matrix

    @staticmethod
    def pearson_correlation(x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y):
            raise ValueError("Lists must have same length")

        if len(x) < 2:
            return 0.0

        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
        denominator = math.sqrt(
            sum((x_i - mean_x) ** 2 for x_i in x) *
            sum((y_i - mean_y) ** 2 for y_i in y)
        )

        if denominator == 0:
            return 0.0

        return numerator / denominator

    @staticmethod
    def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sharpe ratio (risk-adjusted return)

        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate of return

        Returns:
            Sharpe ratio
        """
        if not returns:
            return 0.0

        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess = statistics.mean(excess_returns)
        std_excess = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 0

        if std_excess == 0:
            return 0.0

        return mean_excess / std_excess

    @staticmethod
    def sortino_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
        """
        Calculate Sortino ratio (only considers downside risk)

        Args:
            returns: List of returns
            risk_free_rate: Risk-free rate of return

        Returns:
            Sortino ratio
        """
        if not returns:
            return 0.0

        excess_returns = [r - risk_free_rate for r in returns]
        mean_excess = statistics.mean(excess_returns)

        # Downside deviation (only negative returns)
        downside_returns = [r for r in excess_returns if r < 0]

        if not downside_returns:
            return float('inf')  # No downside risk

        downside_deviation = math.sqrt(sum(r ** 2 for r in downside_returns) / len(downside_returns))

        if downside_deviation == 0:
            return float('inf')

        return mean_excess / downside_deviation

    @staticmethod
    def kelly_optimal_size(win_prob: float, odds: float) -> float:
        """
        Calculate optimal Kelly Criterion bet size

        Args:
            win_prob: Probability of winning
            odds: Decimal odds

        Returns:
            Optimal fraction of bankroll to bet
        """
        if not 0 <= win_prob <= 1:
            raise ValueError("Win probability must be between 0 and 1")

        if odds <= 1:
            raise ValueError("Odds must be greater than 1")

        # Kelly formula: (bp - q) / b
        # where b = odds - 1, p = win_prob, q = 1 - win_prob
        b = odds - 1
        p = win_prob
        q = 1 - win_prob

        kelly = (b * p - q) / b

        return max(0, kelly)  # Don't bet negative amounts


if __name__ == '__main__':
    # Example usage
    print("Advanced Statistics Library - Examples")
    print("=" * 70)

    # 1. Linear Regression
    print("\n1. Linear Regression (Points vs Elo Rating)")
    elo_ratings = [1500, 1550, 1600, 1650, 1700, 1750]
    points_scored = [20, 22, 24, 27, 29, 31]

    reg_result = AdvancedStats.linear_regression(elo_ratings, points_scored)
    print(f"Slope: {reg_result.coefficients[0]:.4f}")
    print(f"Intercept: {reg_result.intercept:.2f}")
    print(f"R-squared: {reg_result.r_squared:.4f}")
    print(f"RMSE: {reg_result.rmse:.2f}")

    # 2. Bayesian Win Probability
    print("\n2. Bayesian Win Probability")
    bayes_result = AdvancedStats.bayesian_win_probability(wins=8, losses=4)
    print(f"Estimated Win Probability: {bayes_result['mean_probability']:.1%}")
    print(f"95% Credible Interval: [{bayes_result['ci_lower']:.1%}, {bayes_result['ci_upper']:.1%}]")

    # 3. Monte Carlo Simulation
    print("\n3. Monte Carlo Simulation (Expected Wins)")

    def simulate_season(games=16, win_prob=0.6):
        """Simulate a season"""
        wins = sum(1 for _ in range(games) if random.random() < win_prob)
        return wins

    mc_result = AdvancedStats.monte_carlo_simulation(
        simulate_season,
        n_simulations=10000,
        games=16,
        win_prob=0.6
    )
    print(f"Expected Wins: {mc_result['mean']:.1f}")
    print(f"90% Range: {mc_result['p5']:.1f} to {mc_result['p95']:.1f} wins")

    # 4. Bootstrap Confidence Interval
    print("\n4. Bootstrap Confidence Interval (ROI)")
    roi_data = [5.2, 8.1, -2.3, 12.4, 6.7, 9.2, 3.5, 11.1, 7.8, 4.9]
    bootstrap = AdvancedStats.bootstrap_confidence_interval(
        roi_data,
        statistics.mean,
        n_bootstrap=1000
    )
    print(f"Mean ROI: {bootstrap['statistic']:.1f}%")
    print(f"95% CI: [{bootstrap['ci_lower']:.1f}%, {bootstrap['ci_upper']:.1f}%]")

    # 5. Exponential Moving Average
    print("\n5. Exponential Moving Average (Trend)")
    scores = [24, 27, 23, 28, 31, 29, 32, 30, 35, 33]
    ema = AdvancedStats.exponential_moving_average(scores, alpha=0.3)
    print(f"Original: {scores}")
    print(f"EMA: {[f'{x:.1f}' for x in ema]}")

    print("\nAll examples completed successfully!")
