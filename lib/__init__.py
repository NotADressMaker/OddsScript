"""
SportsBetLang - Advanced Sports Betting Analytics Library

A comprehensive Python library for sports betting analysis with:
- Advanced statistics (Bayesian inference, Monte Carlo, regression)
- Machine learning models (Random Forests, Decision Trees, Neural Networks)
- Sport-specific analytics for 9 sports:
  * NBA, NFL, NHL, MLB (Professional)
  * College Basketball (CBB), College Football (CFB) (College)
  * WNBA (Women's Professional)
  * Soccer, Horse Racing (Other)
- Expected value calculations and Kelly Criterion
- Data storage and management
- Full-stack API with REST endpoints

Quick Start:
    >>> from lib.simple_api import SBL, Bet, Compare
    >>>
    >>> # Calculate Kelly bet size
    >>> kelly = SBL.kelly(win_prob=0.55, odds=2.0)
    >>>
    >>> # Analyze a bet
    >>> bet = Bet(100).at_odds(2.1).with_probability(0.58)
    >>> bet.print_summary()
    >>>
    >>> # Quick predictions for any sport
    >>> from lib import quick_cbb_prediction, quick_wnba_prediction
    >>> cbb_prob = quick_cbb_prediction(25.5, 18.2, 20.5, 15.2)
    >>> wnba_prob = quick_wnba_prediction(105, 100, 102, 101)
    >>>
    >>> # NHL Advanced Models
    >>> from lib import NHLDecisionTree, NHLPowerRankings
    >>> tree = NHLDecisionTree()
    >>> ou_pred = tree.predict_over_under(3.2, 2.8, 2.9, 3.0, 6.5)
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
from lib.model_builder import Model, ModelBuilder, DataHelper, AdditiveModel, add_on_model

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

# Import easy sport models (simplified interface)
from lib.easy_sport_models import (
    EasySportModel,
    quick_nba_prediction,
    quick_nfl_prediction,
    quick_nhl_prediction,
    quick_mlb_prediction,
    quick_cbb_prediction,
    quick_cfb_prediction,
    quick_wnba_prediction,
    quick_soccer_btts,
    train_and_predict,
    AutoFeatures
)

# Import database
from lib.database import BettingDatabase, create_database

# Import sport-specific analytics packages
from lib.nba_analytics import NBAAnalytics, NBABettingInterface
from lib.nfl_analytics import NFLAnalytics
from lib.nhl_analytics import NHLAnalytics, NHLAdvancedAnalytics
from lib.mlb_analytics import MLBAnalytics
from lib.cbb_analytics import CBBAnalytics
from lib.cfb_analytics import CFBAnalytics
from lib.wnba_analytics import WNBAAnalytics
from lib.soccer_analytics import SoccerAnalytics
from lib.horse_racing_analytics import HorseRacingAnalyzer as HorseRacingAnalytics

# Import NHL advanced prediction models
from lib.nhl_advanced_models import (
    NHLDecisionTree,
    NHLPowerRankings,
    NHLSimilarGameModel,
    quick_nhl_decision_tree_ou,
    quick_nhl_decision_tree_ats
)

# Expert opinion consensus model
from lib.expert_opinion_model import ExpertConsensusModel, ExpertSource, ExpertOpinion
from lib.over_under_trend_model import OverUnderTrendModel, TeamTrendStats

__all__ = [
    # Simplified API (recommended for beginners)
    'SBL',
    'Bet',
    'Compare',

    # ML Model Builder (easy model creation)
    'Model',
    'ModelBuilder',
    'DataHelper',
    'AdditiveModel',
    'add_on_model',

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

    # Easy Sport Models (simplified interface)
    'EasySportModel',
    'quick_nba_prediction',
    'quick_nfl_prediction',
    'quick_nhl_prediction',
    'quick_mlb_prediction',
    'quick_cbb_prediction',
    'quick_cfb_prediction',
    'quick_wnba_prediction',
    'quick_soccer_btts',
    'train_and_predict',
    'AutoFeatures',

    # Database (betting tracking)
    'BettingDatabase',
    'create_database',

    # Advanced statistics
    'AdvancedStats',

    # Machine learning
    'DecisionTree',
    'RandomForest',
    'NeuralNetwork',
    'FeatureEngineering',
    'ModelValidation',

    # Sport-Specific Analytics Packages
    'NBAAnalytics',
    'NBABettingInterface',
    'NFLAnalytics',
    'NHLAnalytics',
    'NHLAdvancedAnalytics',
    'MLBAnalytics',
    'CBBAnalytics',
    'CFBAnalytics',
    'WNBAAnalytics',
    'SoccerAnalytics',
    'HorseRacingAnalytics',

    # NHL Advanced Prediction Models
    'NHLDecisionTree',
    'NHLPowerRankings',
    'NHLSimilarGameModel',
    'quick_nhl_decision_tree_ou',
    'quick_nhl_decision_tree_ats',

    # Expert opinion consensus model
    'ExpertConsensusModel',
    'ExpertSource',
    'ExpertOpinion',
    'OverUnderTrendModel',
    'TeamTrendStats',
]
