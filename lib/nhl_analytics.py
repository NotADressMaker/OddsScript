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
    # Pace & Tempo fields
    shot_attempts_per_60: float = 60.0      # Corsi per 60 minutes
    rush_chances_per_60: float = 5.0        # Rush scoring chances per 60
    neutral_zone_transition_pct: float = 50.0  # NZ transition success %
    pp_opportunities_per_game: float = 3.0  # Avg PP opportunities per game
    xg_for_per_60: float = 0.0             # xG generated per 60 minutes (0 = use xg_for fallback)

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
    medium_danger_save_pct: float = 0.910
    low_danger_save_pct: float = 0.980
    career_save_pct: Optional[float] = None
    career_high_danger_save_pct: Optional[float] = None
    career_medium_danger_save_pct: Optional[float] = None
    career_low_danger_save_pct: Optional[float] = None
    recent_high_danger_save_pct: Optional[float] = None
    recent_medium_danger_save_pct: Optional[float] = None
    recent_low_danger_save_pct: Optional[float] = None
    recent_save_percentage: Optional[float] = None
    season_high_danger_save_pct: Optional[float] = None   # Full-season HDS% for shrinkage
    season_low_danger_save_pct: Optional[float] = None     # Full-season LDS% for shrinkage
    games_started: int = 0
    quality_starts: int = 0
    games_saved_above_expected: float = 0.0  # total GSAx
    starts_last_7: int = 0
    back_to_back_starts: int = 0
    is_starter: bool = True
    is_back_to_back: bool = False  # Is this a B2B start today?


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
    def calculate_adjusted_goalie_save_pct(
        goalie: GoaltenderStats,
        league_avg_sv_pct: float = 0.905,
    ) -> Dict[str, float | str]:
        """
        Calculate goalie adjusted save % weighted by shot quality zones.

        Weights high-danger save % more heavily since it correlates
        with true goalie skill more than low-danger save %.
        """
        hd_weight = 0.45
        md_weight = 0.30
        ld_weight = 0.25

        hd = goalie.high_danger_save_pct
        md = goalie.medium_danger_save_pct
        ld = goalie.low_danger_save_pct

        adjusted_sv_pct = (hd * hd_weight) + (md * md_weight) + (ld * ld_weight)

        # Compare to career norms for regression signal
        career = goalie.career_save_pct if goalie.career_save_pct is not None else league_avg_sv_pct
        deviation_from_career = adjusted_sv_pct - career
        deviation_from_league = adjusted_sv_pct - league_avg_sv_pct

        if deviation_from_career > 0.015:
            sustainability = "unsustainable_high"
        elif deviation_from_career < -0.015:
            sustainability = "unsustainable_low"
        else:
            sustainability = "sustainable"

        return {
            "adjusted_save_pct": float(adjusted_sv_pct),
            "raw_save_pct": float(goalie.save_percentage),
            "deviation_from_career": float(deviation_from_career),
            "deviation_from_league": float(deviation_from_league),
            "sustainability": sustainability,
            "high_danger_sv": float(hd),
            "medium_danger_sv": float(md),
            "low_danger_sv": float(ld),
        }

    @staticmethod
    def calculate_pp_pk_efficiency(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
        league_avg_pp: float = 20.0,
        league_avg_pk: float = 80.0,
    ) -> Dict[str, float]:
        """
        Calculate PP/PK efficiency matchup and its impact on expected goals.

        PP efficiency above average vs weak PK = goals added.
        Strong PK vs average PP = goals suppressed.
        """
        home_pp = home_team.pp_pct
        away_pk = away_team.pk_pct
        away_pp = away_team.pp_pct
        home_pk = home_team.pk_pct

        # PP conversion: goals added per game from PP advantage
        # Avg ~3 PP opportunities/game, each opportunity ~2 min
        home_pp_opp = home_team.pp_opportunities_per_game
        away_pp_opp = away_team.pp_opportunities_per_game

        # Home PP vs Away PK: expected PP goals
        home_pp_rate = home_pp / 100.0
        away_pk_allow_rate = 1.0 - (away_pk / 100.0)
        home_pp_xg = home_pp_opp * (home_pp_rate + away_pk_allow_rate) / 2.0

        # Away PP vs Home PK: expected PP goals
        away_pp_rate = away_pp / 100.0
        home_pk_allow_rate = 1.0 - (home_pk / 100.0)
        away_pp_xg = away_pp_opp * (away_pp_rate + home_pk_allow_rate) / 2.0

        # Total PP goals expected in game
        total_pp_xg = home_pp_xg + away_pp_xg

        # Differential: positive = home special teams advantage
        pp_pk_differential = home_pp_xg - away_pp_xg

        # Relative to league average
        league_pp_rate = league_avg_pp / 100.0
        league_pk_rate = league_avg_pk / 100.0
        league_avg_pp_xg = 3.0 * (league_pp_rate + (1.0 - league_pk_rate)) / 2.0
        total_pp_xg_vs_avg = total_pp_xg - (2.0 * league_avg_pp_xg)

        return {
            "home_pp_expected_goals": float(home_pp_xg),
            "away_pp_expected_goals": float(away_pp_xg),
            "total_pp_expected_goals": float(total_pp_xg),
            "pp_pk_differential": float(pp_pk_differential),
            "total_pp_xg_vs_league_avg": float(total_pp_xg_vs_avg),
            "home_pp_pct": float(home_pp),
            "away_pk_pct": float(away_pk),
            "away_pp_pct": float(away_pp),
            "home_pk_pct": float(home_pk),
        }

    @staticmethod
    def calculate_enhanced_total(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
        home_goalie: GoaltenderStats,
        away_goalie: GoaltenderStats,
        total_line: float,
        home_rest_days: int = 1,
        away_rest_days: int = 1,
        home_is_road: bool = False,
        away_is_road: bool = True,
    ) -> Dict[str, Any]:
        """
        Enhanced O/U model incorporating:
        - xG (expected goals) for both teams
        - Fenwick/Corsi adjusted metrics
        - PP/PK efficiency matchup
        - Goalie adjusted save %
        - Rest/travel factors

        Returns true probability, true odds, and EV vs sportsbook line.
        """
        # 1. Base xG total
        base_home_xg = home_team.xg_for
        base_away_xg = away_team.xg_for

        # 2. Corsi/Fenwick pace adjustment
        # Higher Corsi/Fenwick % = more shot generation = more offensive opportunity
        home_corsi_factor = 1.0 + (home_team.corsi_pct - 50.0) * 0.005
        away_corsi_factor = 1.0 + (away_team.corsi_pct - 50.0) * 0.005
        home_fenwick_factor = 1.0 + (home_team.fenwick_for / max(1.0, home_team.fenwick_for + home_team.fenwick_against) - 0.5) * 0.3

        corsi_fenwick_adj = (home_corsi_factor + away_corsi_factor) / 2.0

        # 3. PP/PK efficiency
        pp_pk = NHLAdvancedAnalytics.calculate_pp_pk_efficiency(home_team, away_team)
        pp_xg_added = pp_pk["total_pp_xg_vs_league_avg"]

        # 4. Goalie adjusted save %
        home_goalie_adj = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(home_goalie)
        away_goalie_adj = NHLAdvancedAnalytics.calculate_adjusted_goalie_save_pct(away_goalie)

        # Goalie quality suppresses goals: better goalie = less goals against
        # Scale: 0.905 is league average; each 0.01 above = ~0.3 fewer goals
        home_goalie_impact = (0.905 - home_goalie_adj["adjusted_save_pct"]) * 30.0
        away_goalie_impact = (0.905 - away_goalie_adj["adjusted_save_pct"]) * 30.0

        # 5. Goalie regression check
        home_goalie_regression = NHLAdvancedAnalytics.detect_goalie_regression(home_goalie)
        away_goalie_regression = NHLAdvancedAnalytics.detect_goalie_regression(away_goalie)

        # If goalie is on a heater, expect regression toward more goals
        regression_adj = 0.0
        if home_goalie_regression["signal"] == "heater":
            regression_adj += 0.15
        elif home_goalie_regression["signal"] == "slump":
            regression_adj -= 0.10
        if away_goalie_regression["signal"] == "heater":
            regression_adj += 0.15
        elif away_goalie_regression["signal"] == "slump":
            regression_adj -= 0.10

        # 6. Rest/B2B adjustment
        rest_adj = 0.0
        if home_rest_days == 0:
            rest_adj -= 0.15  # Home B2B = tired, less offense
            if home_is_road:
                rest_adj -= 0.10  # B2B on road = even worse
        if away_rest_days == 0:
            rest_adj -= 0.15
            if away_is_road:
                rest_adj -= 0.10
        if home_rest_days >= 3:
            rest_adj += 0.08
        if away_rest_days >= 3:
            rest_adj += 0.08

        # B2B goalie rotation penalty
        if home_goalie.is_back_to_back:
            away_goalie_impact -= 0.20  # Backup goalie allows more goals
        if away_goalie.is_back_to_back:
            home_goalie_impact -= 0.20

        # 7. Home advantage
        home_adv = NHLConstants.AVG_HOME_ADVANTAGE

        # Assemble adjusted expected goals
        adj_home_xg = base_home_xg * corsi_fenwick_adj + home_adv + away_goalie_impact
        adj_away_xg = base_away_xg * corsi_fenwick_adj + home_goalie_impact

        # Add PP, regression, rest
        total_xg = adj_home_xg + adj_away_xg + pp_xg_added + regression_adj + rest_adj

        # Clamp to reasonable range
        total_xg = max(3.5, min(9.0, total_xg))
        adj_home_xg = max(1.0, min(5.5, total_xg * 0.52))
        adj_away_xg = max(1.0, min(5.5, total_xg - adj_home_xg))

        # Poisson probabilities
        p_over = _poisson_prob_over_line(total_xg, total_line)
        p_under = _poisson_prob_under_line(total_xg, total_line)
        p_push = _poisson_prob_push(total_xg, total_line)

        # True odds (fair odds with no vig)
        over_true_odds = prob_to_american(max(0.01, min(0.99, p_over))) if p_over > 0.01 else 10000
        under_true_odds = prob_to_american(max(0.01, min(0.99, p_under))) if p_under > 0.01 else 10000

        return {
            "expected_total": float(total_xg),
            "adjusted_home_xg": float(adj_home_xg),
            "adjusted_away_xg": float(adj_away_xg),
            "total_line": float(total_line),
            "over_probability": float(p_over),
            "under_probability": float(p_under),
            "push_probability": float(p_push),
            "over_true_odds": int(over_true_odds),
            "under_true_odds": int(under_true_odds),
            "components": {
                "base_xg_total": float(base_home_xg + base_away_xg),
                "corsi_fenwick_multiplier": float(corsi_fenwick_adj),
                "pp_pk_xg_added": float(pp_xg_added),
                "goalie_impact_home": float(home_goalie_impact),
                "goalie_impact_away": float(away_goalie_impact),
                "regression_adjustment": float(regression_adj),
                "rest_adjustment": float(rest_adj),
                "home_advantage": float(home_adv),
            },
            "goalie_sustainability": {
                "home": home_goalie_adj["sustainability"],
                "away": away_goalie_adj["sustainability"],
            },
            "goalie_regression": {
                "home_signal": str(home_goalie_regression["signal"]),
                "away_signal": str(away_goalie_regression["signal"]),
            },
        }

    @staticmethod
    def compare_vs_sportsbook(
        true_probability: float,
        sportsbook_odds: float,
    ) -> Dict[str, float | str | bool]:
        """
        Convert true probability to true odds, then compare vs sportsbook line
        to find +EV bets.

        Args:
            true_probability: Model's estimated probability (0-1)
            sportsbook_odds: Sportsbook's offered American odds

        Returns:
            Dict with edge, EV, true odds, and whether bet is +EV
        """
        true_prob = max(0.01, min(0.99, true_probability))
        true_odds = prob_to_american(true_prob)
        implied_prob = american_to_implied_prob(sportsbook_odds)
        edge = true_prob - implied_prob
        ev = expected_value_per_1_risk(true_prob, sportsbook_odds)

        is_positive_ev = ev > 0.0

        if edge >= 0.05:
            signal = "strong_bet"
        elif edge >= 0.02:
            signal = "value_bet"
        elif edge >= 0.0:
            signal = "marginal"
        else:
            signal = "no_edge"

        return {
            "true_probability": float(true_prob),
            "true_odds": int(true_odds),
            "sportsbook_odds": float(sportsbook_odds),
            "implied_probability": float(implied_prob),
            "edge": float(edge),
            "edge_pct": float(edge * 100.0),
            "ev_per_dollar": float(ev),
            "is_positive_ev": bool(is_positive_ev),
            "signal": signal,
        }

    @staticmethod
    def calculate_pace_tempo(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
    ) -> Dict[str, float | str]:
        """
        Factor in shot attempts per 60, rush chances, and neutral zone
        transition speed to assess game pace.

        Two high-tempo teams = Over lean.
        Slow + defensive teams = Under or derivative markets.
        """
        # Shot attempts per 60 (Corsi/60)
        home_sa60 = home_team.shot_attempts_per_60
        away_sa60 = away_team.shot_attempts_per_60
        avg_sa60 = (home_sa60 + away_sa60) / 2.0

        # Rush chances per 60
        home_rush = home_team.rush_chances_per_60
        away_rush = away_team.rush_chances_per_60
        avg_rush = (home_rush + away_rush) / 2.0

        # Neutral zone transition %
        home_nz = home_team.neutral_zone_transition_pct
        away_nz = away_team.neutral_zone_transition_pct
        avg_nz = (home_nz + away_nz) / 2.0

        # Pace score: composite of shot rate, rush chances, and NZ transitions
        # Normalized: 60 SA/60 is average, 5 rush/60 is average, 50% NZ is average
        sa_score = (avg_sa60 - 60.0) / 10.0   # each 10 SA above avg = +1
        rush_score = (avg_rush - 5.0) / 2.0    # each 2 rush above avg = +1
        nz_score = (avg_nz - 50.0) / 10.0      # each 10% NZ above avg = +1

        pace_score = sa_score * 0.45 + rush_score * 0.30 + nz_score * 0.25

        # Goal adjustment from pace
        # High pace adds ~0.3 goals per point of pace score
        pace_goal_adjustment = pace_score * 0.30

        # Classification
        if pace_score >= 1.0:
            tempo = "high"
            lean = "over"
        elif pace_score >= 0.3:
            tempo = "above_average"
            lean = "slight_over"
        elif pace_score <= -1.0:
            tempo = "low"
            lean = "under"
        elif pace_score <= -0.3:
            tempo = "below_average"
            lean = "slight_under"
        else:
            tempo = "average"
            lean = "neutral"

        # Derivative market signals
        derivative_signal = "none"
        if pace_score <= -0.8:
            derivative_signal = "1p_under_team_total_under"
        elif pace_score >= 1.2:
            derivative_signal = "1p_over_team_total_over"

        return {
            "pace_score": float(pace_score),
            "pace_goal_adjustment": float(pace_goal_adjustment),
            "tempo": tempo,
            "lean": lean,
            "derivative_signal": derivative_signal,
            "avg_shot_attempts_per_60": float(avg_sa60),
            "avg_rush_chances_per_60": float(avg_rush),
            "avg_nz_transition_pct": float(avg_nz),
            "components": {
                "sa_score": float(sa_score),
                "rush_score": float(rush_score),
                "nz_score": float(nz_score),
            },
        }

    @staticmethod
    def calculate_rest_travel_modifier(
        rest_days: int,
        is_road: bool,
        is_back_to_back: bool,
        goalie_is_backup: bool = False,
        travel_zones: int = 0,
        opponent_rest_days: int = 1,
        opponent_is_road: bool = False,
    ) -> Dict[str, float | str | bool]:
        """
        Rest vs Travel Modifier for NHL fatigue edge.

        Back-to-back on the road with goalie rotation? Fade spot.
        3+ days rest at home? Bet-on setup.
        """
        modifier = 0.0
        flags: List[str] = []

        # Rest advantage/disadvantage
        if is_back_to_back:
            modifier -= 0.20
            flags.append("back_to_back")
            if is_road:
                modifier -= 0.15
                flags.append("b2b_on_road")
            if goalie_is_backup:
                modifier -= 0.10
                flags.append("goalie_rotation")
        elif rest_days == 0:
            modifier -= 0.15
            flags.append("zero_rest")
        elif rest_days >= 3:
            modifier += 0.12
            flags.append("well_rested")
            if not is_road:
                modifier += 0.08
                flags.append("rested_at_home")

        # Travel zone penalty
        if travel_zones >= 3:
            modifier -= 0.12
            flags.append("cross_country_travel")
        elif travel_zones >= 2:
            modifier -= 0.06
            flags.append("significant_travel")
        elif travel_zones >= 1:
            modifier -= 0.03

        # Rest differential
        rest_diff = rest_days - opponent_rest_days
        if rest_diff >= 2:
            modifier += 0.08
        elif rest_diff <= -2:
            modifier -= 0.08

        # Classify the spot
        if is_back_to_back and is_road and goalie_is_backup:
            spot = "fade"
        elif rest_days >= 3 and not is_road:
            spot = "bet_on"
        elif modifier >= 0.15:
            spot = "positive"
        elif modifier <= -0.25:
            spot = "fade"
        elif modifier <= -0.10:
            spot = "caution"
        else:
            spot = "neutral"

        return {
            "modifier": float(modifier),
            "spot": spot,
            "is_back_to_back": bool(is_back_to_back),
            "is_road": bool(is_road),
            "goalie_is_backup": bool(goalie_is_backup),
            "rest_days": int(rest_days),
            "travel_zones": int(travel_zones),
            "rest_differential": int(rest_diff),
            "flags": flags,
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

    # ============================================================
    # V2 UPGRADED SIGNALS
    # ============================================================

    @staticmethod
    def detect_goalie_regression_v2(
        goalie: GoaltenderStats,
        hds_weight_last10: float = 0.50,
        hds_weight_season: float = 0.30,
        hds_weight_career: float = 0.20,
    ) -> Dict[str, Any]:
        """
        Goalie Regression Detection 2.0.

        Improvements over v1:
        - Shrinkage: blends last-10 with season and career baselines
        - Converts deviation into a goals-impact score (not just heater/slump label)
        - Fatigue/uncertainty penalty for B2B or heavy workload
        - Outputs both goalie_effect_xGA and goalie_variance

        adj_hds = 0.50*last10_hds + 0.30*season_hds + 0.20*career_hds
        regress_score = (adj_hds - career_hds)/0.03 * 0.7
                      + (adj_lds - career_lds)/0.01 * 0.3
        Clamped to [-1, +1].

        Positive goalie_effect_xGA = more goals allowed expected (Over lean).
        Negative = fewer goals allowed expected (Under lean).
        """
        # Career baselines (ultimate fallback)
        career_hds = goalie.career_high_danger_save_pct or goalie.high_danger_save_pct
        career_lds = goalie.career_low_danger_save_pct or goalie.low_danger_save_pct

        # Season baselines (fall back to career)
        season_hds = goalie.season_high_danger_save_pct or career_hds
        season_lds = goalie.season_low_danger_save_pct or career_lds

        # Last-10 / recent (fall back to season)
        last10_hds = goalie.recent_high_danger_save_pct or season_hds
        last10_lds = goalie.recent_low_danger_save_pct or season_lds

        # Shrinkage blend
        adj_hds = (
            hds_weight_last10 * last10_hds
            + hds_weight_season * season_hds
            + hds_weight_career * career_hds
        )
        adj_lds = (
            hds_weight_last10 * last10_lds
            + hds_weight_season * season_lds
            + hds_weight_career * career_lds
        )

        # Regress score: normalized deviation from career
        # HD deviations of 0.03 are significant; LD deviations of 0.01
        hd_component = (adj_hds - career_hds) / 0.03 * 0.7
        ld_component = (adj_lds - career_lds) / 0.01 * 0.3
        regress_score = max(-1.0, min(1.0, hd_component + ld_component))

        # Fatigue / uncertainty penalty
        fatigue_penalty = False
        if goalie.is_back_to_back or goalie.starts_last_7 >= 3:
            fatigue_penalty = True
            regress_score *= 0.6  # pull toward 0

        # Convert to goals impact
        # Positive regress_score = performing above career = heater =
        # expect regression toward more goals allowed
        goalie_effect_xGA = regress_score * 0.4

        # Variance: higher when uncertain
        base_variance = 0.3
        if fatigue_penalty:
            base_variance += 0.15
        if goalie.games_started < 10:
            base_variance += 0.15
        if not goalie.is_starter:
            base_variance += 0.20
        goalie_variance = min(1.0, base_variance + abs(regress_score) * 0.2)

        # Signal label
        if regress_score > 0.3:
            signal = "heater_regression_expected"
        elif regress_score < -0.3:
            signal = "slump_rebound_expected"
        else:
            signal = "stable"

        return {
            "goalie_effect_xGA": float(goalie_effect_xGA),
            "goalie_variance": float(goalie_variance),
            "regress_score": float(regress_score),
            "signal": signal,
            "adj_hds": float(adj_hds),
            "adj_lds": float(adj_lds),
            "career_hds": float(career_hds),
            "career_lds": float(career_lds),
            "fatigue_penalty_applied": fatigue_penalty,
            "is_starter": goalie.is_starter,
        }

    @staticmethod
    def calculate_pace_tempo_v2(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
    ) -> Dict[str, Any]:
        """
        Pace & Tempo 2.0: z-score-based tempo index.

        Builds a tempo index from:
        - xG_for_60 (or xg_for as fallback)
        - rush_chances_per_60
        - neutral_zone_transition_pct (NZ speed proxy)
        - pp_opportunities_per_game (penalties drawn)

        tempo = 0.40*z(xG60) + 0.25*z(rush) + 0.20*z(NZspeed) + 0.15*z(PPopp)

        Buckets:
        - High:  tempo >= +0.75
        - Low:   tempo <= -0.75

        Also computes mismatch: high-tempo offense vs slow defense.
        """
        # League averages and std devs for z-scoring (NHL baselines)
        XG60_MEAN, XG60_STD = 2.5, 0.5
        RUSH_MEAN, RUSH_STD = 5.0, 1.5
        NZ_MEAN, NZ_STD = 50.0, 5.0
        PP_MEAN, PP_STD = 3.0, 0.7

        def z(val: float, mean: float, std: float) -> float:
            return (val - mean) / std if std > 0 else 0.0

        # Use xg_for_per_60 if provided, otherwise fall back to xg_for
        home_xg60 = home_team.xg_for_per_60 if home_team.xg_for_per_60 > 0 else home_team.xg_for
        away_xg60 = away_team.xg_for_per_60 if away_team.xg_for_per_60 > 0 else away_team.xg_for

        # If still zero, use league average
        if home_xg60 <= 0:
            home_xg60 = XG60_MEAN
        if away_xg60 <= 0:
            away_xg60 = XG60_MEAN

        avg_xg60 = (home_xg60 + away_xg60) / 2.0
        avg_rush = (home_team.rush_chances_per_60 + away_team.rush_chances_per_60) / 2.0
        avg_nz = (home_team.neutral_zone_transition_pct + away_team.neutral_zone_transition_pct) / 2.0
        avg_pp = (home_team.pp_opportunities_per_game + away_team.pp_opportunities_per_game) / 2.0

        z_xg = z(avg_xg60, XG60_MEAN, XG60_STD)
        z_rush = z(avg_rush, RUSH_MEAN, RUSH_STD)
        z_nz = z(avg_nz, NZ_MEAN, NZ_STD)
        z_pp = z(avg_pp, PP_MEAN, PP_STD)

        tempo = 0.40 * z_xg + 0.25 * z_rush + 0.20 * z_nz + 0.15 * z_pp

        # Bucket classification
        if tempo >= 0.75:
            tempo_label = "high"
        elif tempo <= -0.75:
            tempo_label = "low"
        else:
            tempo_label = "neutral"

        # Mismatch detection: high-tempo offense vs slow defense
        GA_MEAN, GA_STD = 3.1, 0.4  # goals against baselines
        home_offense_z = z(home_xg60, XG60_MEAN, XG60_STD)
        away_offense_z = z(away_xg60, XG60_MEAN, XG60_STD)
        home_defense_z = z(home_team.goals_against, GA_MEAN, GA_STD)  # higher GA = weaker
        away_defense_z = z(away_team.goals_against, GA_MEAN, GA_STD)

        mismatch_score = 0.0
        mismatch_tags: List[str] = []

        if home_offense_z > 0.5 and away_defense_z > 0.5:
            mismatch_score += (home_offense_z + away_defense_z) / 2.0
            mismatch_tags.append("home_offense_vs_away_weak_defense")
        if away_offense_z > 0.5 and home_defense_z > 0.5:
            mismatch_score += (away_offense_z + home_defense_z) / 2.0
            mismatch_tags.append("away_offense_vs_home_weak_defense")

        # Tempo goal adjustment: each 1.0 of tempo index ~ 0.35 goals
        tempo_delta = tempo * 0.35

        return {
            "tempo_index": float(tempo),
            "tempo_label": tempo_label,
            "tempo_delta": float(tempo_delta),
            "mismatch_score": float(mismatch_score),
            "mismatch_tags": mismatch_tags,
            "z_scores": {
                "xg60": float(z_xg),
                "rush": float(z_rush),
                "nz_speed": float(z_nz),
                "pp_opp": float(z_pp),
            },
            "raw_averages": {
                "avg_xg60": float(avg_xg60),
                "avg_rush": float(avg_rush),
                "avg_nz": float(avg_nz),
                "avg_pp": float(avg_pp),
            },
        }

    @staticmethod
    def calculate_fatigue_severity(
        is_b2b: bool = False,
        games_4_nights: int = 0,
        travel_km: float = 0.0,
        time_zones_crossed: int = 0,
        home_rest_days: int = 1,
        is_road: bool = False,
        goalie_confirmed: bool = True,
    ) -> Dict[str, Any]:
        """
        Rest vs Travel Modifier 2.0: Fatigue Severity Score.

        Replaces binary B2B/travel flags with continuous severity scoring.
        Accounts for 3-in-4, time zones, travel distance, and home rest.

        fatigue = 0.50*b2b + 0.25*min(travel_km/1000,1) + 0.25*min(tz/2,1)
        rest_boost = 0.35*I(home_rest_days >= 3)

        Outputs:
        - fatigue_effect_team: hurts side/team total
        - fatigue_effect_total: pushes total (tired legs = more goals allowed,
          but also less finishing; net slight Over from defensive breakdowns)

        Rule-of-thumb tag:
        "Away B2B + >300km + unconfirmed goalie" = avoid/fade spot
        """
        b2b = 1.0 if is_b2b else 0.0

        travel_component = min(travel_km / 1000.0, 1.0)
        tz_component = min(time_zones_crossed / 2.0, 1.0)

        fatigue = 0.50 * b2b + 0.25 * travel_component + 0.25 * tz_component

        # Games-in-4-nights additional penalty
        if games_4_nights >= 3:
            fatigue += 0.30
        elif games_4_nights >= 2:
            fatigue += 0.10

        # Rest boost
        rest_boost = 0.35 if (home_rest_days >= 3 and not is_road) else 0.0

        # Net fatigue effect on team performance
        fatigue_effect_team = -(fatigue * 0.4) + rest_boost

        # Effect on total: tired teams allow more goals but finish less.
        # Net effect is slight push toward Over due to defensive breakdowns.
        fatigue_effect_total = fatigue * 0.15 - rest_boost * 0.10

        # Tags
        tags: List[str] = []
        is_avoid = False
        if is_b2b and is_road and not goalie_confirmed:
            tags.append("away_b2b_unconfirmed_goalie_avoid")
            is_avoid = True
        if is_b2b and is_road:
            tags.append("away_b2b_fade_spot")
        if is_b2b:
            tags.append("b2b")
        if games_4_nights >= 3:
            tags.append("3_in_4_heavy_schedule")
        if travel_km > 2000:
            tags.append("long_travel")
        if time_zones_crossed >= 2:
            tags.append("significant_timezone_change")
        if home_rest_days >= 3 and not is_road:
            tags.append("well_rested_at_home")

        return {
            "fatigue_score": float(fatigue),
            "fatigue_effect_team": float(fatigue_effect_team),
            "fatigue_effect_total": float(fatigue_effect_total),
            "rest_boost": float(rest_boost),
            "tags": tags,
            "is_avoid_spot": bool(is_avoid),
            "components": {
                "b2b": float(b2b),
                "travel_component": float(travel_component),
                "tz_component": float(tz_component),
                "games_4_nights_penalty": float(
                    0.30 if games_4_nights >= 3 else 0.10 if games_4_nights >= 2 else 0.0
                ),
            },
        }

    @staticmethod
    def calculate_composite_edge(
        home_team: TeamMetrics,
        away_team: TeamMetrics,
        home_goalie: GoaltenderStats,
        away_goalie: GoaltenderStats,
        line_total: float,
        model_total_mean: Optional[float] = None,
        total_sigma: float = 0.85,
        home_fatigue: Optional[Dict[str, Any]] = None,
        away_fatigue: Optional[Dict[str, Any]] = None,
        market_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Composite Edge 2.0: Convert all signals to projected total adjustment.

        Start with baseline total projection, then adjust:
          T = T0 + goalie_delta + tempo_delta + fatigue_delta + market_delta

        Then convert to bet decision:
          edge_points = T - line_total
          prob_over = NormalCDF(edge_points / total_sigma)

        Bet rules:
          - Bet Over  if prob_over >= 0.55 and CLV/sharp_move supports
          - Bet Under if prob_over <= 0.45

        Derivatives logic:
          - High tempo + goalie variance high => full-game total Over or live Over
          - Low tempo + strong goalie + rested => 1P Under, team total Under
        """
        # 1. Baseline
        T0 = model_total_mean if model_total_mean is not None else NHLConstants.AVG_TOTAL_GOALS

        # 2. Goalie deltas
        home_goalie_reg = NHLAdvancedAnalytics.detect_goalie_regression_v2(home_goalie)
        away_goalie_reg = NHLAdvancedAnalytics.detect_goalie_regression_v2(away_goalie)
        goalie_delta = home_goalie_reg["goalie_effect_xGA"] + away_goalie_reg["goalie_effect_xGA"]

        # 3. Tempo delta
        tempo = NHLAdvancedAnalytics.calculate_pace_tempo_v2(home_team, away_team)
        tempo_delta = tempo["tempo_delta"]

        # 4. Fatigue delta
        fatigue_delta = 0.0
        if home_fatigue:
            fatigue_delta += home_fatigue.get("fatigue_effect_total", 0.0)
        if away_fatigue:
            fatigue_delta += away_fatigue.get("fatigue_effect_total", 0.0)

        # 5. Market delta
        market_delta = 0.0
        if market_data:
            market_delta = market_data.get("market_delta", 0.0)

        # Projected total
        projected_total = T0 + goalie_delta + tempo_delta + fatigue_delta + market_delta
        projected_total = max(3.5, min(9.0, projected_total))

        # Edge
        edge_points = projected_total - line_total

        # Prob over via normal CDF
        z_val = edge_points / total_sigma
        prob_over = 0.5 * (1.0 + math.erf(z_val / math.sqrt(2)))

        # Confidence based on data completeness + variance
        confidence = 1.0
        if not home_goalie.is_starter:
            confidence -= 0.20
        if not away_goalie.is_starter:
            confidence -= 0.20
        if home_fatigue and home_fatigue.get("is_avoid_spot"):
            confidence -= 0.15
        if away_fatigue and away_fatigue.get("is_avoid_spot"):
            confidence -= 0.15
        avg_variance = (
            home_goalie_reg["goalie_variance"] + away_goalie_reg["goalie_variance"]
        ) / 2.0
        confidence -= avg_variance * 0.3
        confidence = max(0.1, min(1.0, confidence))

        # Tags
        tags: List[str] = []
        if home_goalie_reg["signal"] == "heater_regression_expected":
            tags.append("Home goalie heater likely to regress")
        if away_goalie_reg["signal"] == "heater_regression_expected":
            tags.append("Away goalie heater likely to regress")
        if home_goalie_reg["signal"] == "slump_rebound_expected":
            tags.append("Home goalie slump rebound expected")
        if away_goalie_reg["signal"] == "slump_rebound_expected":
            tags.append("Away goalie slump rebound expected")
        if tempo["tempo_label"] == "high":
            tags.append("High tempo matchup")
        if tempo["tempo_label"] == "low":
            tags.append("Low tempo matchup")
        if tempo["mismatch_tags"]:
            tags.extend(tempo["mismatch_tags"])
        if home_fatigue:
            tags.extend(home_fatigue.get("tags", []))
        if away_fatigue:
            tags.extend(away_fatigue.get("tags", []))
        if market_data and market_data.get("steam_flag"):
            tags.append("Steam move detected")

        # Recommendation
        if prob_over >= 0.55 and confidence >= 0.5:
            recommendation = "Over"
        elif prob_over <= 0.45 and confidence >= 0.5:
            recommendation = "Under"
        else:
            recommendation = "Pass"

        # Derivatives logic
        derivatives: List[str] = []
        if tempo["tempo_label"] == "high" and avg_variance > 0.4:
            derivatives.append("Full-game total Over or live Over")
        if tempo["tempo_label"] == "low" and avg_variance < 0.35:
            derivatives.append("1P Under, team total Under")
        if home_goalie_reg["goalie_variance"] > 0.5:
            derivatives.append("Home team total Over consideration")
        if away_goalie_reg["goalie_variance"] > 0.5:
            derivatives.append("Away team total Over consideration")

        return {
            "projected_total": float(projected_total),
            "line_total": float(line_total),
            "edge_points": float(edge_points),
            "prob_over": float(prob_over),
            "confidence": float(confidence),
            "tags": tags,
            "recommendation": recommendation,
            "derivatives": derivatives,
            "components": {
                "baseline": float(T0),
                "goalie_delta": float(goalie_delta),
                "tempo_delta": float(tempo_delta),
                "fatigue_delta": float(fatigue_delta),
                "market_delta": float(market_delta),
            },
            "goalie_detail": {
                "home": home_goalie_reg,
                "away": away_goalie_reg,
            },
            "tempo_detail": tempo,
        }

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
# RLM & Public Splits Tracker
# ============================================================

class ReverseLineMovement:
    """
    Track % of bets vs % of money on sides/totals to detect
    reverse line movement and sharp action.

    RLM = line moves AGAINST where the majority of bets are placed,
    indicating sharp money on the other side.
    """

    @staticmethod
    def detect_rlm(
        bet_pct_side_a: float,
        money_pct_side_a: float,
        opening_odds_a: float,
        current_odds_a: float,
        opening_odds_b: float,
        current_odds_b: float,
        total_bets: int = 0,
        side_a_label: str = "Side A",
        side_b_label: str = "Side B",
    ) -> Dict[str, Any]:
        """
        Detect reverse line movement and sharp action signals.

        Args:
            bet_pct_side_a: % of total bets on side A (0-100)
            money_pct_side_a: % of total money on side A (0-100)
            opening_odds_a: Opening American odds for side A
            current_odds_a: Current American odds for side A
            opening_odds_b: Opening American odds for side B
            current_odds_b: Current American odds for side B
            total_bets: Total number of bets (for volume assessment)
            side_a_label: Label for side A
            side_b_label: Label for side B

        Returns:
            Dict with RLM signals, sharp action indicators, and recommendation
        """
        bet_pct_b = 100.0 - bet_pct_side_a
        money_pct_b = 100.0 - money_pct_side_a

        # Bet vs money split
        bet_money_divergence_a = money_pct_side_a - bet_pct_side_a
        bet_money_divergence_b = money_pct_b - bet_pct_b

        # Line movement direction
        # For American odds: line moving from -110 to -130 means side got more expensive (sharp money)
        # Simplify: convert to implied prob to detect movement direction
        opening_implied_a = american_to_implied_prob(opening_odds_a)
        current_implied_a = american_to_implied_prob(current_odds_a)
        opening_implied_b = american_to_implied_prob(opening_odds_b)
        current_implied_b = american_to_implied_prob(current_odds_b)

        line_move_a = current_implied_a - opening_implied_a  # positive = line moved toward A
        line_move_b = current_implied_b - opening_implied_b

        # RLM Detection:
        # Public is on A (bet_pct_a > 55%), but line moves toward B
        rlm_detected = False
        rlm_side = "none"

        if bet_pct_side_a >= 55.0 and line_move_a < -0.005:
            rlm_detected = True
            rlm_side = side_b_label
        elif bet_pct_b >= 55.0 and line_move_b < -0.005:
            rlm_detected = True
            rlm_side = side_a_label

        # Sharp money indicator:
        # Big $ divergence from bet count = sharp bettors on that side
        sharp_side = "none"
        if bet_money_divergence_a >= 10.0:
            sharp_side = side_a_label
        elif bet_money_divergence_b >= 10.0:
            sharp_side = side_b_label

        # Volume assessment
        is_low_volume = total_bets > 0 and total_bets < 5000
        sharp_flag = rlm_detected and is_low_volume

        # Market inefficiency signal
        if sharp_flag:
            signal = "market_inefficiency"
        elif rlm_detected:
            signal = "rlm_detected"
        elif sharp_side != "none":
            signal = "sharp_money"
        else:
            signal = "no_signal"

        # Public side
        public_side = side_a_label if bet_pct_side_a >= 55.0 else side_b_label if bet_pct_b >= 55.0 else "split"

        return {
            "rlm_detected": bool(rlm_detected),
            "rlm_side": rlm_side,
            "sharp_side": sharp_side,
            "public_side": public_side,
            "signal": signal,
            "sharp_low_volume_flag": bool(sharp_flag),
            "bet_pct": {side_a_label: float(bet_pct_side_a), side_b_label: float(bet_pct_b)},
            "money_pct": {side_a_label: float(money_pct_side_a), side_b_label: float(money_pct_b)},
            "bet_money_divergence": {
                side_a_label: float(bet_money_divergence_a),
                side_b_label: float(bet_money_divergence_b),
            },
            "line_movement": {
                side_a_label: float(line_move_a),
                side_b_label: float(line_move_b),
            },
            "odds": {
                side_a_label: {"opening": float(opening_odds_a), "current": float(current_odds_a)},
                side_b_label: {"opening": float(opening_odds_b), "current": float(current_odds_b)},
            },
            "total_bets": int(total_bets),
        }

    @staticmethod
    def detect_sharp_movement(
        line_moves: Optional[List[Dict[str, Any]]] = None,
        is_pinnacle_moved_first: bool = False,
        move_sustained: bool = False,
        low_volume_significant_move: bool = False,
    ) -> Dict[str, Any]:
        """
        RLM & Public Splits 2.0: Sharpness scoring.

        Tracks line movement quality, not just direction.
        Public splits become optional, used only as secondary confirmation.

        Sharpness score (0-3):
          +1 if sharp book (Pinnacle/Circa style) moves first
          +1 if move is sustained (doesn't snap back)
          +1 if move happens on low volume but meaningful cents/half-goal

        Outputs:
          steam_flag: fast multi-book move
          sharp_move_score: 0-3
          rlm_direction: "over" | "under" | "none"
          market_delta: projected total adjustment from market signal
        """
        if line_moves is None:
            line_moves = []

        sharp_move_score = 0
        if is_pinnacle_moved_first:
            sharp_move_score += 1
        if move_sustained:
            sharp_move_score += 1
        if low_volume_significant_move:
            sharp_move_score += 1

        # Steam detection: multiple books moving in same direction rapidly
        steam_flag = False
        if len(line_moves) >= 2:
            directions = [m.get("direction", 0) for m in line_moves]
            nonzero = [d for d in directions if d != 0]
            if len(nonzero) >= 2 and (
                all(d > 0 for d in nonzero) or all(d < 0 for d in nonzero)
            ):
                steam_flag = True

        # Determine RLM direction from moves
        rlm_direction = "none"
        if line_moves:
            avg_direction = sum(m.get("direction", 0) for m in line_moves) / len(line_moves)
            if avg_direction > 0:
                rlm_direction = "over"
            elif avg_direction < 0:
                rlm_direction = "under"

        # Market delta for composite model
        # sharp_move_score of 3 with steam ~ 0.25 goal adjustment
        sign = 1 if rlm_direction == "over" else -1 if rlm_direction == "under" else 0
        market_delta = 0.0
        if steam_flag:
            market_delta += 0.15 * sign
        market_delta += sharp_move_score * 0.05 * sign

        return {
            "steam_flag": bool(steam_flag),
            "sharp_move_score": int(sharp_move_score),
            "rlm_direction": rlm_direction,
            "market_delta": float(market_delta),
            "line_moves_count": len(line_moves),
        }

    @staticmethod
    def detect_totals_rlm(
        bet_pct_over: float,
        money_pct_over: float,
        opening_total: float,
        current_total: float,
        opening_over_odds: float = -110,
        current_over_odds: float = -110,
        opening_under_odds: float = -110,
        current_under_odds: float = -110,
        total_bets: int = 0,
    ) -> Dict[str, Any]:
        """
        Detect RLM specifically for totals (O/U) markets.

        Public hammering Over but line drops = sharp Under money.
        """
        bet_pct_under = 100.0 - bet_pct_over
        money_pct_under = 100.0 - money_pct_over

        line_move = current_total - opening_total  # positive = total went up

        # RLM: public on Over but line drops, or public on Under but line rises
        rlm_detected = False
        rlm_lean = "none"

        if bet_pct_over >= 55.0 and line_move < -0.25:
            rlm_detected = True
            rlm_lean = "under"
        elif bet_pct_under >= 55.0 and line_move > 0.25:
            rlm_detected = True
            rlm_lean = "over"

        # Money divergence
        over_divergence = money_pct_over - bet_pct_over
        under_divergence = money_pct_under - bet_pct_under

        sharp_side = "none"
        if over_divergence >= 10.0:
            sharp_side = "over"
        elif under_divergence >= 10.0:
            sharp_side = "under"

        is_low_volume = total_bets > 0 and total_bets < 5000
        sharp_flag = rlm_detected and is_low_volume

        if sharp_flag:
            signal = "market_inefficiency"
        elif rlm_detected:
            signal = "rlm_detected"
        elif sharp_side != "none":
            signal = "sharp_money"
        else:
            signal = "no_signal"

        return {
            "rlm_detected": bool(rlm_detected),
            "rlm_lean": rlm_lean,
            "sharp_side": sharp_side,
            "signal": signal,
            "sharp_low_volume_flag": bool(sharp_flag),
            "bet_pct": {"over": float(bet_pct_over), "under": float(bet_pct_under)},
            "money_pct": {"over": float(money_pct_over), "under": float(money_pct_under)},
            "line_movement": {
                "opening_total": float(opening_total),
                "current_total": float(current_total),
                "move": float(line_move),
            },
            "total_bets": int(total_bets),
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
