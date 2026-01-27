
   #!/usr/bin/env python3
"""
Enhanced NHL Analytics Library
Comprehensive statistical models for NHL (Hockey) betting including:
- Expected Goals (xG) models
- Advanced metrics (Corsi, Fenwick, PDO)
- Power Play/Penalty Kill analysis
- Goaltender performance analysis
- Team strength calculations
- Machine learning predictions
- Bayesian inference
- Monte Carlo simulations
"""
import math
import random
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    from lib.poisson_calculator import PoissonCalculator
    from lib.advanced_stats import AdvancedStats
    from lib.ml_models import RandomForest, FeatureEngineering
except ImportError:
    # Handle imports for testing
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from lib.poisson_calculator import PoissonCalculator
    from lib.advanced_stats import AdvancedStats
    from lib.ml_models import RandomForest, FeatureEngineering


class ShotQuality(Enum):
    """Shot quality categories"""
    HIGH_DANGER = "high_danger"     # Slot, close range
    MEDIUM_DANGER = "medium_danger" # Mid-range
    LOW_DANGER = "low_danger"       # Perimeter, long range


class Situation(Enum):
    """Game situations"""
    EVEN_STRENGTH = "even_strength"
    POWER_PLAY = "power_play"
    PENALTY_KILL = "penalty_kill"
    EMPTY_NET = "empty_net"


@dataclass
class TeamMetrics:
    """Advanced team metrics"""
    goals_for: float
    goals_against: float
    shots_for: float
    shots_against: float
    corsi_for: float          # All shot attempts
    corsi_against: float
    fenwick_for: float        # Unblocked shot attempts
    fenwick_against: float
    save_percentage: float
    shooting_percentage: float
    pdo: float                # Save% + Shooting% (luck metric)
    power_play_pct: float
    penalty_kill_pct: float
    faceoff_win_pct: float


@dataclass
class GoaltenderStats:
    """Goaltender statistics"""
    save_percentage: float
    goals_against_average: float
    high_danger_save_pct: float
    games_started: int
    quality_starts: int       # Games with SV% > .913
    games_saved_above_expected: float  # GSAx


@dataclass
class ExpectedGoalsModel:
    """Expected goals (xG) calculation"""
    shot_distance: float
    shot_angle: float
    shot_type: str           # wrist, slap, snap, backhand, tip, deflection
    shot_quality: ShotQuality
    rebound: bool
    rush_shot: bool


