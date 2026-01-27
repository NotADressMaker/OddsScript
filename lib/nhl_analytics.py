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


@dataclass
class GoaltenderStats:
    save_percentage: float = 0.905
    games_started: int = 0
    games_saved_above_expected: float = 0.0  # total GSAx


# ----------------------------
# Odds + EV utilities (American odds)
# ----------------------------

def american_to_implied_prob(odds: float) -> float:
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def prob_to_american(prob: float) -> int:
    prob = float(prob)
    if prob <= 0.0 or prob >= 1.0:
        raise ValueError("Probability must be between 0 and 1 (exclusive).")
    if prob > 0.5:
        return int(-round((prob / (1 - prob)) * 100))
    return int(round(((1 - prob) / prob) * 100))


def payout_per_1_risk(odds: float) -> float:
    # profit for risking $1
    if odds > 0:
        return odds / 100.0
    return 100.0 / (-odds)


def expected_value_per_1_risk(prob_win: float, odds: float) -> float:
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
    def adjust_for_goalies(
        home_xg: float,
        away_xg: float,
        home_gsax: float = 0.0,
        away_gsax: float = 0.0,
        league_gsax_avg: float = NHLConstants.LEAGUE_GSAX_AVG,
        impact_per_gsax: float = 0.12,
    ) -> Tuple[float, float]:
        # better goalie lowers opponent xG
        home_adj = 1.0 - (home_gsax - league_gsax_avg) * impact_per_gsax
        away_adj = 1.0 - (away_gsax - league_gsax_avg) * impact_per_gsax

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
            }

        # fallback: crude normal approximation on Skellam-ish behavior (kept simple)
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
        }


# ============================================================
# 2) NHLAnalytics (LEGACY, backward compatible)
# ============================================================

