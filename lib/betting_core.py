#!/usr/bin/env python3
"""
lib/betting_core.py

Sport-agnostic betting utilities for SportsBetLang.

Purpose:
- Standardize result containers (BetResult) across all sports/markets
- Centralize odds conversions + EV math
- Provide convergence + ranking helpers (2-model / 3-model agreement)

This avoids duplicating the same logic inside NHL/NBA/etc files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ============================================================
# Odds / EV utilities (American odds)
# ============================================================

def american_to_implied_prob(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds == 0:
        raise ValueError("American odds cannot be 0")
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return (-odds) / ((-odds) + 100.0)


def prob_to_american(prob: float) -> int:
    """Convert probability to fair American odds (rounded)."""
    p = float(prob)
    if p <= 0.0 or p >= 1.0:
        raise ValueError("Probability must be between 0 and 1 (exclusive).")
    if p > 0.5:
        return int(-round((p / (1.0 - p)) * 100))
    return int(round(((1.0 - p) / p) * 100))


def payout_per_1_risk(odds: float) -> float:
    """
    Profit (not return) for risking $1 at American odds.
      -120 -> profit = 100/120 = 0.8333
      +150 -> profit = 150/100 = 1.5
    """
    o = float(odds)
    if o > 0:
        return o / 100.0
    return 100.0 / (-o)


def expected_value_per_1_risk(prob_win: float, odds: float) -> float:
    """
    EV for risking $1:
      EV = p(win)*profit - p(lose)*1
    """
    p = float(prob_win)
    profit = payout_per_1_risk(float(odds))
    return p * profit - (1.0 - p)


# ============================================================
# Standard outputs
# ============================================================

@dataclass
class BetResult:
    """Universal result object that every sport module should return."""

    sport: str                    # "NHL", "NBA", ...
    bet_type: str                 # "MONEY" | "SPREAD" | "TOTAL" | "PROP" ...
    pick: str                     # e.g., "HOME", "AWAY", "UNDER 6.5", "TEAM +1.5"
    prob: float                   # model probability for THIS pick winning
    fair_odds: int                # fair American odds derived from prob
    market_odds: Optional[float]  # market American odds, if supplied
    implied_prob: Optional[float] # implied probability from market_odds
    edge: Optional[float]         # prob - implied_prob
    ev_per_1: Optional[float]     # expected value per $1 risked
    model_votes: Dict[str, str]   # {"power":"UNDER 6.5", "tree":"UNDER 6.5"...}
    model_probs: Dict[str, float] # {"power":0.56, "tree":0.58...} (prob for the pick)
    details: Dict[str, Any]       # free-form, sport-specific info


@dataclass
class BetRecommendation:
    """A ranked recommendation record (useful for "top N plays")."""

    bet: BetResult
    score: float                  # composite ranking score
    reasons: List[str]            # short bullet reasons


# ============================================================
# Convergence helpers
# ============================================================

def convergence_summary(votes: Dict[str, str]) -> Dict[str, Any]:
    """Count votes from multiple models and report best pick and max agreement."""
    counts: Dict[str, int] = {}
    for v in votes.values():
        counts[v] = counts.get(v, 0) + 1
    best = max(counts.items(), key=lambda kv: kv[1])[0] if counts else None
    return {
        "counts": counts,
        "best_pick": best,
        "max_count": counts.get(best, 0) if best else 0,
        "n_models": len(votes),
    }


def is_converged(votes: Dict[str, str], required: int) -> bool:
    """True if at least `required` models agree on the same exact pick string."""
    s = convergence_summary(votes)
    return bool(s["best_pick"]) and int(s["max_count"]) >= int(required)


# ============================================================
# Ranking + filtering
# ============================================================

def make_bet_result(
    *,
    sport: str,
    bet_type: str,
    pick: str,
    prob: float,
    market_odds: Optional[float],
    model_votes: Optional[Dict[str, str]] = None,
    model_probs: Optional[Dict[str, float]] = None,
    details: Optional[Dict[str, Any]] = None,
) -> BetResult:
    """Convenience constructor that fills fair odds, edge, EV."""
    p = float(prob)
    fair = prob_to_american(p)

    implied = edge = ev = None
    if market_odds is not None:
        implied = american_to_implied_prob(float(market_odds))
        edge = p - implied
        ev = expected_value_per_1_risk(p, float(market_odds))

    return BetResult(
        sport=str(sport),
        bet_type=str(bet_type),
        pick=str(pick),
        prob=p,
        fair_odds=int(fair),
        market_odds=float(market_odds) if market_odds is not None else None,
        implied_prob=float(implied) if implied is not None else None,
        edge=float(edge) if edge is not None else None,
        ev_per_1=float(ev) if ev is not None else None,
        model_votes=model_votes or {},
        model_probs=model_probs or {},
        details=details or {},
    )


def rank_bets(
    bets: List[BetResult],
    *,
    min_models: int = 0,
    min_convergence: int = 0,
    min_ev: Optional[float] = None,
    min_edge: Optional[float] = None,
) -> List[BetRecommendation]:
    """
    Filter + rank bets by a simple scoring function.

    Scoring philosophy (simple, interpretable):
    - EV matters most (if present)
    - Edge helps (if present)
    - Convergence acts as a multiplier
    """
    recs: List[BetRecommendation] = []

    for b in bets:
        # Model count / convergence filters
        if min_models and len(b.model_votes) < min_models:
            continue
        if min_convergence and not is_converged(b.model_votes, min_convergence):
            continue

        # EV / edge filters (if present)
        if min_ev is not None:
            if b.ev_per_1 is None or b.ev_per_1 < float(min_ev):
                continue
        if min_edge is not None:
            if b.edge is None or b.edge < float(min_edge):
                continue

        # Score
        ev = b.ev_per_1 if b.ev_per_1 is not None else 0.0
        edge = b.edge if b.edge is not None else 0.0
        conv = convergence_summary(b.model_votes)
        agree = int(conv["max_count"])
        nmods = max(1, int(conv["n_models"]))
        conv_factor = 1.0 + 0.25 * (agree / nmods)  # 1.0 -> 1.25 boost

        score = (2.0 * ev + 1.0 * edge) * conv_factor

        reasons: List[str] = []
        if b.ev_per_1 is not None:
            reasons.append(f"EV per $1: {b.ev_per_1:+.3f}")
        if b.edge is not None:
            reasons.append(f"Edge: {b.edge:+.3f}")
        if conv["best_pick"]:
            reasons.append(f"Convergence: {agree}/{nmods} on {conv['best_pick']}")
        else:
            reasons.append("Convergence: n/a")

        recs.append(BetRecommendation(bet=b, score=float(score), reasons=reasons))

    recs.sort(key=lambda r: r.score, reverse=True)
    return recs


# ============================================================
# Tiny smoke test
# ============================================================

if __name__ == "__main__":
    demo = make_bet_result(
        sport="DEMO",
        bet_type="TOTAL",
        pick="UNDER 6.5",
        prob=0.56,
        market_odds=-110,
        model_votes={"power": "UNDER 6.5", "tree": "UNDER 6.5", "similar": "OVER 6.5"},
        model_probs={"power": 0.56, "tree": 0.58, "similar": 0.49},
        details={"note": "example"},
    )
    ranked = rank_bets([demo], min_convergence=2, min_ev=0.0)
    print("Ranked:", ranked[0].bet.pick, "score=", ranked[0].score, "reasons=", ranked[0].reasons)
