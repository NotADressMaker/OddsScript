"""
Betting strategies for OddsScript.

Provides pluggable betting strategies using the StrategyRegistry:
- Kelly Criterion (quarter, full, conservative)
- Flat betting (fixed amount)
- Percentage betting (% of bankroll)
- Unit betting (unit-based)

All strategies auto-register via decorators.
"""

from oddsscript.strategies.base import (
    BettingStrategy,
    BetRecommendation,
    BetAction,
    StrategyRegistry,
    register_strategy
)

# Import strategies to auto-register them
from oddsscript.strategies.kelly import (
    KellyStrategy,
    FullKellyStrategy,
    ConservativeKellyStrategy
)

from oddsscript.strategies.flat import (
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
