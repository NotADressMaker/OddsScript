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

# Import model builder
from lib.model_builder import Model, ModelBuilder, DataHelper

# Import sport-specific models and features
from lib.sport_models import (
    NBAModels, NFLModels, NHLModels, MLBModels,
    CollegeFootballModels, CollegeBasketballModels,
    SoccerModels, HorseRacingModels,
    get_sport_model
)
from lib.sport_features import (
    NBAFeatures, NFLFeatures, NHLFeatures, MLBFeatures,
    CollegeFootballFeatures, CollegeBasketballFeatures,
    SoccerFeatures, HorseRacingFeatures,
    get_sport_features
)

__all__ = [
    # Simplified API (recommended for beginners)
    'SBL',
    'Bet',
    'Compare',

    # ML Model Builder (easy model creation)
    'Model',
    'ModelBuilder',
    'DataHelper',

    # Sport-Specific Models
    'NBAModels',
    'NFLModels',
    'NHLModels',
    'MLBModels',
    'CollegeFootballModels',
    'CollegeBasketballModels',
    'SoccerModels',
    'HorseRacingModels',
    'get_sport_model',

    # Sport-Specific Features
    'NBAFeatures',
    'NFLFeatures',
    'NHLFeatures',
    'MLBFeatures',
    'CollegeFootballFeatures',
    'CollegeBasketballFeatures',
    'SoccerFeatures',
    'HorseRacingFeatures',
    'get_sport_features',

    # Advanced statistics
    'AdvancedStats',

    # Machine learning
    'DecisionTree',
    'RandomForest',
    'NeuralNetwork',
    'FeatureEngineering',
    'ModelValidation',
]
