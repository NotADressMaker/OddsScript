"""
Analytical libraries for sports betting.

Contains refactored libraries using oddsscript.common utilities:
- Statistics (✓ migrated)
- Backtesting (pending)
- CLV tracking (pending)
- Variance calculations (pending)
- Poisson models (✓ migrated)
- Elo ratings (✓ migrated)
- State space models (✓ migrated)
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
from sportsbetlang.analytics.poisson import (
    poisson_probability,
    poisson_cumulative,
    calculate_match_probabilities,
    calculate_total_probabilities,
    calculate_correct_score_probabilities,
    calculate_btts_probability,
    simulate_poisson_event,
    simulate_match,
    PoissonModel,
)
from sportsbetlang.analytics.elo import (
    TeamRating,
    EloRatingSystem,
)
from sportsbetlang.analytics.state_space import (
    KalmanState,
    LocalLevelModel,
)
from sportsbetlang.analytics.repro import ensure_random_state, set_global_seed
from sportsbetlang.analytics.registry import ModelRegistry

__all__ = [
    # Basic stats
    'mean', 'median', 'mode', 'variance', 'std_dev', 'percentile',
    'correlation', 'z_score', 'moving_average', 'weighted_average',

    # Betting stats
    'win_rate', 'units_won', 'roi', 'sharpe_ratio', 'max_drawdown',
    'profit_factor', 'expectancy', 'confidence_interval',
    'calculate_breakeven_rate', 'kelly_growth_rate',

    # Poisson models
    'poisson_probability', 'poisson_cumulative',
    'calculate_match_probabilities', 'calculate_total_probabilities',
    'calculate_correct_score_probabilities', 'calculate_btts_probability',
    'simulate_poisson_event', 'simulate_match', 'PoissonModel',

    # Elo ratings
    'TeamRating', 'EloRatingSystem',

    # State space models
    'KalmanState', 'LocalLevelModel',

    # Reproducibility
    'ensure_random_state', 'set_global_seed',
    'ModelRegistry',
]
