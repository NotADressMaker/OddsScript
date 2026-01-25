"""
SportsBetLang - Advanced Sports Betting Analytics Library

A comprehensive Python library for sports betting analysis with:
- Advanced statistics (Bayesian inference, Monte Carlo, regression)
- Machine learning models (Random Forests, Decision Trees, Neural Networks)
- Sport-specific analytics (NFL, NBA, MLB, NHL, CFB, CBB, Soccer, Horse Racing)
- Expected value calculations and Kelly Criterion
- Data storage and management
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

__all__ = [
    'AdvancedStats',
    'DecisionTree',
    'RandomForest',
    'NeuralNetwork',
    'FeatureEngineering',
    'ModelValidation',
]
