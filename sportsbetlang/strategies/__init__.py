"""
Betting strategies for SportsBetLang.

Provides pluggable betting strategies using the StrategyRegistry:
- Kelly Criterion (quarter, full, conservative)
- Flat betting (fixed amount)
- Percentage betting (% of bankroll)
- Unit betting (unit-based)

All strategies auto-register via decorators.
"""

from sportsbetlang.strategies.base import (
    BettingStrategy,
    BetRecommendation,
    BetAction,
    StrategyRegistry,
    register_strategy
)

# Import strategies to auto-register them
from sportsbetlang.strategies.kelly import (
    KellyStrategy,
    FullKellyStrategy,
    ConservativeKellyStrategy
)

from sportsbetlang.strategies.flat import (
    FlatBettingStrategy,
    PercentageBettingStrategy,
    UnitBettingStrategy
)

__all__ = [
    # Base classes
    'BettingStrategy',
    'BetRecommendation',
    'BetAction',
    'StrategyRegistry',
    'register_strategy',

    # Kelly strategies
    'KellyStrategy',
    'FullKellyStrategy',
    'ConservativeKellyStrategy',

    # Flat strategies
    'FlatBettingStrategy',
    'PercentageBettingStrategy',
    'UnitBettingStrategy',
]
