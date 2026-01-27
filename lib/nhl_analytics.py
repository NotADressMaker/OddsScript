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

# Updated league averages (use current season values; update seasonally)
# Source: MoneyPuck / Natural Stat Trick / NHL EDGE (2025-26 mid-season approx)
class NHLConstants:
    AVG_GOALS_PER_GAME = 3.15          # per team → total ~6.3
    AVG_HOME_ADVANTAGE = 0.28          # goals
    AVG_TOTAL_GOALS = 6.3
    AVG_SAVE_PERCENTAGE = 0.905
    AVG_SHOOTING_PERCENTAGE = 0.102
    AVG_PDO = 100.7                    # slight upward trend
    HIGH_DANGER_CONVERSION = 0.26      # ~26% in slot
    MEDIUM_DANGER_CONVERSION = 0.115
    LOW_DANGER_CONVERSION = 0.048

# Replace all hard-coded numbers with NHLConstants.XXX
# Example in calculate_expected_goals:
quality_multiplier = {
    ShotQuality.HIGH_DANGER: NHLConstants.HIGH_DANGER_CONVERSION / 0.095 * 3.5,
    ShotQuality.MEDIUM_DANGER: NHLConstants.MEDIUM_DANGER_CONVERSION / 0.095 * 1.5,
    ShotQuality.LOW_DANGER: NHLConstants.LOW_DANGER_CONVERSION / 0.095 * 0.6
}[shot_quality]

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
    HIGH_DANGER = "high_danger"  # Slot, close range
    MEDIUM_DANGER = "medium_danger"  # Mid-range
    LOW_DANGER = "low_danger"  # Perimeter, long range


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
    corsi_for: float  # All shot attempts
    corsi_against: float
    fenwick_for: float  # Unblocked shot attempts
    fenwick_against: float
    save_percentage: float
    shooting_percentage: float
    pdo: float  # Save% + Shooting% (luck metric)
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
    quality_starts: int  # Games with SV% > .913
    games_saved_above_expected: float  # GSAx


@dataclass
class ExpectedGoalsModel:
    """Expected goals (xG) calculation"""
    shot_distance: float
    shot_angle: float
    shot_type: str  # wrist, slap, snap, backhand, tip, deflection
    shot_quality: ShotQuality
    rebound: bool
    rush_shot: bool


