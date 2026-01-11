"""
OddsScript Standard Library - Statistics Module

Provides statistical functions useful for sports betting analysis.
"""

from typing import List, Union
import math


def mean(values: List[Union[int, float]]) -> float:
    """Calculate the arithmetic mean of a list of numbers"""
    if not values:
        raise ValueError("Cannot calculate mean of empty list")
    return sum(values) / len(values)


def median(values: List[Union[int, float]]) -> float:
    """Calculate the median of a list of numbers"""
    if not values:
        raise ValueError("Cannot calculate median of empty list")
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
    else:
        return sorted_values[n // 2]


def mode(values: List[Union[int, float]]) -> Union[int, float]:
    """Find the most common value in a list"""
    if not values:
        raise ValueError("Cannot calculate mode of empty list")
    from collections import Counter
    counts = Counter(values)
    return counts.most_common(1)[0][0]


def variance(values: List[Union[int, float]], sample: bool = True) -> float:
    """Calculate the variance of a list of numbers"""
    if not values:
        raise ValueError("Cannot calculate variance of empty list")
    avg = mean(values)
    squared_diffs = [(x - avg) ** 2 for x in values]
    divisor = len(values) - 1 if sample else len(values)
    if divisor == 0:
        raise ValueError("Sample variance undefined for single value")
    return sum(squared_diffs) / divisor


def std_dev(values: List[Union[int, float]], sample: bool = True) -> float:
    """Calculate the standard deviation of a list of numbers"""
    return math.sqrt(variance(values, sample))


def percentile(values: List[Union[int, float]], p: float) -> float:
    """Calculate the p-th percentile of a list of numbers"""
    if not 0 <= p <= 100:
        raise ValueError("Percentile must be between 0 and 100")
    if not values:
        raise ValueError("Cannot calculate percentile of empty list")

    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * (p / 100)
    floor_k = math.floor(k)
    ceil_k = math.ceil(k)

    if floor_k == ceil_k:
        return sorted_values[int(k)]

    d0 = sorted_values[int(floor_k)] * (ceil_k - k)
    d1 = sorted_values[int(ceil_k)] * (k - floor_k)
    return d0 + d1


def correlation(x_values: List[float], y_values: List[float]) -> float:
    """Calculate Pearson correlation coefficient between two lists"""
    if len(x_values) != len(y_values):
        raise ValueError("Lists must have the same length")
    if len(x_values) < 2:
        raise ValueError("Need at least 2 values for correlation")

    n = len(x_values)
    mean_x = mean(x_values)
    mean_y = mean(y_values)

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
    denominator = math.sqrt(
        sum((x - mean_x) ** 2 for x in x_values) *
        sum((y - mean_y) ** 2 for y in y_values)
    )

    if denominator == 0:
        return 0

    return numerator / denominator


def z_score(value: float, values: List[float]) -> float:
    """Calculate the z-score of a value given a dataset"""
    avg = mean(values)
    sd = std_dev(values)
    if sd == 0:
        raise ValueError("Standard deviation is zero")
    return (value - avg) / sd


def moving_average(values: List[float], window: int) -> List[float]:
    """Calculate moving average with specified window size"""
    if window <= 0:
        raise ValueError("Window must be positive")
    if window > len(values):
        raise ValueError("Window cannot be larger than dataset")

    result = []
    for i in range(len(values) - window + 1):
        window_values = values[i:i + window]
        result.append(mean(window_values))
    return result


def weighted_average(values: List[float], weights: List[float]) -> float:
    """Calculate weighted average"""
    if len(values) != len(weights):
        raise ValueError("Values and weights must have the same length")
    if not values:
        raise ValueError("Cannot calculate weighted average of empty list")

    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("Total weight cannot be zero")

    return sum(v * w for v, w in zip(values, weights)) / total_weight


# Betting-specific statistical functions

def win_rate(wins: int, losses: int) -> float:
    """Calculate win rate as a percentage"""
    total = wins + losses
    if total == 0:
        return 0.0
    return (wins / total) * 100


def units_won(wins: int, losses: int, avg_odds: float = -110, unit_size: float = 1.0) -> float:
    """Calculate total units won/lost"""
    if avg_odds > 0:
        win_amount = unit_size * (avg_odds / 100)
    else:
        win_amount = unit_size * (100 / abs(avg_odds))

    total_won = wins * win_amount
    total_lost = losses * unit_size
    return total_won - total_lost


def roi(wins: int, losses: int, avg_odds: float = -110) -> float:
    """Calculate ROI as a percentage"""
    total_bets = wins + losses
    if total_bets == 0:
        return 0.0

    units_profit = units_won(wins, losses, avg_odds)
    return (units_profit / total_bets) * 100


def sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio for betting performance"""
    if not returns:
        return 0.0

    avg_return = mean(returns)
    if len(returns) < 2:
        return 0.0

    sd = std_dev(returns)
    if sd == 0:
        return 0.0

    return (avg_return - risk_free_rate) / sd


def max_drawdown(bankroll_history: List[float]) -> float:
    """Calculate maximum drawdown from bankroll history"""
    if not bankroll_history:
        return 0.0

    peak = bankroll_history[0]
    max_dd = 0.0

    for value in bankroll_history:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak if peak > 0 else 0
        if drawdown > max_dd:
            max_dd = drawdown

    return max_dd * 100  # Return as percentage


def profit_factor(gross_wins: float, gross_losses: float) -> float:
    """Calculate profit factor (gross wins / gross losses)"""
    if gross_losses == 0:
        return float('inf') if gross_wins > 0 else 0
    return gross_wins / gross_losses


def expectancy(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Calculate expectancy (average profit per bet)"""
    loss_rate = 1 - win_rate
    return (win_rate * avg_win) - (loss_rate * avg_loss)


def confidence_interval(values: List[float], confidence: float = 0.95) -> tuple:
    """Calculate confidence interval for a dataset"""
    if len(values) < 2:
        raise ValueError("Need at least 2 values for confidence interval")

    avg = mean(values)
    sd = std_dev(values)
    n = len(values)

    # Using t-distribution approximation
    # For 95% confidence, t ≈ 1.96 for large samples
    if confidence == 0.95:
        t_value = 1.96
    elif confidence == 0.99:
        t_value = 2.576
    elif confidence == 0.90:
        t_value = 1.645
    else:
        t_value = 1.96  # default to 95%

    margin = t_value * (sd / math.sqrt(n))
    return (avg - margin, avg + margin)


# Export all functions
__all__ = [
    'mean', 'median', 'mode', 'variance', 'std_dev', 'percentile',
    'correlation', 'z_score', 'moving_average', 'weighted_average',
    'win_rate', 'units_won', 'roi', 'sharpe_ratio', 'max_drawdown',
    'profit_factor', 'expectancy', 'confidence_interval'
]