class NHLAdvancedAnalytics:
    """Enhanced NHL analytics with advanced statistics"""

    # Updated league averages (2025-26 mid-season approx; update seasonally)
    AVG_GOALS_PER_GAME = 3.15          # per team → total ~6.3
    AVG_HOME_ADVANTAGE = 0.28          # goals
    AVG_TOTAL_GOALS = 6.3
    AVG_SAVE_PERCENTAGE = 0.905
    AVG_SHOOTING_PERCENTAGE = 0.102
    AVG_PDO = 100.7                    # slight upward trend
    LEAGUE_GSAX_AVG_PER_GAME = 0.0     # league average GSAx = 0 by definition

    # Expected goals baselines
    XG_DISTANCE_FACTOR = 0.95          # xG decreases with distance
    XG_ANGLE_FACTOR = 0.90

    # Shot type conversion rates (updated to modern NHL)
    SHOT_CONVERSION_RATES = {
        'wrist': 0.098,
        'slap': 0.091,
        'snap': 0.107,
        'backhand': 0.085,
        'tip': 0.150,
        'deflection': 0.130
    }

    @staticmethod
    def calculate_expected_goals(
        shot_distance: float,
        shot_angle: float,
        shot_type: str = 'wrist',
        shot_quality: ShotQuality = ShotQuality.MEDIUM_DANGER,
        rebound: bool = False,
        rush_shot: bool = False
    ) -> float:
        """
        Calculate expected goals (xG) for a single shot
        """
        base_xg = NHLAdvancedAnalytics.SHOT_CONVERSION_RATES.get(shot_type, 0.098)
        distance_factor = math.exp(-shot_distance / 30.0)
        angle_factor = math.cos(math.radians(shot_angle))

        quality_multiplier = {
            ShotQuality.HIGH_DANGER: 3.6,
            ShotQuality.MEDIUM_DANGER: 1.6,
            ShotQuality.LOW_DANGER: 0.6
        }[shot_quality]

        rebound_multiplier = 1.8 if rebound else 1.0
        rush_multiplier = 1.3 if rush_shot else 1.0

        xg = (base_xg * distance_factor * angle_factor *
              quality_multiplier * rebound_multiplier * rush_multiplier)

        return min(xg, 0.70)  # slightly higher cap for modern NHL

    @staticmethod
    def adjust_for_goalies(
        home_xg: float,
        away_xg: float,
        home_gsax: float = 0.0,
        away_gsax: float = 0.0,
        league_gsax_avg: float = 0.0
    ) -> Tuple[float, float]:
        """
        Adjust expected goals based on starting goalie quality.
        GSAx > 0 = elite goalie → lowers opponent's xG
        GSAx < 0 = weak goalie → increases opponent's xG
        """
        home_adj = 1 - (home_gsax - league_gsax_avg) * 0.12
        away_adj = 1 - (away_gsax - league_gsax_avg) * 0.12

        adjusted_home_xg = home_xg * away_adj      # home xG lowered by away goalie
        adjusted_away_xg = away_xg * home_adj      # away xG lowered by home goalie

        # Sanity clamps
        adjusted_home_xg = max(0.5, min(adjusted_home_xg, 5.8))
        adjusted_away_xg = max(0.5, min(adjusted_away_xg, 5.8))

        return adjusted_home_xg, adjusted_away_xg

    @staticmethod
    def predict_game_ml(
        home_team_metrics: TeamMetrics,
        away_team_metrics: TeamMetrics,
        home_goalie_stats: GoaltenderStats,
        away_goalie_stats: GoaltenderStats,
        use_ml: bool = False
    ) -> Dict[str, float]:
        """
        Predict game outcome using advanced metrics
        Now includes robust GSAx-based goalie adjustment
        """
        # Base expected goals from team metrics
        home_xg = home_team_metrics.goals_for * (
            1 + (home_team_metrics.corsi_for / 100 - 0.5) * 0.2
        )
        away_xg = away_team_metrics.goals_for * (
            1 + (away_team_metrics.corsi_for / 100 - 0.5) * 0.2
        )

        # Per-game GSAx (safe division)
        home_gsax_per = (
            home_goalie_stats.games_saved_above_expected / home_goalie_stats.games_started
            if home_goalie_stats.games_started > 0 else 0.0
        )
        away_gsax_per = (
            away_goalie_stats.games_saved_above_expected / away_goalie_stats.games_started
            if away_goalie_stats.games_started > 0 else 0.0
        )

        # Apply goalie adjustment
        home_expected, away_expected = NHLAdvancedAnalytics.adjust_for_goalies(
            home_xg=home_xg,
            away_xg=away_xg,
            home_gsax=home_gsax_per,
            away_gsax=away_gsax_per,
            league_gsax_avg=NHLAdvancedAnalytics.LEAGUE_GSAX_AVG_PER_GAME
        )

        # Small home-ice boost after goalie adj
        home_expected += NHLAdvancedAnalytics.AVG_HOME_ADVANTAGE

        # Poisson probabilities
        results = PoissonCalculator.calculate_match_probabilities(
            home_expected, away_expected, max_goals=10
        )

        # Overtime adjustment (50/50 split of draws)
        ot_split = results['draw'] * 0.5

        return {
            'home_win_probability': results['home_win'] + ot_split,
            'away_win_probability': results['away_win'] + ot_split,
            'regulation_home_win': results['home_win'],
            'regulation_away_win': results['away_win'],
            'overtime_probability': results['draw'],
            'expected_home_goals': home_expected,
            'expected_away_goals': away_expected,
            'expected_total': home_expected + away_expected
        }

    # ... (keep all your other methods unchanged: calculate_team_expected_goals,
    # calculate_corsi_fenwick, calculate_pdo, analyze_goaltender_performance,
    # calculate_power_play_value, calculate_team_strength, simulate_season_monte_carlo,
    # analyze_betting_edge, calculate_live_betting_edge, etc.)

# Backward compatibility class remains unchanged
class NHLAnalytics:
    # ... your existing code here ...
    pass


if __name__ == '__main__':
    print("Enhanced NHL Analytics Library (with goalie adjustment)")
    print("=" * 70)

    # Test the new adjustment
    print("\nTest: Goalie Adjustment")
    adj_home, adj_away = NHLAdvancedAnalytics.adjust_for_goalies(
        home_xg=3.2,
        away_xg=2.9,
        home_gsax=0.45,    # strong home goalie
        away_gsax=-0.30,   # weak away goalie
        league_gsax_avg=0.0
    )
    print(f"Adjusted home xG: {adj_home:.2f}")
    print(f"Adjusted away xG: {adj_away:.2f}")

    # Full predict_game_ml test would go here (using sample metrics/stats)
    
    
        
       
