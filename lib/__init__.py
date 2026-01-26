"""
SportsBetLang - Advanced Sports Betting Analytics Library

A comprehensive Python library for sports betting analysis with:
- Advanced statistics (Bayesian inference, Monte Carlo, regression)
- Machine learning models (Random Forests, Decision Trees, Neural Networks)
- Sport-specific analytics (NFL, NBA, MLB, NHL, CFB, CBB, Soccer, Horse Racing)
- Expected value calculations and Kelly Criterion
- Data storage and management

Quick Start:
    >>> from lib.simple_api import SBL, Bet, Compare
    >>>
    >>> # Calculate Kelly bet size
    >>> kelly = SBL.kelly(win_prob=0.55, odds=2.0)
    >>>
    >>> # Analyze a bet
    >>> bet = Bet(100).at_odds(2.1).with_probability(0.58)
    >>> bet.print_summary()
"""

__version__ = "0.1.0"

# Import key modules for easier access
from lib.advanced_stats import AdvancedStats
from lib.ml_models import (
    DecisionTree,
    RandomForest,
    NeuralNetwork,
    FeatureEngineering,
    ModelValidation
)

# Import simplified API
from lib.simple_api import SBL, Bet, Compare

__all__ = [
    # Simplified API (recommended for beginners)
    'SBL',
    'Bet',
    'Compare',

    # Advanced statistics
    'AdvancedStats',

    # Machine learning
    'DecisionTree',
    'RandomForest',
    'NeuralNetwork',
    'FeatureEngineering',
    'ModelValidation',
]
