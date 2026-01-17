"""
Analytical libraries for sports betting.

Contains refactored libraries using oddsscript.common utilities:
- Statistics (✓ migrated)
- Backtesting (pending)
- CLV tracking (pending)
- Variance calculations (pending)
- Poisson models (pending)
- Elo ratings (pending)
- Expected goals (pending)
- Correlation analysis (pending)
- Regression analysis (pending)
- Multi-outcome Kelly (pending)
"""

from sportsbetlang.analytics.statistics import (
    # Basic stats
    mean, median, mode, variance, std_dev, percentile,
    correlation, z_score, moving_average, weighted_average,

    # Betting stats
    win_rate, units_won, roi, sharpe_ratio, max_drawdown,
    profit_factor, expectancy, confidence_interval,
    calculate_breakeven_rate, kelly_growth_rate
)

__all__ = [
    # Basic stats
    'mean', 'median', 'mode', 'variance', 'std_dev', 'percentile',
    'correlation', 'z_score', 'moving_average', 'weighted_average',

    # Betting stats
    'win_rate', 'units_won', 'roi', 'sharpe_ratio', 'max_drawdown',
    'profit_factor', 'expectancy', 'confidence_interval',
    'calculate_breakeven_rate', 'kelly_growth_rate'
]
