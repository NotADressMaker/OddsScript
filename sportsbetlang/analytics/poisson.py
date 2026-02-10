"""
SportsBetLang Analytics - Poisson Models

Provides Poisson-based scoring models for low-scoring sports (soccer, hockey).
Includes probability helpers with tail-aware truncation to avoid undercounting
when using finite score grids.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

_RNG = random.Random()


def set_seed(seed: int) -> None:
    """Set deterministic seed for Poisson simulation helpers."""

    _RNG.seed(seed)


def poisson_probability(k: int, lambda_param: float) -> float:
    """Calculate Poisson probability P(X = k)."""
    if k < 0:
        raise ValueError("k must be non-negative")
    if lambda_param < 0:
        raise ValueError("lambda_param must be non-negative")
    return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)


def poisson_cumulative(k: int, lambda_param: float) -> float:
    """Calculate Poisson cumulative probability P(X <= k)."""
    if k < 0:
        return 0.0
    return sum(poisson_probability(i, lambda_param) for i in range(k + 1))


def _bounded_poisson_probs(lambda_param: float, max_goals: int) -> List[float]:
    """Return Poisson probabilities for 0..max_goals with tail mass folded into max_goals."""
    if max_goals < 0:
        raise ValueError("max_goals must be non-negative")
    if lambda_param < 0:
        raise ValueError("lambda_param must be non-negative")

    probs = [poisson_probability(k, lambda_param) for k in range(max_goals)]
    tail = 1.0 - sum(probs)
    tail = max(tail, 0.0)
    probs.append(tail)
    return probs


def calculate_match_probabilities(
    home_lambda: float,
    away_lambda: float,
    max_goals: int = 10,
    include_tail: bool = True,
) -> Dict[str, object]:
    """
    Calculate match outcome probabilities.

    When include_tail is True, the last score bucket represents "max_goals or more"
    to preserve total probability mass.
    """
    if include_tail:
        home_probs = _bounded_poisson_probs(home_lambda, max_goals)
        away_probs = _bounded_poisson_probs(away_lambda, max_goals)
    else:
        home_probs = [poisson_probability(k, home_lambda) for k in range(max_goals + 1)]
        away_probs = [poisson_probability(k, away_lambda) for k in range(max_goals + 1)]

    prob_matrix: List[List[float]] = []
    for home_index, prob_home in enumerate(home_probs):
        row = []
        for prob_away in away_probs:
            row.append(prob_home * prob_away)
        prob_matrix.append(row)

    home_win = sum(
        prob_matrix[h][a]
        for h in range(len(home_probs))
        for a in range(h)
    )
    away_win = sum(
        prob_matrix[h][a]
        for h in range(len(home_probs))
        for a in range(h + 1, len(away_probs))
    )
    draw = sum(prob_matrix[i][i] for i in range(min(len(home_probs), len(away_probs))))

    return {
        "home_win": home_win,
        "away_win": away_win,
        "draw": draw,
        "prob_matrix": prob_matrix,
        "max_goals": max_goals,
        "include_tail": include_tail,
    }


def calculate_total_probabilities(
    home_lambda: float,
    away_lambda: float,
    total_line: float,
    max_goals: int = 15,
    include_tail: bool = True,
) -> Dict[str, float]:
    """
    Calculate over/under probabilities for a total line.

    When include_tail is True, the final bucket represents "max_goals or more" and
    counts toward the over side for non-integer lines.
    """
    total_lambda = home_lambda + away_lambda

    if include_tail:
        probs = _bounded_poisson_probs(total_lambda, max_goals)
        goal_range = range(len(probs))
    else:
        probs = [poisson_probability(k, total_lambda) for k in range(max_goals + 1)]
        goal_range = range(max_goals + 1)

    over_prob = 0.0
    under_prob = 0.0

    for total_goals, prob in zip(goal_range, probs):
        if total_goals > total_line:
            over_prob += prob
        elif total_goals < total_line:
            under_prob += prob

    return {
        "over_probability": over_prob,
        "under_probability": under_prob,
        "expected_total": total_lambda,
        "line": total_line,
        "max_goals": max_goals,
        "include_tail": include_tail,
    }


def calculate_correct_score_probabilities(
    home_lambda: float,
    away_lambda: float,
    max_score: int = 5
) -> List[Tuple[int, int, float]]:
    """Calculate probabilities for each correct score."""
    scores: List[Tuple[int, int, float]] = []
    for home_score in range(max_score + 1):
        for away_score in range(max_score + 1):
            prob_home = poisson_probability(home_score, home_lambda)
            prob_away = poisson_probability(away_score, away_lambda)
            scores.append((home_score, away_score, prob_home * prob_away))
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores


def calculate_btts_probability(home_lambda: float, away_lambda: float) -> Dict[str, float]:
    """Calculate both teams to score probability."""
    home_scores = 1 - poisson_probability(0, home_lambda)
    away_scores = 1 - poisson_probability(0, away_lambda)
    btts_yes = home_scores * away_scores
    return {
        "btts_yes": btts_yes,
        "btts_no": 1 - btts_yes,
        "home_scores_prob": home_scores,
        "away_scores_prob": away_scores,
    }


def simulate_poisson_event(lambda_param: float, seed: Optional[int] = None) -> int:
    """Simulate a single Poisson-distributed random variable."""
    if lambda_param < 0:
        raise ValueError("lambda_param must be non-negative")
    if seed is not None:
        _RNG.seed(seed)

    if lambda_param < 30:
        threshold = math.exp(-lambda_param)
        k = 0
        p = 1.0
        while p > threshold:
            k += 1
            p *= _RNG.random()
        return k - 1
    return max(0, int(_RNG.gauss(lambda_param, math.sqrt(lambda_param)) + 0.5))


def simulate_match(
    home_lambda: float,
    away_lambda: float,
    seed: Optional[int] = None
) -> Dict[str, object]:
    """Simulate a single match outcome using Poisson distribution."""
    if seed is not None:
        _RNG.seed(seed)

    home_score = simulate_poisson_event(home_lambda)
    away_score = simulate_poisson_event(away_lambda)

    if home_score > away_score:
        result = "home_win"
    elif away_score > home_score:
        result = "away_win"
    else:
        result = "draw"

    return {
        "home_score": home_score,
        "away_score": away_score,
        "total_score": home_score + away_score,
        "result": result,
    }


@dataclass
class PoissonModel:
    """Convenience wrapper for Poisson scoring models."""

    max_goals: int = 10
    include_tail: bool = True

    def match_probabilities(self, home_lambda: float, away_lambda: float) -> Dict[str, object]:
        return calculate_match_probabilities(
            home_lambda,
            away_lambda,
            max_goals=self.max_goals,
            include_tail=self.include_tail,
        )

    def total_probabilities(self, home_lambda: float, away_lambda: float, total_line: float) -> Dict[str, float]:
        return calculate_total_probabilities(
            home_lambda,
            away_lambda,
            total_line,
            max_goals=max(self.max_goals, int(total_line) + 2),
            include_tail=self.include_tail,
        )

    def simulate(self, home_lambda: float, away_lambda: float, seed: Optional[int] = None) -> Dict[str, object]:
        return simulate_match(home_lambda, away_lambda, seed)