class NHLAnalytics:
    """
    Backward compatible helper surface.

    IMPORTANT:
    - Keep these signatures stable if other scripts call them.
    - They return dicts with simple keys like 'win_probability', etc.
    """
    AVG_HOME_ADVANTAGE = NHLConstants.AVG_HOME_ADVANTAGE

    @staticmethod
    def calculate_moneyline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        is_home: bool = True,
        include_overtime: bool = True,
    ) -> Dict[str, float]:
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0.0
        team_lambda = float(team_goals_avg) + float(home_adj)
        opp_lambda = float(opponent_goals_avg)

        out = NHLAdvancedAnalytics.predict_game_from_xg(team_lambda, opp_lambda, include_overtime=include_overtime)
        # map to legacy key names
        win_prob = out["home_win_probability"] if is_home else out["away_win_probability"]
        loss_prob = out["away_win_probability"] if is_home else out["home_win_probability"]

        return {
            "win_probability": float(win_prob),
            "loss_probability": float(loss_prob),
            "overtime_probability": float(out.get("overtime_probability", 0.0)),
            "expected_total": float(out["expected_total"]),
        }

    @staticmethod
    def calculate_puckline_probability(
        team_goals_avg: float,
        opponent_goals_avg: float,
        puckline: float = -1.5,
        is_home: bool = True,
        max_goals: int = 10,
    ) -> Dict[str, float]:
        home_adj = NHLAnalytics.AVG_HOME_ADVANTAGE if is_home else 0.0
        team_lambda = float(team_goals_avg) + float(home_adj)
        opp_lambda = float(opponent_goals_avg)

        # best if PoissonCalculator exists (needs prob_matrix)
        if PoissonCalculator is not None:
            res = PoissonCalculator.calculate_match_probabilities(team_lambda, opp_lambda, max_goals=max_goals)
            matrix = res.get("prob_matrix")
            cover_prob = 0.0
            if matrix is not None:
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
        return {"cover_probability": float(p), "puckline": float(puckline), "expected_margin": float(margin)}

    @staticmethod
    def calculate_total_probability(
        team1_goals_avg: float,
        team2_goals_avg: float,
        total_line: float,
        goalie_adjustment: float = 1.0,
    ) -> Dict[str, float]:
        total_lambda = (float(team1_goals_avg) + float(team2_goals_avg)) * float(goalie_adjustment)

        if PoissonCalculator is not None and hasattr(PoissonCalculator, "calculate_total_probabilities"):
            res = PoissonCalculator.calculate_total_probabilities(total_lambda / 2.0, total_lambda / 2.0, total_line, max_goals=12)
            return {
                "over_probability": float(res["over_probability"]),
                "under_probability": float(res["under_probability"]),
                "expected_total": float(total_lambda),
                "line": float(total_line),
                "goalie_adjustment": float(goalie_adjustment),
            }

        p_over = _poisson_prob_over_line(total_lambda, total_line, max_k=25)
        p_under = _poisson_prob_under_line(total_lambda, total_line, max_k=25)
        return {
            "over_probability": float(p_over),
            "under_probability": float(p_under),
            "expected_total": float(total_lambda),
            "line": float(total_line),
            "goalie_adjustment": float(goalie_adjustment),
        }

    @staticmethod
    def simulate_game(home_goals_avg: float, away_goals_avg: float, seed: Optional[int] = None) -> Dict[str, Any]:
        if seed is not None:
            random.seed(seed)

        home_lambda = float(home_goals_avg) + NHLAnalytics.AVG_HOME_ADVANTAGE
        away_lambda = float(away_goals_avg)

        # If PoissonCalculator exists, use it
        if PoissonCalculator is not None and hasattr(PoissonCalculator, "simulate_match"):
            sim = PoissonCalculator.simulate_match(home_lambda, away_lambda, seed)
            # normalize output
            home_score = int(sim.get("home_score", 0))
            away_score = int(sim.get("away_score", 0))
            return {
                "home_score": home_score,
                "away_score": away_score,
                "total_goals": home_score + away_score,
                "margin": home_score - away_score,
                "regulation_result": sim.get("result"),
            }

        # fallback sampling
        def sample_poisson(lam: float) -> int:
            # Knuth
            L = math.exp(-lam)
            k = 0
            p = 1.0
            while p > L:
                k += 1
                p *= random.random()
            return k - 1

        home_score = sample_poisson(home_lambda)
        away_score = sample_poisson(away_lambda)
        return {
            "home_score": int(home_score),
            "away_score": int(away_score),
            "total_goals": int(home_score + away_score),
            "margin": int(home_score - away_score),
            "regulation_result": "home_win" if home_score > away_score else "away_win" if away_score > home_score else "draw",
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

        # Poisson total
        if PoissonCalculator is not None and hasattr(PoissonCalculator, "calculate_total_probabilities"):
            # some implementations want team lambdas; ours uses a direct total approximation anyway
            p_over = _poisson_prob_over_line(lam_total, total_line, max_k=max_goals_sum)
            p_under = _poisson_prob_under_line(lam_total, total_line, max_k=max_goals_sum)
        else:
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

    def _collect_moneyline(self, home: str, away: str, features: Dict[str, float]) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
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

    def _collect_spread(self, home: str, away: str, features: Dict[str, float], line_home: float, line_away: float) -> Tuple[Dict[str, str], Dict[str, float], Dict[str, Any]]:
        votes: Dict[str, str] = {}
        probs: Dict[str, float] = {}
        raw: Dict[str, Any] = {}

        for name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(model, ["predict_spread", "predict_puckline", "predict_game", "predict"], home, away, features, line_home, line_away)
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

        # split via xgf_diff if present (else xg_diff)
        if "xgf_diff" in features:
            strength = float(features.get("xgf_diff", 0.0))
        else:
            strength = float(features.get("xg_diff", 0.0))

        share = 0.5 + 0.06 * strength + 0.05 * home_adv + 0.02 * gsax_diff
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
