# lib/nhl_analytics.py
"""
NHL Analytics + Betting Interface
- Standardizes outputs for MONEYLINE / SPREAD (puckline) / TOTAL (O/U)
- Designed to plug cleanly into SportsBetLang "MONEY / SPREAD / TOTAL" language

Key idea: return consistent dict outputs that include:
  - pick (e.g., "OVER", "UNDER", "HOME", "AWAY", "HOME +1.5")
  - probability (model win prob of the pick)
  - fair odds (American) from probability
  - edge (prob - implied_prob_from_market)
  - ev (expected value per $1 risked)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any

from .nhl_feature_engineering import NHLFeatureEngineering
from .nhl_ensemble import NHLEnsemble


# ----------------------------
# Odds + EV utilities
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
    # If p > 0.5 -> negative odds, else positive
    if prob > 0.5:
        odds = -round((prob / (1 - prob)) * 100)
    else:
        odds = round(((1 - prob) / prob) * 100)
    return int(odds)


def payout_per_1_risk(odds: float) -> float:
    """
    Profit (not return) for risking $1 at given American odds.
    Example: -120 -> profit = 1/1.2 = 0.8333
             +150 -> profit = 1.5
    """
    if odds > 0:
        return odds / 100.0
    return 100.0 / (-odds)


def expected_value_per_1_risk(prob_win: float, odds: float) -> float:
    """
    EV for risking $1:
      EV = p * profit - (1-p) * 1
    """
    profit = payout_per_1_risk(odds)
    return prob_win * profit - (1.0 - prob_win)


# ----------------------------
# Simple Poisson helpers (for totals)
# ----------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """P(X=k) for Poisson(lam)."""
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_cdf(k: int, lam: float, max_k: int = 25) -> float:
    """P(X<=k) approx by summing pmf."""
    k = int(k)
    total = 0.0
    for i in range(0, min(k, max_k) + 1):
        total += poisson_pmf(i, lam)
    return total


def poisson_prob_over_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    """
    P(Total > line) assuming integer goals.
    If line is 6.5, "over" means >= 7.
    If line is 6.0, books often grade pushes at 6; treat separately in caller.
    """
    if line % 1 == 0.5:
        threshold = int(math.floor(line) + 1)  # 6.5 -> 7
        p_le = poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
        return max(0.0, 1.0 - p_le)
    # If integer line, "over" means >= line+1
    threshold = int(line) + 1
    p_le = poisson_cdf(threshold - 1, total_lambda, max_k=max_k)
    return max(0.0, 1.0 - p_le)


def poisson_prob_under_line(total_lambda: float, line: float, max_k: int = 25) -> float:
    """
    P(Total < line). For 6.5, "under" means <= 6.
    For integer line, caller should handle push separately.
    """
    if line % 1 == 0.5:
        threshold = int(math.floor(line))  # 6.5 -> 6
        return poisson_cdf(threshold, total_lambda, max_k=max_k)
    # integer line: under means <= line-1 (push at line)
    threshold = int(line) - 1
    return poisson_cdf(threshold, total_lambda, max_k=max_k)


def poisson_prob_push(total_lambda: float, line: float) -> float:
    """If line is integer, push probability is P(Total == line). Otherwise 0."""
    if line % 1 != 0:
        return 0.0
    k = int(line)
    return poisson_pmf(k, total_lambda)


# ----------------------------
# Standard return container
# ----------------------------

@dataclass
class BetResult:
    bet_type: str                 # "MONEY" | "SPREAD" | "TOTAL"
    pick: str                     # ex: "HOME", "AWAY", "HOME +1.5", "UNDER 6.5"
    prob: float                   # model probability of winning the pick
    fair_odds: int                # fair American odds from prob
    market_odds: Optional[float]  # odds user/book offers
    implied_prob: Optional[float] # implied probability from market_odds
    edge: Optional[float]         # prob - implied_prob
    ev_per_1: Optional[float]     # EV per $1 risked (None if market_odds not provided)
    details: Dict[str, Any]       # extra model context


# ----------------------------
# Main API class used by DSL
# ----------------------------

class NHLAnalytics:
    """
    Primary interface that SportsBetLang can call.
    It exposes:
      - predict_moneyline(...)
      - predict_spread(...)
      - predict_total(...)
    """

    def __init__(self, ensemble: NHLEnsemble):
        self.ensemble = ensemble

    # ---- MONEYLINE ----

    def predict_moneyline(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, BetResult]:
        """
        Returns both sides so caller can choose. Ensemble should provide home win prob.
        Expected ensemble API:
          - ensemble.predict_moneyline(home_team, away_team, features) -> dict with 'home_win_prob'
        """
        pred = self.ensemble.predict_moneyline(home_team, away_team, features)
        p_home = float(pred.get("home_win_prob", 0.5))
        p_away = 1.0 - p_home

        return {
            "HOME": self._make_bet_result(
                bet_type="MONEY",
                pick="HOME",
                prob=p_home,
                market_odds=market_home_odds,
                details={"home_team": home_team, "away_team": away_team, "raw": pred},
            ),
            "AWAY": self._make_bet_result(
                bet_type="MONEY",
                pick="AWAY",
                prob=p_away,
                market_odds=market_away_odds,
                details={"home_team": home_team, "away_team": away_team, "raw": pred},
            ),
        }

    # ---- SPREAD / PUCKLINE ----

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
        """
        Puckline: typically +/-1.5
        Expected ensemble API:
          - ensemble.predict_spread(home_team, away_team, features, line_home, line_away)
            -> dict with 'home_cover_prob' (prob home covers its line)
        """
        pred = self.ensemble.predict_spread(home_team, away_team, features, line_home, line_away)
        p_home_cover = float(pred.get("home_cover_prob", 0.5))
        p_away_cover = 1.0 - p_home_cover

        return {
            "HOME": self._make_bet_result(
                bet_type="SPREAD",
                pick=f"HOME {line_home:+.1f}",
                prob=p_home_cover,
                market_odds=market_home_odds,
                details={"home_team": home_team, "away_team": away_team, "raw": pred, "line_home": line_home},
            ),
            "AWAY": self._make_bet_result(
                bet_type="SPREAD",
                pick=f"AWAY {line_away:+.1f}",
                prob=p_away_cover,
                market_odds=market_away_odds,
                details={"home_team": home_team, "away_team": away_team, "raw": pred, "line_away": line_away},
            ),
        }

    # ---- TOTAL ----

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
        """
        Computes Over/Under probabilities using a Poisson total approximation.

        Expected ensemble API:
          - ensemble.predict_expected_goals(home_team, away_team, features)
            -> dict with 'home_xg' and 'away_xg'
        If your ensemble doesn't have this yet, add it (recommended), or
        replace with your own expected goals model.

        Push handling:
          - If total_line is integer (e.g., 6.0), we compute push probability.
            BetResult.prob is "win probability" (excluding pushes) by default,
            and details include push probability.
        """
        eg = self.ensemble.predict_expected_goals(home_team, away_team, features)
        home_xg = float(eg.get("home_xg", 3.0))
        away_xg = float(eg.get("away_xg", 3.0))
        lam_total = home_xg + away_xg

        p_over = poisson_prob_over_line(lam_total, total_line, max_k=max_goals_sum)
        p_under = poisson_prob_under_line(lam_total, total_line, max_k=max_goals_sum)
        p_push = poisson_prob_push(lam_total, total_line)

        # For integer totals, the "win prob" is conditional on not pushing, if desired.
        # Many bettors still prefer raw P(win) ignoring push; here we store both.
        details_common = {
            "home_team": home_team,
            "away_team": away_team,
            "home_xg": home_xg,
            "away_xg": away_xg,
            "expected_total": lam_total,
            "p_push": p_push,
            "raw_expected_goals": eg,
        }

        return {
            "OVER": self._make_bet_result(
                bet_type="TOTAL",
                pick=f"OVER {total_line:.1f}",
                prob=p_over,
                market_odds=market_over_odds,
                details={**details_common, "side": "OVER", "p_over": p_over, "p_under": p_under},
            ),
            "UNDER": self._make_bet_result(
                bet_type="TOTAL",
                pick=f"UNDER {total_line:.1f}",
                prob=p_under,
                market_odds=market_under_odds,
                details={**details_common, "side": "UNDER", "p_over": p_over, "p_under": p_under},
            ),
        }

    # ---- Helpers ----

    def _make_bet_result(
        self,
        bet_type: str,
        pick: str,
        prob: float,
        market_odds: Optional[float],
        details: Optional[Dict[str, Any]] = None,
    ) -> BetResult:
        prob = float(prob)
        fair = prob_to_american(prob)
        implied = None
        edge = None
        ev = None

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
            details=details or {},
        )


# Backward compatibility alias if other modules import NHLAdvancedAnalytics
NHLAdvancedAnalytics = NHLAnalytics


# ----------------------------
# Example usage (for testing or REPL)
# ----------------------------

if __name__ == "__main__":
    # NOTE: These classes must exist in your project.
    # If they live elsewhere, import them appropriately.
    from .nhl_power_rankings import NHLPowerRankings
    from .nhl_decision_tree import NHLDecisionTree
    from .nhl_similar_game_model import NHLSimilarGameModel

    power = NHLPowerRankings()
    tree = NHLDecisionTree()
    similar = NHLSimilarGameModel()  # requires historical data

    ensemble = NHLEnsemble(power, tree, similar)
    analytics = NHLAnalytics(ensemble)

    features = NHLFeatureEngineering.create_game_features(
        home_data={"xgf": 3.2, "xga": 2.8, "corsi_pct": 54.5, "is_home": True},
        away_data={"xgf": 2.9, "xga": 3.0, "corsi_pct": 48.2},
        home_rest_days=2,
        away_rest_days=1,
    )

    # Moneyline
    ml = analytics.predict_moneyline(
        home_team="Boston Bruins",
        away_team="Nashville Predators",
        features=features,
        market_home_odds=-113,
        market_away_odds=+105,
    )
    print("MONEY:", ml["HOME"])

    # Total
    tot = analytics.predict_total(
        home_team="Boston Bruins",
        away_team="Nashville Predators",
        features=features,
        total_line=6.5,
        market_over_odds=+100,
        market_under_odds=-122,
    )
    print("TOTAL:", tot["UNDER"])
