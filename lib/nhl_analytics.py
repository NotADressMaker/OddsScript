#!/usr/bin/env python3
"""
lib/nhl_analytics.py

NHL Analytics Library (SportsBetLang-friendly, NO NHLEnsemble)

This file intentionally contains THREE layers:

1) NHLAdvancedAnalytics
   - the "engine room": xG / goalie adjustments / strength signals
   - can be used standalone for analysis

2) NHLAnalytics (LEGACY, backward compatible)
   - keeps older method names/signatures working:
       - calculate_moneyline_probability(...)
       - calculate_puckline_probability(...)
       - calculate_total_probability(...)
       - simulate_game(...)
   - uses PoissonCalculator where available

3) NHLBettingInterface (SportsBetLang-facing)
   - standardized outputs for:
       - MONEY (moneyline)
       - SPREAD (puckline)
       - TOTAL (over/under)
   - optional 3-model convergence using:
       - power_model
       - similar_model
       - tree_model
   - NO NHLEnsemble required
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------
# Optional repo imports
# ----------------------------
try:
    from lib.poisson_calculator import PoissonCalculator
except Exception:
    PoissonCalculator = None  # type: ignore


# ----------------------------
# Constants / enums / data containers
# ----------------------------

class NHLConstants:
    """
    Update seasonally. Keep these in ONE place.
    Values here are conservative defaults (not promises of accuracy).
    """
    AVG_GOALS_PER_GAME = 3.10        # per team
    AVG_TOTAL_GOALS = 6.20           # per game total
    AVG_HOME_ADVANTAGE = 0.25        # goals
    AVG_PDO = 100.0                  # luck metric center
    LEAGUE_GSAX_AVG = 0.0            # GSAx average is ~0 by definition


class ShotQuality(Enum):
    HIGH_DANGER = "high_danger"
    MEDIUM_DANGER = "medium_danger"
    LOW_DANGER = "low_danger"


class Situation(Enum):
    EVEN_STRENGTH = "even_strength"
    POWER_PLAY = "power_play"
    PENALTY_KILL = "penalty_kill"


@dataclass
class TeamMetrics:
    goals_for: float
    goals_against: float
    corsi_pct: float = 50.0
    xg_for: float = 0.0
    xg_against: float = 0.0
    pdo: float = NHLConstants.AVG_PDO
    pp_pct: float = 20.0
    pk_pct: float = 80.0
    recent_form: Optional[List[int]] = None  # 1=win,0=loss
    shots_for: float = 0.0
    shots_against: float = 0.0
    corsi_for: float = 0.0
    corsi_against: float = 0.0
    fenwick_for: float = 0.0
    fenwick_against: float = 0.0
    save_percentage: float = 0.0
    shooting_percentage: float = 0.0
    power_play_pct: Optional[float] = None
    penalty_kill_pct: Optional[float] = None
    faceoff_win_pct: float = 0.5

    def __post_init__(self) -> None:
        if self.power_play_pct is None:
            self.power_play_pct = self.pp_pct / 100.0
        if self.penalty_kill_pct is None:
            self.penalty_kill_pct = self.pk_pct / 100.0


@dataclass
class GoaltenderStats:
    save_percentage: float = 0.905
    goals_against_average: float = 2.8
    high_danger_save_pct: float = 0.820
    low_danger_save_pct: float = 0.980
    career_high_danger_save_pct: Optional[float] = None
    career_low_danger_save_pct: Optional[float] = None
    recent_high_danger_save_pct: Optional[float] = None
    recent_low_danger_save_pct: Optional[float] = None
    recent_save_percentage: Optional[float] = None
    games_started: int = 0
    quality_starts: int = 0
    games_saved_above_expected: float = 0.0  # total GSAx
    starts_last_7: int = 0
    back_to_back_starts: int = 0
    is_starter: bool = True


# ----------------------------
# Odds + EV utilities (American odds)
# ----------------------------

def american_to_implied_prob(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def prob_to_american(prob: float) -> int:
    """Convert probability to fair American odds (rounded)."""
    prob = float(prob)
    if prob <= 0.0 or prob >= 1.0:
        raise ValueError("Probability must be between 0 and 1 (exclusive).")
    if prob > 0.5:
        return int(-round((prob / (1 - prob)) * 100))
    return int(round(((1 - prob) / prob) * 100))


def payout_per_1_risk(odds: float) -> float:
    """Profit for risking $1 at given American odds."""
    if odds > 0:
        return odds / 100.0
    return 100.0 / (-odds)


def expected_value_per_1_risk(prob_win: float, odds: float) -> float:
    """EV for risking $1: EV = p*profit - (1-p)*1"""
    profit = payout_per_1_risk(odds)
    return prob_win * profit - (1.0 - prob_win)


# ----------------------------
# Simple Poisson helpers (used if PoissonCalculator missing)
# ----------------------------

def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def _poisson_cdf(k: int, lam: float, max_k: int = 25) -> float:
    total = 0.0
    for i in range(0, min(int(k), max_k) + 1):
        total += _poisson_pmf(i, lam)
    return total


def _poisson_prob_over_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    # 6.5 -> over means >= 7
    if line % 1 == 0.5:
        threshold = int(math.floor(line) + 1)
        p_le = _poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
        return max(0.0, 1.0 - p_le)
    # integer: over means >= line+1
    threshold = int(line) + 1
    p_le = _poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
    return max(0.0, 1.0 - p_le)


def _poisson_prob_under_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    # 6.5 -> under means <= 6
    if line % 1 == 0.5:
        threshold = int(math.floor(line))
        return _poisson_cdf(threshold, total_lambda, max_k=max_k)
    # integer: under means <= line-1 (push at line)
    threshold = int(line) - 1
    return _poisson_cdf(threshold, total_lambda, max_k=max_k)


def _poisson_prob_push(total_lambda: float, line: float) -> float:
    if line % 1 != 0:
        return 0.0
    return _poisson_pmf(int(line), total_lambda)


# ============================================================
# 1) NHLAdvancedAnalytics (engine room)
# ============================================================

class NHLAdvancedAnalytics:
    # shot conversion baselines by type
    SHOT_CONVERSION_RATES = {
        "wrist": 0.095,
        "slap": 0.088,
        "snap": 0.103,
        "backhand": 0.082,
        "tip": 0.145,
        "deflection": 0.125,
    }

    @staticmethod
    def calculate_expected_goals(
        shot_distance: float,
        shot_angle: float,
        shot_type: str = "wrist",
        shot_quality: ShotQuality = ShotQuality.MEDIUM_DANGER,
        rebound: bool = False,
        rush_shot: bool = False,
    ) -> float:
        base_xg = NHLAdvancedAnalytics.SHOT_CONVERSION_RATES.get(shot_type, 0.095)
        distance_factor = math.exp(-shot_distance / 30.0)
        angle_factor = max(0.0, math.cos(math.radians(shot_angle)))

        if shot_quality == ShotQuality.HIGH_DANGER:
            quality_multiplier = 3.5
        elif shot_quality == ShotQuality.MEDIUM_DANGER:
            quality_multiplier = 1.5
        else:
            quality_multiplier = 0.6

        rebound_multiplier = 1.8 if rebound else 1.0
        rush_multiplier = 1.3 if rush_shot else 1.0

        xg = base_xg * distance_factor * angle_factor * quality_multiplier * rebound_multiplier * rush_multiplier
        return float(min(xg, 0.65))

    @staticmethod
    def calculate_team_expected_goals(
        shots_for: int,
        high_danger_shots: int,
        medium_danger_shots: int,
        rebounds: int = 0,
        rush_shots: int = 0,
    ) -> float:
        """Estimate team expected goals from shot quality mix."""
        shots_for = max(0, int(shots_for))
        high_danger_shots = max(0, int(high_danger_shots))
        medium_danger_shots = max(0, int(medium_danger_shots))
        rebounds = max(0, int(rebounds))
        rush_shots = max(0, int(rush_shots))

        low_danger_shots = max(0, shots_for - high_danger_shots - medium_danger_shots)

        xg = (
            high_danger_shots * 0.20
            + medium_danger_shots * 0.10
            + low_danger_shots * 0.05
            + rebounds * 0.05
            + rush_shots * 0.04
        )
        return float(max(0.1, xg))

    @staticmethod
    def calculate_corsi_fenwick(
        shots_for: int,
        shots_against: int,
        blocked_shots_for: int,
        blocked_shots_against: int,
        missed_shots_for: int,
        missed_shots_against: int,
    ) -> Dict[str, float]:
        """Calculate Corsi/Fenwick metrics."""
        corsi_for = shots_for + blocked_shots_for + missed_shots_for
        corsi_against = shots_against + blocked_shots_against + missed_shots_against
        total_corsi = corsi_for + corsi_against
        corsi_pct = (corsi_for / total_corsi * 100.0) if total_corsi > 0 else 50.0

        fenwick_for = shots_for + missed_shots_for
        fenwick_against = shots_against + missed_shots_against
        total_fenwick = fenwick_for + fenwick_against
        fenwick_pct = (fenwick_for / total_fenwick * 100.0) if total_fenwick > 0 else 50.0

        return {
            "corsi_for": float(corsi_for),
            "corsi_against": float(corsi_against),
            "corsi_percentage": float(corsi_pct),
            "corsi_differential": float(corsi_for - corsi_against),
            "fenwick_for": float(fenwick_for),
            "fenwick_against": float(fenwick_against),
            "fenwick_percentage": float(fenwick_pct),
        }

    @staticmethod
    def calculate_pdo(save_percentage: float, shooting_percentage: float) -> float:
        """PDO = (SV% + SH%) * 100."""
        return float((save_percentage + shooting_percentage) * 100.0)

    @staticmethod
    def analyze_goaltender_performance(
        saves: int,
        shots_against: int,
        goals_against: int,
        games_played: int,
        high_danger_saves: int,
        high_danger_shots: int,
        expected_goals_against: float,
    ) -> Dict[str, float | str]:
        """Compute goaltender summary stats."""
        save_percentage = (saves / shots_against) if shots_against > 0 else 0.0
        gaa = (goals_against / games_played) if games_played > 0 else 0.0
        high_danger_save_pct = (
            high_danger_saves / high_danger_shots if high_danger_shots > 0 else 0.0
        )
        gsax = float(expected_goals_against) - float(goals_against)

        if gsax >= 10:
            performance = "elite"
        elif gsax >= 2:
            performance = "good"
        elif gsax <= -5:
            performance = "poor"
        else:
            performance = "average"

        return {
            "save_percentage": float(save_percentage),
            "goals_against_average": float(gaa),
            "high_danger_save_pct": float(high_danger_save_pct),
            "goals_saved_above_expected": float(gsax),
            "performance_vs_expected": performance,
        }

    @staticmethod
    def detect_goalie_regression(
        goalie: GoaltenderStats,
        high_danger_weight: float = 0.65,
        low_danger_weight: float = 0.35,
        heater_threshold: float = 0.02,
        slump_threshold: float = -0.02,
    ) -> Dict[str, float | str]:
        """
        Detect unsustainable heater/slump using high/low danger save% vs career norms.

        High danger save % gets more weight, because it is less stable and more
        impactful in single-game outcomes.
        """
        career_high = goalie.career_high_danger_save_pct
        career_low = goalie.career_low_danger_save_pct
        recent_high = goalie.recent_high_danger_save_pct
        recent_low = goalie.recent_low_danger_save_pct

        if career_high is None:
            career_high = goalie.high_danger_save_pct
        if career_low is None:
            career_low = goalie.low_danger_save_pct
        if recent_high is None:
            recent_high = goalie.high_danger_save_pct
        if recent_low is None:
            recent_low = goalie.low_danger_save_pct

        high_delta = float(recent_high - career_high)
        low_delta = float(recent_low - career_low)
        weighted_delta = (high_delta * high_danger_weight) + (low_delta * low_danger_weight)
        volatility_score = abs(weighted_delta)

        if not goalie.is_starter:
            return {
                "signal": "non_starter",
                "weighted_delta": 0.0,
                "volatility_score": float(volatility_score),
                "high_danger_delta": float(high_delta),
                "low_danger_delta": float(low_delta),
                "confidence": 0.0,
            }

        if weighted_delta >= heater_threshold:
            signal = "heater"
        elif weighted_delta <= slump_threshold:
            signal = "slump"
        else:
            signal = "stable"

        sample_starts = max(1, goalie.starts_last_7)
        sample_factor = min(1.0, 0.4 + (sample_starts / 7.0))
        confidence = min(0.95, 0.5 + volatility_score * 10.0) * sample_factor

        return {
            "signal": signal,
            "weighted_delta": float(weighted_delta),
            "volatility_score": float(volatility_score),
            "high_danger_delta": float(high_delta),
            "low_danger_delta": float(low_delta),
            "confidence": float(confidence),
        }

    @staticmethod
    def adjust_team_strength_for_goalie(
        base_strength: float,
        goalie: GoaltenderStats,
        back_to_back_penalty: float = 1.6,
        volatility_multiplier: float = 28.0,
    ) -> Dict[str, float | str]:
        """
        Adjust team strength based on goalie regression and back-to-back starts.

        Heater -> expect regression (negative adjustment).
        Slump -> expect rebound (positive adjustment).
        Back-to-back starts add fatigue penalty, scaled by volatility.
        """
        regression = NHLAdvancedAnalytics.detect_goalie_regression(goalie)
        adjustment = 0.0

        if regression["signal"] == "heater":
            adjustment -= min(4.0, regression["volatility_score"] * volatility_multiplier)
        elif regression["signal"] == "slump":
            adjustment += min(4.0, regression["volatility_score"] * volatility_multiplier)

        fatigue_penalty = 0.0
        if goalie.back_to_back_starts > 0:
            fatigue_penalty = -1.0 * (back_to_back_penalty + (regression["volatility_score"] * 6.0))

        adjusted_strength = float(base_strength + adjustment + fatigue_penalty)

        return {
            "base_strength": float(base_strength),
            "adjusted_strength": adjusted_strength,
            "goalie_adjustment": float(adjustment),
            "fatigue_penalty": float(fatigue_penalty),
            "goalie_signal": str(regression["signal"]),
            "goalie_volatility": float(regression["volatility_score"]),
            "confidence": float(regression["confidence"]),
        }

    @staticmethod
    def calculate_team_strength(
        goals_for: float,
        goals_against: float,
        xg_for: float,
        xg_against: float,
        corsi_pct: float,
        pdo: float,
        recent_form: Optional[List[int]] = None,
    ) -> Dict[str, float | str]:
        """Estimate overall team strength from key metrics."""
        recent_form = recent_form or []
        recent_win_rate = sum(recent_form) / len(recent_form) if recent_form else 0.5

        rating = 50.0
        rating += (goals_for - goals_against) * 8.0
        rating += (xg_for - xg_against) * 5.0
        rating += (corsi_pct - 50.0) * 0.8
        rating += (pdo - 100.0) * 0.6
        rating += (recent_win_rate - 0.5) * 20.0

        if rating >= 70:
            tier = "elite"
        elif rating >= 60:
            tier = "strong"
        elif rating >= 50:
            tier = "average"
        elif rating >= 40:
            tier = "weak"
        else:
            tier = "poor"

        pdo_regression_expected = max(0.0, pdo - NHLConstants.AVG_PDO)

        return {
            "strength_rating": float(rating),
            "tier": tier,
            "recent_form_win_rate": float(recent_win_rate),
            "pdo_regression_expected": float(pdo_regression_expected),
        }

    @staticmethod
    def calculate_first_period_probability(
        home_goals_avg: float,
        away_goals_avg: float,
        total_line: float = 1.5,
        first_period_share: float = 0.3,
    ) -> Dict[str, float]:
        """Estimate first period win/draw probabilities and totals."""
        home_lambda = home_goals_avg * first_period_share
        away_lambda = away_goals_avg * first_period_share
        total_lambda = home_lambda + away_lambda

        if PoissonCalculator is not None:
            results = PoissonCalculator.calculate_match_probabilities(home_lambda, away_lambda, max_goals=8)
            home_win = results["home_win"]
            away_win = results["away_win"]
            draw = results["draw"]
        else:
            home_win = 0.5
            away_win = 0.3
            draw = 0.2

        scoreless_probability = math.exp(-total_lambda)
        over_total = _poisson_prob_over_line(total_lambda, total_line)
        under_total = _poisson_prob_under_line(total_lambda, total_line)

        return {
            "home_win_1p": float(home_win),
            "away_win_1p": float(away_win),
            "draw_1p": float(draw),
            "scoreless_probability": float(scoreless_probability),
            "expected_goals_1p": float(total_lambda),
            "over_total": float(over_total),
            "under_total": float(under_total),
        }

    @staticmethod
    def calculate_score_adjusted_corsi(
        shots_for: int,
        shots_against: int,
        blocked_for: int,
        blocked_against: int,
        missed_for: int,
        missed_against: int,
        goal_differential: int,
        time_trailing: float = 0.0,
        time_leading: float = 0.0,
        time_tied: float = 0.0,
    ) -> Dict[str, float]:
        corsi = NHLAdvancedAnalytics.calculate_corsi_fenwick(
            shots_for,
            shots_against,
            blocked_for,
            blocked_against,
            missed_for,
            missed_against,
        )
        raw_corsi_pct = corsi["corsi_percentage"]
        total_time = time_trailing + time_leading + time_tied
        if total_time <= 0:
            total_time = 60.0

        score_effect = (time_leading - time_trailing) / total_time
        adjustment = score_effect * 5.0  # percent points
        adjusted_corsi_pct = max(0.0, min(100.0, raw_corsi_pct + adjustment))

        return {
            "raw_corsi_pct": float(raw_corsi_pct),
            "adjusted_corsi_pct": float(adjusted_corsi_pct),
            "score_effect": float(score_effect),
            "goal_differential": float(goal_differential),
        }

    @staticmethod
    def calculate_player_prop_probability(
        player_avg: float,
        prop_line: float,
        stat_type: str = "goals",
        opponent_adjustment: float = 1.0,
        home_ice: bool = False,
    ) -> Dict[str, float | str]:
        """Estimate player prop probabilities."""
        adjusted_average = player_avg * opponent_adjustment * (1.05 if home_ice else 1.0)

        if stat_type in {"saves"}:
            std_dev = max(1.0, adjusted_average * 0.2)
            z = (prop_line - adjusted_average) / std_dev
            under = 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
            over = 1.0 - under
            push = 0.0
        else:
            over = _poisson_prob_over_line(adjusted_average, prop_line)
            under = _poisson_prob_under_line(adjusted_average, prop_line)
            push = _poisson_prob_push(adjusted_average, prop_line)

        if over - under > 0.05:
            recommendation = "over"
        elif under - over > 0.05:
            recommendation = "under"
        else:
            recommendation = "no_edge"

        return {
            "adjusted_average": float(adjusted_average),
            "over_probability": float(over),
            "under_probability": float(under),
            "push_probability": float(push),
            "recommendation": recommendation,
        }

    @staticmethod
    def analyze_betting_edge(
        predicted_probability: float,
        offered_odds: float,
        confidence_interval: Tuple[float, float],
        bankroll: float,
        use_kelly: bool = True,
    ) -> Dict[str, float | str]:
        implied_prob = 1.0 / offered_odds
        edge = predicted_probability - implied_prob
        expected_value = (
            predicted_probability * (offered_odds - 1.0) - (1.0 - predicted_probability)
        )
        if use_kelly:
            kelly_fraction = max(expected_value / (offered_odds - 1.0), 0.0)
        else:
            kelly_fraction = 0.0

        if edge >= 0.05:
            recommendation = "strong_bet"
        elif edge >= 0.01:
            recommendation = "value_bet"
        else:
            recommendation = "pass"

        return {
            "edge_percentage": float(edge * 100.0),
            "expected_value_pct": float(expected_value * 100.0),
            "kelly_fraction": float(kelly_fraction),
            "bet_recommendation": recommendation,
            "confidence_interval": confidence_interval,
            "bankroll": float(bankroll),
        }

    @staticmethod
    def calculate_live_betting_edge(
        current_score_home: int,
        current_score_away: int,
        time_remaining_mins: float,
        home_team_strength: float,
        away_team_strength: float,
        live_odds: Dict[str, float],
    ) -> Dict[str, float | str]:
        score_diff = current_score_home - current_score_away
        strength_delta = home_team_strength - away_team_strength
        time_weight = max(0.0, min(1.0, (60.0 - time_remaining_mins) / 60.0))

        home_prob = 0.5 + strength_delta * 0.5 + score_diff * 0.05 * (1.0 + time_weight)
        home_prob = max(0.01, min(0.99, home_prob))
        away_prob = 1.0 - home_prob

        implied_home = 1.0 / live_odds.get("home", 1.0)
        implied_away = 1.0 / live_odds.get("away", 1.0)
        home_edge = home_prob - implied_home
        away_edge = away_prob - implied_away
        if home_edge > away_edge:
            best_bet = "home"
        elif away_edge > home_edge:
            best_bet = "away"
        else:
            best_bet = "no_edge"

        return {
            "home_win_probability": float(home_prob),
            "away_win_probability": float(away_prob),
            "best_bet": best_bet,
            "home_edge": float(home_edge),
            "away_edge": float(away_edge),
        }

    @staticmethod
    def calculate_power_play_value(
        pp_opportunities: int,
        pp_goals: int,
        league_avg_pp_pct: float = 0.20,
    ) -> Dict[str, float]:
        if pp_opportunities <= 0:
            pp_pct = 0.0
        else:
            pp_pct = pp_goals / pp_opportunities
        return {
            "pp_percentage": float(pp_pct * 100.0),
            "pp_differential": float(pp_pct - league_avg_pp_pct),
        }

    @staticmethod
    def predict_game_ml(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
        home_goalie: GoaltenderStats,
        away_goalie: GoaltenderStats,
    ) -> Dict[str, float]:
        home_xg = (home_team.goals_for + home_team.xg_for) / 2.0
        away_xg = (away_team.goals_for + away_team.xg_for) / 2.0
        home_xg += NHLConstants.AVG_HOME_ADVANTAGE

        home_xg, away_xg = NHLAdvancedAnalytics.adjust_for_goalies(
            home_xg,
            away_xg,
            home_gsax=home_goalie.games_saved_above_expected,
            away_gsax=away_goalie.games_saved_above_expected,
        )

        results = NHLAdvancedAnalytics.predict_game_from_xg(home_xg, away_xg)
        return {
            "home_win_probability": float(results["home_win_probability"]),
            "away_win_probability": float(results["away_win_probability"]),
        }

    @staticmethod
    def adjust_for_goalies(
        home_xg: float,
        away_xg: float,
        home_gsax: float = 0.0,
        away_gsax: float = 0.0,
        league_gsax_avg: float = NHLConstants.LEAGUE_GSAX_AVG,
        impact_per_gsax: float = 0.16,
    ) -> Tuple[float, float]:
        """
        Better goalie (higher GSAx) lowers opponent expected goals.
        """
        home_adj = 1.0 - (home_gsax - league_gsax_avg) * impact_per_gsax
        away_adj = 1.0 - (away_gsax - league_gsax_avg) * impact_per_gsax

        home_adj = max(0.75, min(home_adj, 1.25))
        away_adj = max(0.75, min(away_adj, 1.25))

        adj_home = home_xg * away_adj
        adj_away = away_xg * home_adj

        adj_home = max(0.5, min(adj_home, 5.5))
        adj_away = max(0.5, min(adj_away, 5.5))
        return float(adj_home), float(adj_away)

    @staticmethod
    def predict_game_from_xg(
        home_xg: float,
        away_xg: float,
        include_overtime: bool = True,
        max_goals: int = 10,
    ) -> Dict[str, float]:
        """
        Uses PoissonCalculator if present; otherwise uses a small internal approximation.
        Returns home/away win probabilities + expected totals.

        Note: This method is "engine room" and does not attempt to expose
        full regulation vs OT breakdown unless PoissonCalculator provides it.
        """
        if PoissonCalculator is not None:
            res = PoissonCalculator.calculate_match_probabilities(home_xg, away_xg, max_goals=max_goals)
            ot_split = res["draw"] * 0.5 if include_overtime else 0.0
            return {
                "home_win_probability": float(res["home_win"] + ot_split),
                "away_win_probability": float(res["away_win"] + ot_split),
                "overtime_probability": float(res["draw"]),
                "expected_home_goals": float(home_xg),
                "expected_away_goals": float(away_xg),
                "expected_total": float(home_xg + away_xg),
                # optional regulation breakdown when available
                "regulation_home_win": float(res["home_win"]),
                "regulation_away_win": float(res["away_win"]),
            }

        # fallback: crude normal approximation (kept simple)
        mu = home_xg - away_xg
        sigma = math.sqrt(max(0.25, home_xg + away_xg))
        z = mu / sigma
        p_home_reg = 0.5 * (1.0 + math.erf(z / math.sqrt(2)))
        p_home = p_home_reg + (1.0 - p_home_reg) * 0.5 if include_overtime else p_home_reg
        p_home = max(0.01, min(0.99, p_home))
        return {
            "home_win_probability": float(p_home),
            "away_win_probability": float(1.0 - p_home),
            "overtime_probability": 0.0,
            "expected_home_goals": float(home_xg),
            "expected_away_goals": float(away_xg),
            "expected_total": float(home_xg + away_xg),
            "regulation_home_win": float(p_home_reg),
            "regulation_away_win": float(1.0 - p_home_reg),
        }


# ============================================================
# 2) NHLAnalytics (LEGACY, backward compatible)
# ============================================================

class NHLAnalytics:
    """
    Backward compatible helper surface.

    IMPORTANT:
    - Keep these signatures stable if other scripts call them.
    - Legacy tools often expect:
        win_probability, regulation_win_probability, overtime_probability, loss_probability
    """
    AVG_HOME_ADVANTAGE = NHLConstants.AVG_HOME_ADVANTAGE

    @staticmethod
    def calculate_moneyline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        is_home: bool = True,
        include_overtime: bool = True,
        max_goals: int = 10,
    ) -> Dict[str, float]:
        """
        Legacy moneyline probability.

        Fixes two common pitfalls:
        - Includes 'regulation_win_probability' key expected by analyzer tooling
        - Applies home advantage to the actual home side even when is_home=False
        """
        home_adv = NHLAnalytics.AVG_HOME_ADVANTAGE

        # Apply home advantage to whoever is home
        if is_home:
            home_lambda = float(team_goals_avg) + home_adv
            away_lambda = float(opponent_goals_avg)
        else:
            home_lambda = float(opponent_goals_avg) + home_adv
            away_lambda = float(team_goals_avg)

        # Best path: PoissonCalculator provides regulation + draw explicitly
        if PoissonCalculator is not None:
            res = PoissonCalculator.calculate_match_probabilities(home_lambda, away_lambda, max_goals=max_goals)

            reg_win = float(res["home_win"] if is_home else res["away_win"])
            reg_loss = float(res["away_win"] if is_home else res["home_win"])
            ot_prob = float(res["draw"])

            if include_overtime:
                win = reg_win + ot_prob * 0.5
                loss = reg_loss + ot_prob * 0.5
            else:
                win = reg_win
                loss = reg_loss

            return {
                "win_probability": float(win),
                "regulation_win_probability": float(reg_win),
                "overtime_probability": float(ot_prob),
                "loss_probability": float(loss),
                "expected_total": float(home_lambda + away_lambda),
            }

        # Fallback: use engine approximation
        out = NHLAdvancedAnalytics.predict_game_from_xg(
            home_xg=home_lambda,
            away_xg=away_lambda,
            include_overtime=include_overtime,
            max_goals=max_goals,
        )

        win_prob = out["home_win_probability"] if is_home else out["away_win_probability"]
        reg_win = out.get("regulation_home_win", win_prob) if is_home else out.get("regulation_away_win", 1.0 - win_prob)
        loss_prob = 1.0 - win_prob

        return {
            "win_probability": float(win_prob),
            "regulation_win_probability": float(reg_win),
            "overtime_probability": float(out.get("overtime_probability", 0.0)),
            "loss_probability": float(loss_prob),
            "expected_total": float(team_lambda + opp_lambda),
        }

    @staticmethod
    def calculate_puckline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        puckline: float = -1.5,
        is_home: bool = True,
        max_goals: int = 10,
    ) -> Dict[str, float]:
        """
        Legacy puckline cover probability.
        """
        home_adv = NHLAnalytics.AVG_HOME_ADVANTAGE

        if is_home:
            team_lambda = float(team_goals_avg) + home_adv
            opp_lambda = float(opponent_goals_avg)
        else:
            team_lambda = float(team_goals_avg)
            opp_lambda = float(opponent_goals_avg) + home_adv

        # best if PoissonCalculator exists (needs prob_matrix)
        if PoissonCalculator is not None:
            res = PoissonCalculator.calculate_match_probabilities(team_lambda, opp_lambda, max_goals=max_goals)
            matrix = res.get("prob_matrix")
            if matrix is not None:
                cover_prob = 0.0
                for tg in range(len(matrix)):
                    for og in range(len(matrix[0])):
                        margin = tg - og
                        if puckline < 0:
                            if margin > abs(puckline):
                                cover_prob += matrix[tg][og]
                        else:
                            if margin + puckline > 0:
                                cover_prob += matrix[tg][og]
                return {
                    "cover_probability": float(cover_prob),
                    "puckline": float(puckline),
                    "expected_margin": float(team_lambda - opp_lambda),
                }

        # fallback: logistic on expected margin
        margin = team_lambda - opp_lambda
        line_adj = 0.35 if puckline < 0 else -0.20
        p = 1.0 / (1.0 + math.exp(-0.85 * (margin + line_adj)))
        p = max(0.01, min(0.99, p))
        return {
            "cover_probability": float(p),
            "puckline": float(puckline),
            "expected_margin": float(margin),
        }

    @staticmethod
    def calculate_total_probability(
        team1_goals_avg: float,
        team2_goals_avg: float,
        total_line: float,
        goalie_adjustment: float = 1.0,
        referee_adjustment: float = 1.0,
        max_goals_sum: int = 25,
    ) -> Dict[str, float]:
        """
        Legacy over/under probability.
        """
        total_lambda = (
            (float(team1_goals_avg) + float(team2_goals_avg))
            * float(goalie_adjustment)
            * float(referee_adjustment)
        )

        # use calculator if present and compatible; otherwise internal Poisson sums
        if PoissonCalculator is not None and hasattr(PoissonCalculator, "calculate_total_probabilities"):
            try:
                res = PoissonCalculator.calculate_total_probabilities(
                    total_lambda / 2.0, total_lambda / 2.0, total_line, max_goals=12
                )
                return {
                    "over_probability": float(res["over_probability"]),
                    "under_probability": float(res["under_probability"]),
                    "expected_total": float(total_lambda),
                    "line": float(total_line),
                    "goalie_adjustment": float(goalie_adjustment),
                    "referee_adjustment": float(referee_adjustment),
                }
            except Exception:
                pass

        p_over = _poisson_prob_over_line(total_lambda, total_line, max_k=max_goals_sum)
        p_under = _poisson_prob_under_line(total_lambda, total_line, max_k=max_goals_sum)
        return {
            "over_probability": float(p_over),
            "under_probability": float(p_under),
            "expected_total": float(total_lambda),
            "line": float(total_line),
            "goalie_adjustment": float(goalie_adjustment),
            "referee_adjustment": float(referee_adjustment),
        }

    @staticmethod
    def simulate_game(home_goals_avg: float, away_goals_avg: float, seed: Optional[int] = None) -> Dict[str, Any]:
        """
        Legacy simulation.
        """
        if seed is not None:
            random.seed(seed)

        home_lambda = float(home_goals_avg) + NHLAnalytics.AVG_HOME_ADVANTAGE
        away_lambda = float(away_goals_avg)

        # If PoissonCalculator exists, use it
        if PoissonCalculator is not None and hasattr(PoissonCalculator, "simulate_match"):
            sim = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed)
            home_score = int(sim.get("home_score", 0))
            away_score = int(sim.get("away_score", 0))
            overtime = sim.get("result") == "draw"
            return {
                "home_score": home_score,
                "away_score": away_score,
                "total_goals": home_score + away_score,
                "margin": home_score - away_score,
                "regulation_result": sim.get("result"),
                "overtime": overtime,
            }

        # fallback sampling
        def sample_poisson(lam: float) -> int:
            # Knuth algorithm
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= random.random()
            return k - 1

        home_score = sample_poisson(home_lambda)
        away_score = sample_poisson(away_lambda)
        overtime = home_score == away_score
        return {
            "home_score": int(home_score),
            "away_score": int(away_score),
            "total_goals": int(home_score + away_score),
            "margin": int(home_score - away_score),
            "regulation_result": "home_win" if home_score > away_score else "away_win" if away_score > home_score else "draw",
            "overtime": overtime,
        }


# ============================================================
# 3) NHLBettingInterface (SportsBetLang-facing surface)
# ============================================================

@dataclass
class BetResult:
    bet_type: str                 # "MONEY" | "SPREAD" | "TOTAL"
    pick: str                     # "HOME", "AWAY", "HOME -1.5", "UNDER 6.5"
    prob: float                   # win probability for THIS pick
    fair_odds: int                # fair American odds
    market_odds: Optional[float]  # market American odds if supplied
    implied_prob: Optional[float]
    edge: Optional[float]
    ev_per_1: Optional[float]     # EV per $1 risked
    details: Dict[str, Any]


class NHLBettingInterface:
    """
    SportsBetLang-friendly wrapper.
    NO ensemble object required: pass your 3 models directly (optional).

    Expected (flexible) model method names:
      - moneyline: predict_moneyline / predict_game / predict
        returning dict with home prob key:
          'home_win_prob' OR 'home_win_probability' OR 'p_home' OR 'home_prob'
      - spread: predict_spread / predict_puckline
        returning dict with:
          'home_cover_prob' OR 'cover_probability' (for home side)
      - expected goals (optional): predict_expected_goals / predict_xg / expected_goals
        returning dict with: home_xg, away_xg
    """

    def __init__(
        self,
        power_model: Optional[Any] = None,
        similar_model: Optional[Any] = None,
        tree_model: Optional[Any] = None,
    ):
        self.power = power_model
        self.similar = similar_model
        self.tree = tree_model

    # ---------- MONEY ----------
    def predict_moneyline(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, BetResult]:
        votes, probs, raw = self._collect_moneyline(home_team, away_team, features)
        p_home = self._avg_or_default(probs, 0.5)
        p_home = self._clamp(p_home, 0.01, 0.99)
        p_away = 1.0 - p_home

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "model_probs_home": probs,
            "model_votes": votes,
            "convergence": self._convergence(votes),
            "raw": raw,
        }

        return {
            "HOME": self._make("MONEY", "HOME", p_home, market_home_odds, details),
            "AWAY": self._make("MONEY", "AWAY", p_away, market_away_odds, details),
        }

    # ---------- SPREAD ----------
    def predict_spread(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        line_home: float,
        line_away: float,
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, BetResult]:
        votes, probs, raw = self._collect_spread(home_team, away_team, features, line_home, line_away)
        p_home_cover = self._avg_or_default(probs, 0.5)
        p_home_cover = self._clamp(p_home_cover, 0.01, 0.99)
        p_away_cover = 1.0 - p_home_cover

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "line_home": line_home,
            "line_away": line_away,
            "model_probs_home_cover": probs,
            "model_votes": votes,
            "convergence": self._convergence(votes),
            "raw": raw,
        }

        return {
            "HOME": self._make("SPREAD", f"HOME {line_home:+.1f}", p_home_cover, market_home_odds, details),
            "AWAY": self._make("SPREAD", f"AWAY {line_away:+.1f}", p_away_cover, market_away_odds, details),
        }

    # ---------- TOTAL ----------
    def predict_total(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        total_line: float,
        market_over_odds: Optional[float] = None,
        market_under_odds: Optional[float] = None,
        max_goals_sum: int = 25,
    ) -> Dict[str, BetResult]:
        home_xg, away_xg, src = self._expected_goals(home_team, away_team, features)
        lam_total = home_xg + away_xg

        p_over = _poisson_prob_over_line(lam_total, total_line, max_k=max_goals_sum)
        p_under = _poisson_prob_under_line(lam_total, total_line, max_k=max_goals_sum)
        p_push = _poisson_prob_push(lam_total, total_line)

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "home_xg": home_xg,
            "away_xg": away_xg,
            "expected_total": lam_total,
            "total_line": total_line,
            "p_push": p_push,
            "xg_source": src,
        }

        return {
            "OVER": self._make("TOTAL", f"OVER {total_line:.1f}", float(p_over), market_over_odds, details),
            "UNDER": self._make("TOTAL", f"UNDER {total_line:.1f}", float(p_under), market_under_odds, details),
        }

    # ----------------------------
    # Internal: model calls + extraction
    # ----------------------------

    def _collect_moneyline(
        self, home: str, away: str, features: Dict[str, float]
    ) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
        votes: Dict[str, str] = {}
        probs: Dict[str, float] = {}
        raw: Dict[str, Any] = {}

        for name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(model, ["predict_moneyline", "predict_game", "predict"], home, away, features)
            raw[name] = out
            p = self._extract_home_prob(out)
            if p is not None:
                probs[name] = p
                votes[name] = "HOME" if p >= 0.5 else "AWAY"

        return votes, probs, raw

    def _collect_spread(
        self, home: str, away: str, features: Dict[str, float], line_home: float, line_away: float
    ) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
        votes: Dict[str, str] = {}
        probs: Dict[str, float] = {}
        raw: Dict[str, Any] = {}

        for name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(
                model,
                ["predict_spread", "predict_puckline", "predict_game", "predict"],
                home, away, features, line_home, line_away
            )
            raw[name] = out
            p = self._extract_home_cover_prob(out)
            if p is not None:
                probs[name] = p
                votes[name] = f"HOME {line_home:+.1f}" if p >= 0.5 else f"AWAY {line_away:+.1f}"

        return votes, probs, raw

    def _expected_goals(self, home: str, away: str, features: Dict[str, float]) -> Tuple[float, float, str]:
        # ask models first
        for name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(model, ["predict_expected_goals", "predict_xg", "expected_goals"], home, away, features)
            if isinstance(out, dict) and out.get("home_xg") is not None and out.get("away_xg") is not None:
                return float(out["home_xg"]), float(out["away_xg"]), f"{name}.model"

        # feature proxy fallback:
        base_total = float(features.get("xgf_total_proxy", NHLConstants.AVG_TOTAL_GOALS))
        total = 0.65 * NHLConstants.AVG_TOTAL_GOALS + 0.35 * base_total

        home_adv = float(features.get("home_advantage", NHLConstants.AVG_HOME_ADVANTAGE))
        gsax_diff = float(features.get("gsax_diff", 0.0))
        referee_goal_modifier = float(features.get("referee_goal_modifier", 1.0))
        referee_home_bias = float(features.get("referee_home_bias", 0.0))

        strength = float(features.get("xgf_diff", features.get("xg_diff", 0.0)))

        total *= self._clamp(referee_goal_modifier, 0.85, 1.15)

        share = 0.5 + 0.06 * strength + 0.05 * home_adv + 0.05 * gsax_diff + 0.03 * referee_home_bias
        share = self._clamp(share, 0.35, 0.65)

        home_xg = total * share
        away_xg = total - home_xg
        home_xg = self._clamp(home_xg, 1.2, 5.5)
        away_xg = self._clamp(away_xg, 1.2, 5.5)
        return float(home_xg), float(away_xg), "feature_proxy"

    @staticmethod
    def _safe_call(model: Any, method_names: List[str], *args) -> Any:
        for m in method_names:
            if hasattr(model, m):
                fn = getattr(model, m)
                try:
                    return fn(*args)
                except TypeError:
                    # some models accept fewer args
                    try:
                        return fn(*args[:2])
                    except Exception:
                        continue
                except Exception:
                    continue
        return None

    @staticmethod
    def _extract_home_prob(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for k in ("home_win_prob", "home_win_probability", "p_home", "home_prob", "prob_home"):
            if k in out and out[k] is not None:
                try:
                    return float(out[k])
                except Exception:
                    return None
        return None

    @staticmethod
    def _extract_home_cover_prob(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for k in ("home_cover_prob", "cover_probability", "p_home_cover"):
            if k in out and out[k] is not None:
                try:
                    return float(out[k])
                except Exception:
                    return None
        return None

    # ----------------------------
    # Output builder
    # ----------------------------

    def _make(self, bet_type: str, pick: str, prob: float, market_odds: Optional[float], details: Dict[str, Any]) -> BetResult:
        prob = self._clamp(float(prob), 0.001, 0.999)
        fair = prob_to_american(prob)

        implied = edge = ev = None
        if market_odds is not None:
            implied = american_to_implied_prob(float(market_odds))
            edge = prob - implied
            ev = expected_value_per_1_risk(prob, float(market_odds))

        return BetResult(
            bet_type=bet_type,
            pick=pick,
            prob=prob,
            fair_odds=fair,
            market_odds=market_odds,
            implied_prob=implied,
            edge=edge,
            ev_per_1=ev,
            details=details,
        )

    @staticmethod
    def _avg_or_default(d: Dict[str, float], default: float) -> float:
        if not d:
            return default
        return sum(d.values()) / float(len(d))

    @staticmethod
    def _convergence(votes: Dict[str, str]) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for v in votes.values():
            counts[v] = counts.get(v, 0) + 1
        best = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
        return {"counts": counts, "best_pick": best, "max_count": counts.get(best, 0) if best else 0}

    @staticmethod
    def _clamp(x: float, lo: float, hi: float) -> float:
        return float(max(lo, min(hi, x)))


# ----------------------------
# Tiny smoke test (optional)
# ----------------------------
if __name__ == "__main__":
    print("Loaded nhl_analytics.py (legacy + SportsBetLang interface)")
    print("Legacy NHLAnalytics exists:", hasattr(NHLAnalytics, "calculate_moneyline_probability"))
    print("SportsBetLang wrapper exists:", NHLBettingInterface)
