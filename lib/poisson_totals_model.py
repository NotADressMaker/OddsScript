#!/usr/bin/env python3
"""
Poisson totals models for over/under (O/U) betting.

Provides standard Poisson totals as well as common "friends":
- Bivariate Poisson (shared scoring component)
- Zero-inflated Poisson (extra mass at scoreless outcomes)
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


def _poisson_pmf(k: int, lambda_param: float) -> float:
    if k < 0:
        return 0.0
    if lambda_param < 0:
        raise ValueError("lambda_param must be non-negative")
    return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)


def _poisson_probs(lambda_param: float, max_goals: int) -> List[float]:
    return [_poisson_pmf(k, lambda_param) for k in range(max_goals + 1)]


def _safe_sum(values: List[float]) -> float:
    return max(0.0, min(1.0, sum(values)))


class PoissonTotalsModel:
    """Poisson-style totals models for O/U lines."""

    def __init__(self, max_goals: int = 15) -> None:
        if max_goals < 0:
            raise ValueError("max_goals must be non-negative")
        self.max_goals = max_goals

    def total_probabilities(
        self,
        home_lambda: float,
        away_lambda: float,
        total_line: float,
    ) -> Dict[str, float]:
        """Standard Poisson totals: Total ~ Poisson(home_lambda + away_lambda)."""
        total_lambda = home_lambda + away_lambda
        totals = _poisson_probs(total_lambda, self.max_goals)
        return self._over_under_from_totals(totals, total_line, total_lambda)

    def total_probabilities_bivariate(
        self,
        home_lambda: float,
        away_lambda: float,
        shared_lambda: float,
        total_line: float,
    ) -> Dict[str, float]:
        """
        Bivariate Poisson totals with shared scoring component.

        X = A + C, Y = B + C where A,B,C are independent Poisson.
        shared_lambda controls correlation (larger => higher covariance).
        """
        if shared_lambda < 0:
            raise ValueError("shared_lambda must be non-negative")

        totals = [0.0 for _ in range(self.max_goals + 1)]
        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                joint = self._bivariate_joint_probability(
                    home_goals,
                    away_goals,
                    home_lambda,
                    away_lambda,
                    shared_lambda,
                )
                total = home_goals + away_goals
                if total <= self.max_goals:
                    totals[total] += joint

        expected_total = home_lambda + away_lambda + 2 * shared_lambda
        return self._over_under_from_totals(totals, total_line, expected_total)

    def total_probabilities_zero_inflated(
        self,
        home_lambda: float,
        away_lambda: float,
        zero_prob_home: float,
        zero_prob_away: float,
        total_line: float,
    ) -> Dict[str, float]:
        """
        Zero-inflated Poisson totals with extra mass at zero scoring.

        zero_prob_home/away represent the additional probability of a zero score.
        """
        if not 0.0 <= zero_prob_home <= 1.0:
            raise ValueError("zero_prob_home must be between 0 and 1")
        if not 0.0 <= zero_prob_away <= 1.0:
            raise ValueError("zero_prob_away must be between 0 and 1")

        home_probs = _poisson_probs(home_lambda, self.max_goals)
        away_probs = _poisson_probs(away_lambda, self.max_goals)

        home_probs[0] = (1 - zero_prob_home) * home_probs[0] + zero_prob_home
        away_probs[0] = (1 - zero_prob_away) * away_probs[0] + zero_prob_away

        for k in range(1, self.max_goals + 1):
            home_probs[k] *= (1 - zero_prob_home)
            away_probs[k] *= (1 - zero_prob_away)

        totals = [0.0 for _ in range(self.max_goals + 1)]
        for home_goals, home_prob in enumerate(home_probs):
            for away_goals, away_prob in enumerate(away_probs):
                total = home_goals + away_goals
                if total <= self.max_goals:
                    totals[total] += home_prob * away_prob

        expected_total = (
            (1 - zero_prob_home) * home_lambda
            + (1 - zero_prob_away) * away_lambda
        )
        return self._over_under_from_totals(totals, total_line, expected_total)

    @staticmethod
    def _bivariate_joint_probability(
        home_goals: int,
        away_goals: int,
        home_lambda: float,
        away_lambda: float,
        shared_lambda: float,
    ) -> float:
        max_shared = min(home_goals, away_goals)
        prob = 0.0
        for shared_goals in range(max_shared + 1):
            prob += (
                _poisson_pmf(home_goals - shared_goals, home_lambda)
                * _poisson_pmf(away_goals - shared_goals, away_lambda)
                * _poisson_pmf(shared_goals, shared_lambda)
            )
        return prob

    @staticmethod
    def _over_under_from_totals(
        totals: List[float],
        total_line: float,
        expected_total: float,
    ) -> Dict[str, float]:
        over_prob = 0.0
        under_prob = 0.0
        for total_goals, prob in enumerate(totals):
            if total_goals > total_line:
                over_prob += prob
            elif total_goals < total_line:
                under_prob += prob

        return {
            "over_probability": _safe_sum([over_prob]),
            "under_probability": _safe_sum([under_prob]),
            "expected_total": expected_total,
            "line": total_line,
        }