class NHLAdvancedAnalytics:
    """Enhanced NHL analytics with advanced statistics"""

    # NHL constants
    AVG_GOALS_PER_GAME = 3.0
    AVG_HOME_ADVANTAGE = 0.25  # Goals
    AVG_TOTAL_GOALS = 6.0
    AVG_SAVE_PERCENTAGE = 0.910
    AVG_SHOOTING_PERCENTAGE = 0.095
    AVG_PDO = 100.0  # (SV% + SH%) * 100

    # Expected goals baselines
    XG_DISTANCE_FACTOR = 0.95  # xG decreases with distance
    XG_ANGLE_FACTOR = 0.90

    # Shot type conversion rates
    SHOT_CONVERSION_RATES = {
        'wrist': 0.095,
        'slap': 0.088,
        'snap': 0.103,
        'backhand': 0.082,
        'tip': 0.145,
        'deflection': 0.125
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
        Calculate expected goals (xG) for a shot

        Based on shot characteristics and historical data

        Args:
            shot_distance: Distance from goal in feet
            shot_angle: Angle from center in degrees
            shot_type: Type of shot
            shot_quality: Shot danger level
            rebound: Whether shot is a rebound
            rush_shot: Whether shot is from a rush

        Returns:
            Expected goals value (0-1)
        """
        # Base conversion rate by shot type
        base_xg = NHLAdvancedAnalytics.SHOT_CONVERSION_RATES.get(shot_type, 0.095)

        # Adjust for distance (inverse relationship)
        distance_factor = math.exp(-shot_distance / 30.0)

        # Adjust for angle (perpendicular is best)
        angle_factor = math.cos(math.radians(shot_angle))

        # Adjust for shot quality zone
        if shot_quality == ShotQuality.HIGH_DANGER:
            quality_multiplier = 3.5  # High danger = ~3.5x more likely
        elif shot_quality == ShotQuality.MEDIUM_DANGER:
            quality_multiplier = 1.5
        else:
            quality_multiplier = 0.6

        # Rebound bonus
        rebound_multiplier = 1.8 if rebound else 1.0

        # Rush shot bonus
        rush_multiplier = 1.3 if rush_shot else 1.0

        xg = (base_xg * distance_factor * angle_factor *
              quality_multiplier * rebound_multiplier * rush_multiplier)

        # Cap at reasonable maximum
        return min(xg, 0.65)

    @staticmethod
    def calculate_team_expected_goals(
        shots_for: int,
        high_danger_shots: int,
        medium_danger_shots: int,
        rebounds: int,
        rush_shots: int
    ) -> float:
        """
        Calculate team expected goals from shot data

        Args:
            shots_for: Total shots
            high_danger_shots: Shots from high danger areas
            medium_danger_shots: Shots from medium danger areas
            rebounds: Rebound shots
            rush_shots: Rush shots

        Returns:
            Expected goals
        """
        low_danger = shots_for - high_danger_shots - medium_danger_shots

        xg = (high_danger_shots * 0.25 +  # High danger ~25% conversion
              medium_danger_shots * 0.12 +  # Medium ~12%
              low_danger * 0.05 +  # Low ~5%
              rebounds * 0.10 +  # Rebound bonus
              rush_shots * 0.04)  # Rush bonus

        return xg

    @staticmethod
    def calculate_corsi_fenwick(
        shots_for: int,
        shots_against: int,
        blocked_shots_for: int,
        blocked_shots_against: int,
        missed_shots_for: int,
        missed_shots_against: int
    ) -> Dict[str, float]:
        """
        Calculate Corsi and Fenwick metrics

        Corsi = All shot attempts (shots + blocks + misses)
        Fenwick = Unblocked shot attempts (shots + misses)

        Args:
            shots_for: Shots on goal for
            shots_against: Shots on goal against
            blocked_shots_for: Blocked shots for
            blocked_shots_against: Blocked shots against
            missed_shots_for: Missed shots for
            missed_shots_against: Missed shots against

        Returns:
            Dictionary with Corsi and Fenwick metrics
        """
        # Corsi (all shot attempts)
        corsi_for = shots_for + blocked_shots_for + missed_shots_for
        corsi_against = shots_against + blocked_shots_against + missed_shots_against
        corsi_total = corsi_for + corsi_against

        corsi_pct = (corsi_for / corsi_total * 100) if corsi_total > 0 else 50.0

        # Fenwick (unblocked shot attempts)
        fenwick_for = shots_for + missed_shots_for
        fenwick_against = shots_against + missed_shots_against
        fenwick_total = fenwick_for + fenwick_against

        fenwick_pct = (fenwick_for / fenwick_total * 100) if fenwick_total > 0 else 50.0

        return {
            'corsi_for': corsi_for,
            'corsi_against': corsi_against,
            'corsi_percentage': corsi_pct,
            'corsi_differential': corsi_for - corsi_against,
            'fenwick_for': fenwick_for,
            'fenwick_against': fenwick_against,
            'fenwick_percentage': fenwick_pct,
            'fenwick_differential': fenwick_for - fenwick_against
        }

    @staticmethod
    def calculate_pdo(save_percentage: float, shooting_percentage: float) -> float:
        """
        Calculate PDO (luck metric)

        PDO = (Save% + Shooting%) * 100
        League average = 100.0

        Teams with high PDO (> 102) likely to regress
        Teams with low PDO (< 98) likely to improve

        Args:
            save_percentage: Team save percentage
            shooting_percentage: Team shooting percentage

        Returns:
            PDO value
        """
        return (save_percentage + shooting_percentage) * 100

    @staticmethod
    def analyze_goaltender_performance(
        saves: int,
        shots_against: int,
        goals_against: int,
        games_played: int,
        high_danger_saves: int,
        high_danger_shots: int,
        expected_goals_against: float
    ) -> Dict[str, float]:
        """
        Comprehensive goaltender analysis

        Args:
            saves: Total saves
            shots_against: Total shots faced
            goals_against: Total goals allowed
            games_played: Games played
            high_danger_saves: Saves on high danger shots
            high_danger_shots: High danger shots faced
            expected_goals_against: Expected goals based on shot quality

        Returns:
            Goaltender metrics
        """
        # Basic stats
        save_pct = saves / shots_against if shots_against > 0 else 0
        gaa = (goals_against / games_played) * 60 if games_played > 0 else 0  # Per 60 min

        # Quality start percentage (SV% > .913)
        # Approximate based on save percentage
        quality_start_likelihood = 1 / (1 + math.exp(-(save_pct - 0.913) * 100))

        # High danger save percentage
        hd_save_pct = (high_danger_saves / high_danger_shots
                      if high_danger_shots > 0 else 0)

        # Goals saved above expected (GSAx)
        gsax = expected_goals_against - goals_against
        gsax_per_game = gsax / games_played if games_played > 0 else 0

        return {
            'save_percentage': save_pct,
            'goals_against_average': gaa,
            'high_danger_save_pct': hd_save_pct,
            'quality_start_likelihood': quality_start_likelihood,
            'goals_saved_above_expected': gsax,
            'gsax_per_game': gsax_per_game,
            'performance_vs_expected': 'elite' if gsax_per_game > 0.3
                                      else 'above_average' if gsax_per_game > 0
                                      else 'below_average'
        }

    @staticmethod
    def calculate_power_play_value(
        pp_opportunities: int,
        pp_goals: int,
        league_avg_pp_pct: float = 0.20
    ) -> Dict[str, float]:
        """
        Analyze power play effectiveness

        Args:
            pp_opportunities: Power play opportunities
            pp_goals: Power play goals scored
            league_avg_pp_pct: League average PP%

        Returns:
            Power play metrics
        """
        pp_pct = (pp_goals / pp_opportunities * 100) if pp_opportunities > 0 else 0

        # Expected goals based on league average
        expected_pp_goals = pp_opportunities * league_avg_pp_pct

        # Goals above/below expected
        pp_differential = pp_goals - expected_pp_goals

        # Bayesian adjusted PP% (with league prior)
        bayesian_result = AdvancedStats.bayesian_win_probability(
            wins=pp_goals,
            losses=pp_opportunities - pp_goals,
            prior_alpha=league_avg_pp_pct * 100,
            prior_beta=(1 - league_avg_pp_pct) * 100
        )

        return {
            'pp_percentage': pp_pct,
            'pp_goals': pp_goals,
            'pp_opportunities': pp_opportunities,
            'expected_pp_goals': expected_pp_goals,
            'pp_differential': pp_differential,
            'bayesian_pp_pct': bayesian_result['mean_probability'] * 100,
            'pp_confidence_interval': (
                bayesian_result['ci_lower'] * 100,
                bayesian_result['ci_upper'] * 100
            )
        }

    @staticmethod
    def calculate_team_strength(
        goals_for: float,
        goals_against: float,
        xg_for: float,
        xg_against: float,
        corsi_pct: float,
        pdo: float,
        recent_form: List[int]
    ) -> Dict[str, float]:
        """
        Calculate comprehensive team strength rating

        Combines multiple metrics with Bayesian inference

        Args:
            goals_for: Goals scored per game
            goals_against: Goals allowed per game
            xg_for: Expected goals for per game
            xg_against: Expected goals against per game
            corsi_pct: Corsi percentage
            pdo: PDO value
            recent_form: Recent results (1=win, 0=loss) - last 10 games

        Returns:
            Team strength metrics
        """
        # Goal differential (actual)
        goal_diff = goals_for - goals_against

        # Expected goal differential (more stable predictor)
        xg_diff = xg_for - xg_against

        # Possession metric (Corsi as proxy)
        possession_strength = (corsi_pct - 50) / 10  # Normalized

        # PDO regression (teams regress to 100)
        pdo_adjustment = (pdo - 100) * 0.03  # Expect regression
        luck_adjusted_diff = goal_diff - pdo_adjustment

        # Recent form using EMA
        if recent_form:
            form_ema = AdvancedStats.exponential_moving_average(
                [float(x) for x in recent_form],
                alpha=0.3
            )
            current_form = form_ema[-1] if form_ema else 0.5
        else:
            current_form = 0.5

        # Combined strength rating (0-100 scale)
        base_strength = 50 + (xg_diff * 8)  # xG diff is most predictive
        base_strength += possession_strength * 2
        base_strength += current_form * 5

        # Clip to reasonable bounds
        strength_rating = max(20, min(80, base_strength))

        return {
            'strength_rating': strength_rating,
            'goal_differential': goal_diff,
            'expected_goal_differential': xg_diff,
            'luck_adjusted_differential': luck_adjusted_diff,
            'possession_rating': possession_strength,
            'current_form': current_form,
            'pdo_regression_expected': pdo_adjustment,
            'tier': 'elite' if strength_rating > 65
                   else 'above_average' if strength_rating > 55
                   else 'average' if strength_rating > 45
                   else 'below_average'
        }

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

        Can use either statistical model or machine learning

        Args:
            home_team_metrics: Home team advanced metrics
            away_team_metrics: Away team advanced metrics
            home_goalie_stats: Home goaltender stats
            away_goalie_stats: Away goaltender stats
            use_ml: Whether to use machine learning model

        Returns:
            Game predictions
        """
        # Calculate expected goals based on metrics
        home_xg = home_team_metrics.goals_for * (
            1 + (home_team_metrics.corsi_for / 100 - 0.5) * 0.2
        )
        away_xg = away_team_metrics.goals_for * (
            1 + (away_team_metrics.corsi_for / 100 - 0.5) * 0.2
        )

        # Adjust for goaltender quality
        home_goalie_adj = 1 - (home_goalie_stats.save_percentage - 0.910) * 0.5
        away_goalie_adj = 1 - (away_goalie_stats.save_percentage - 0.910) * 0.5

        home_xg_adjusted = home_xg + 0.25  # Home ice
        away_xg_adjusted = away_xg

        # Adjust for opposing goaltender
        home_expected = home_xg_adjusted * away_goalie_adj
        away_expected = away_xg_adjusted * home_goalie_adj

        # Use Poisson for probabilities
        results = PoissonCalculator.calculate_match_probabilities(
            home_expected,
            away_expected,
            max_goals=10
        )

        # Adjust for overtime (50/50 split of draws)
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

    @staticmethod
    def simulate_season_monte_carlo(
        team_strength: float,
        games_remaining: int,
        current_points: int,
        n_simulations: int = 10000
    ) -> Dict[str, any]:
        """
        Monte Carlo simulation of remaining season

        Args:
            team_strength: Team strength rating (0-1, where 0.5 is average)
            games_remaining: Number of games left
            current_points: Current point total
            n_simulations: Number of simulations

        Returns:
            Season outcome probabilities
        """
        def simulate_remaining_games():
            """Simulate remaining games"""
            points = current_points
            for _ in range(games_remaining):
                # Win probability based on team strength
                if random.random() < team_strength:
                    points += 2  # Win
                elif random.random() < 0.25:  # ~25% of losses go to OT
                    points += 1  # OT loss
                # else: regulation loss, 0 points
            return points

        # Run Monte Carlo simulation
        results = AdvancedStats.monte_carlo_simulation(
            simulate_remaining_games,
            n_simulations=n_simulations
        )

        # Calculate playoff probability (assuming ~95 points needed)
        playoff_threshold = 95
        playoff_prob = sum(1 for pts in results['results']
                          if pts >= playoff_threshold) / n_simulations

        return {
            'expected_points': results['mean'],
            'median_points': results['median'],
            'points_std_dev': results['std_dev'],
            'points_range': (results['min'], results['max']),
            'points_90pct_confidence': (results['p5'], results['p95']),
            'playoff_probability': playoff_prob,
            'simulations': n_simulations
        }

    @staticmethod
    def analyze_betting_edge(
        predicted_probability: float,
        offered_odds: float,
        confidence_interval: Tuple[float, float],
        bankroll: float = 1000,
        use_kelly: bool = True
    ) -> Dict[str, float]:
        """
        Analyze betting edge and optimal bet sizing

        Args:
            predicted_probability: Model's predicted win probability
            offered_odds: Sportsbook odds
            confidence_interval: CI for predicted probability
            bankroll: Current bankroll
            use_kelly: Whether to use Kelly Criterion

        Returns:
            Betting analysis
        """
        # Calculate implied probability from odds
        implied_prob = 1 / offered_odds

        # Edge
        edge = predicted_probability - implied_prob
        edge_pct = edge * 100

        # Expected value
        ev = (predicted_probability * (offered_odds - 1)) - (1 - predicted_probability)
        ev_pct = ev * 100

        # Kelly Criterion sizing
        if use_kelly:
            kelly_fraction = AdvancedStats.kelly_optimal_size(
                predicted_probability,
                offered_odds
            )
            # Use half-Kelly for conservatism
            recommended_bet = bankroll * kelly_fraction * 0.5
        else:
            # Fixed 2% of bankroll if edge > 5%
            recommended_bet = bankroll * 0.02 if edge_pct > 5 else 0

        # Confidence-adjusted edge (use lower bound)
        conservative_edge = confidence_interval[0] - implied_prob

        return {
            'predicted_probability': predicted_probability,
            'implied_probability': implied_prob,
            'edge_percentage': edge_pct,
            'expected_value_pct': ev_pct,
            'kelly_fraction': kelly_fraction if use_kelly else 0,
            'recommended_bet': max(0, recommended_bet),
            'conservative_edge': conservative_edge * 100,
            'bet_recommendation': 'strong_bet' if edge_pct > 10
                                 else 'bet' if edge_pct > 5
                                 else 'small_bet' if edge_pct > 2
                                 else 'pass'
        }

    @staticmethod
    def calculate_live_betting_edge(
        current_score_home: int,
        current_score_away: int,
        time_remaining_mins: float,
        home_team_strength: float,
        away_team_strength: float,
        live_odds: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate betting edge for live/in-play betting

        Args:
            current_score_home: Current home team score
            current_score_away: Current away team score
            time_remaining_mins: Time remaining in game (minutes)
            home_team_strength: Home team strength rating
            away_team_strength: Away team strength rating
            live_odds: Current live odds {'home': 2.1, 'away': 1.8}

        Returns:
            Live betting analysis
        """
        # Calculate expected goals for remaining time
        goals_per_60 = 6.0  # League average total
        time_fraction = time_remaining_mins / 60.0

        expected_remaining_goals = goals_per_60 * time_fraction

        # Distribute based on team strength
        home_fraction = home_team_strength / (home_team_strength + away_team_strength)

        home_expected_remaining = expected_remaining_goals * home_fraction
        away_expected_remaining = expected_remaining_goals * (1 - home_fraction)

        # Current score + expected remaining
        home_projected = current_score_home + home_expected_remaining
        away_projected = current_score_away + away_expected_remaining

        # Win probabilities using Poisson for remaining goals
        remaining_probs = PoissonCalculator.calculate_match_probabilities(
            home_expected_remaining,
            away_expected_remaining,
            max_goals=8
        )

        # Adjust based on current score
        if current_score_home > current_score_away:
            # Home is ahead
            goal_diff = current_score_home - current_score_away
            home_win_prob = remaining_probs['home_win'] + remaining_probs['draw']
            if goal_diff >= 2:
                home_win_prob = min(0.95, home_win_prob * 1.2)
        elif current_score_away > current_score_home:
            # Away is ahead
            goal_diff = current_score_away - current_score_home
            home_win_prob = remaining_probs['home_win']
            if goal_diff >= 2:
                home_win_prob = max(0.05, home_win_prob * 0.8)
        else:
            # Tied
            home_win_prob = (remaining_probs['home_win'] +
                           remaining_probs['draw'] * 0.5)

        away_win_prob = 1 - home_win_prob

        # Calculate edges
        home_edge = home_win_prob - (1 / live_odds['home']) if 'home' in live_odds else 0
        away_edge = away_win_prob - (1 / live_odds['away']) if 'away' in live_odds else 0

        return {
            'home_win_probability': home_win_prob,
            'away_win_probability': away_win_prob,
            'home_projected_goals': home_projected,
            'away_projected_goals': away_projected,
            'time_remaining': time_remaining_mins,
            'home_edge_pct': home_edge * 100,
            'away_edge_pct': away_edge * 100,
            'best_bet': 'home' if home_edge > 0.05
                       else 'away' if away_edge > 0.05
                       else 'none'
        }


# Maintain backward compatibility with basic class
class NHLAnalytics:
    """Basic NHL analytics (backward compatible)"""

    AVG_GOALS_PER_GAME = 3.0
    AVG_HOME_ADVANTAGE = 0.25
    AVG_TOTAL_GOALS = 6.0
    REGULATION_TIME_PCT = 0.75

    @staticmethod
    def calculate_moneyline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        is_home: bool = True,
        include_overtime: bool = True
    ) -> Dict:
        """Calculate NHL moneyline probability"""
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0
        team_lambda = team_goals_avg + home_adj
        opp_lambda = opponent_goals_avg

        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda, opp_lambda, max_goals=10
        )

        if include_overtime:
            overtime_win_boost = results['draw'] * 0.5
            return {
                'win_probability': results['home_win'] + overtime_win_boost if is_home else results['away_win'] + overtime_win_boost,
                'regulation_win_probability': results['home_win'] if is_home else results['away_win'],
                'overtime_probability': results['draw'],
                'loss_probability': results['away_win'] if is_home else results['home_win']
            }
        else:
            return {
                'win_probability': results['home_win'] if is_home else results['away_win'],
                'tie_probability': results['draw'],
                'loss_probability': results['away_win'] if is_home else results['home_win']
            }

    @staticmethod
    def calculate_puckline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        puckline: float = -1.5,
        is_home: bool = True
    ) -> Dict:
        """Calculate puck line cover probability"""
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0
        team_lambda = team_goals_avg + home_adj
        opp_lambda = opponent_goals_avg

        results = PoissonCalculator.calculate_match_probabilities(
            team_lambda, opp_lambda, max_goals=10
        )

        cover_prob = 0.0
        prob_matrix = results['prob_matrix']

        for team_goals in range(len(prob_matrix)):
            for opp_goals in range(len(prob_matrix[0])):
                margin = team_goals - opp_goals
                if puckline < 0:
                    if margin > abs(puckline):
                        cover_prob += prob_matrix[team_goals][opp_goals]
                else:
                    if margin + puckline > 0:
                        cover_prob += prob_matrix[team_goals][opp_goals]

        return {
            'cover_probability': cover_prob,
            'puckline': puckline,
            'expected_margin': team_lambda - opp_lambda
        }

    @staticmethod
    def calculate_total_probability(
        team1_goals_avg: float,
        team2_goals_avg: float,
        total_line: float,
        goalie_adjustment: float = 1.0
    ) -> Dict:
        """Calculate over/under probability"""
        total_lambda = (team1_goals_avg + team2_goals_avg) * goalie_adjustment

        results = PoissonCalculator.calculate_total_probabilities(
            total_lambda / 2, total_lambda / 2, total_line, max_goals=12
        )

        return {
            'over_probability': results['over_probability'],
            'under_probability': results['under_probability'],
            'expected_total': total_lambda,
            'line': total_line,
            'goalie_adjustment': goalie_adjustment
        }

    @staticmethod
    def simulate_game(
        home_goals_avg: float,
        away_goals_avg: float,
        seed: Optional[int] = None
    ) -> Dict:
        """Simulate NHL game"""
        home_lambda = home_goals_avg + NHLAnalytics.AVG_HOME_ADVANTAGE
        away_lambda = away_goals_avg

        result = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed)

        game_result = {
            'home_score': result['home_score'],
            'away_score': result['away_score'],
            'total_goals': result['total_score'],
            'regulation_result': result['result'],
            'margin': result['home_score'] - result['away_score']
        }

        if result['result'] == 'draw':
            if seed is not None:
                random.seed(seed + 1)
            ot_winner = random.choice(['home_win', 'away_win'])
            game_result['final_result'] = ot_winner
            game_result['overtime'] = True
            if ot_winner == 'home_win':
                game_result['home_score'] += 1
            else:
                game_result['away_score'] += 1
        else:
            game_result['final_result'] = result['result']
            game_result['overtime'] = False

        return game_result


if __name__ == '__main__':
    print("Enhanced NHL Analytics Library")
    print("=" * 70)

    # Example 1: Expected Goals
    print("\n1. Expected Goals (xG) Calculation:")
    xg = NHLAdvancedAnalytics.calculate_expected_goals(
        shot_distance=15,
        shot_angle=20,
        shot_type='wrist',
        shot_quality=ShotQuality.HIGH_DANGER,
        rebound=True
    )
    print(f"   xG for high-danger rebound: {xg:.3f}")

    # Example 2: Goaltender Analysis
    print("\n2. Goaltender Performance Analysis:")
    goalie_analysis = NHLAdvancedAnalytics.analyze_goaltender_performance(
        saves=580,
        shots_against=640,
        goals_against=60,
        games_played=20,
        high_danger_saves=180,
        high_danger_shots=210,
        expected_goals_against=65
    )
    print(f"   Save%: {goalie_analysis['save_percentage']:.3f}")
    print(f"   GSAx: {goalie_analysis['goals_saved_above_expected']:.2f}")
    print(f"   Performance: {goalie_analysis['performance_vs_expected']}")

    # Example 3: Team Strength Rating
    print("\n3. Team Strength Analysis:")
    recent_games = [1, 1, 0, 1, 1, 1, 0, 1, 1, 1]  # 8-2 in last 10
    strength = NHLAdvancedAnalytics.calculate_team_strength(
        goals_for=3.5,
        goals_against=2.3,
        xg_for=3.2,
        xg_against=2.5,
        corsi_pct=54.5,
        pdo=101.2,
        recent_form=recent_games
    )
    print(f"   Strength Rating: {strength['strength_rating']:.1f}/100")
    print(f"   Tier: {strength['tier']}")
    print(f"   xG Differential: {strength['expected_goal_differential']:.2f}")

    # Example 4: Betting Edge Analysis
    print("\n4. Betting Edge Analysis:")
    edge_analysis = NHLAdvancedAnalytics.analyze_betting_edge(
        predicted_probability=0.58,
        offered_odds=2.1,
        confidence_interval=(0.53, 0.63),
        bankroll=1000,
        use_kelly=True
    )
    print(f"   Edge: {edge_analysis['edge_percentage']:.2f}%")
    print(f"   EV: {edge_analysis['expected_value_pct']:.2f}%")
    print(f"   Recommended Bet: ${edge_analysis['recommended_bet']:.2f}")
    print(f"   Recommendation: {edge_analysis['bet_recommendation']}")

    # Example 5: Monte Carlo Season Simulation
    print("\n5. Monte Carlo Season Simulation:")
    season_sim = NHLAdvancedAnalytics.simulate_season_monte_carlo(
        team_strength=0.58,
        games_remaining=25,
        current_points=75,
        n_simulations=10000
    )
    print(f"   Expected Points: {season_sim['expected_points']:.1f}")
    print(f"   90% CI: {season_sim['points_90pct_confidence']}")
    print(f"   Playoff Probability: {season_sim['playoff_probability']*100:.1f}%")
