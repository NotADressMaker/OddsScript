#!/usr/bin/env python3
"""
Over/Under Trend Model

Provides a sport-agnostic approach for estimating totals by comparing
recent 5-game trends against season averages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


def _safe_mean(values: Iterable[float]) -> float:
    values_list = list(values)
    if not values_list:
        raise ValueError("Expected at least one value to calculate mean")
    return sum(values_list) / len(values_list)


def _ratio(numerator: float, denominator: float, fallback: float = 1.0) -> float:
    if denominator == 0:
        return fallback
    return numerator / denominator


@dataclass(frozen=True)
class TeamTrendStats:
    """Container for team scoring/allowing averages and recent results."""

    season_avg_for: float
    season_avg_against: float
    recent_games_for: List[float]
    recent_games_against: List[float]

    def recent_avg_for(self) -> float:
        return _safe_mean(self.recent_games_for)

    def recent_avg_against(self) -> float:
        return _safe_mean(self.recent_games_against)

    def recent_trend_factors(self) -> Tuple[float, float]:
        """
        Return offensive/defensive trend multipliers based on last 5 games.

        Offensive trend = recent scoring vs season average scoring.
        Defensive trend = recent allowed vs season average allowed.
        """

        offense_trend = _ratio(self.recent_avg_for(), self.season_avg_for)
        defense_trend = _ratio(self.recent_avg_against(), self.season_avg_against)
        return offense_trend, defense_trend


class OverUnderTrendModel:
    """
    Sport-agnostic totals model using recent 5-game trends vs season averages.

    Inputs are per-team scoring/allowing averages for the season and the most
    recent five games. The model blends season baselines with trend multipliers
    to estimate the expected total and pick an over/under side.
    """

    def __init__(self, trend_weight: float = 0.5):
        """
        Args:
            trend_weight: Weight (0-1) controlling how much recent trends
                influence the baseline. 0 uses only season averages; 1 uses
                only recent-trend-adjusted totals.
        """
        if not 0.0 <= trend_weight <= 1.0:
            raise ValueError("trend_weight must be between 0 and 1")
        self.trend_weight = trend_weight

    def estimate_total(self, team: TeamTrendStats, opponent: TeamTrendStats) -> float:
        """
        Estimate expected points/goals for a team vs an opponent.
        """
        base_score = (team.season_avg_for + opponent.season_avg_against) / 2
        team_off_trend, team_def_trend = team.recent_trend_factors()
        opp_off_trend, opp_def_trend = opponent.recent_trend_factors()

        trend_multiplier = (team_off_trend + opp_def_trend) / 2
        trend_score = base_score * trend_multiplier
        return (1 - self.trend_weight) * base_score + self.trend_weight * trend_score

    def estimate_match_total(
        self,
        home: TeamTrendStats,
        away: TeamTrendStats,
        line: Optional[float] = None,
    ) -> dict:
        """
        Estimate match total and optional over/under pick vs a betting line.

        Returns:
            dict with expected_total, home_expected, away_expected, and if
            line is provided: pick, edge, confidence.
        """
        home_expected = self.estimate_total(home, away)
        away_expected = self.estimate_total(away, home)
        expected_total = home_expected + away_expected

        response = {
            "expected_total": expected_total,
            "home_expected": home_expected,
            "away_expected": away_expected,
        }

        if line is not None:
            edge = expected_total - line
            pick = "OVER" if edge > 0 else "UNDER"
            confidence = min(0.85, 0.5 + abs(edge) / max(line, 1) * 0.5)
            response.update({
                "line": line,
                "pick": pick,
                "edge": edge,
                "confidence": confidence,
            })

        return response

    @staticmethod
    def build_team_stats(
        season_avg_for: float,
        season_avg_against: float,
        recent_for: Iterable[float],
        recent_against: Iterable[float],
    ) -> TeamTrendStats:
        """Helper to build TeamTrendStats from iterables."""
        return TeamTrendStats(
            season_avg_for=season_avg_for,
            season_avg_against=season_avg_against,
            recent_games_for=list(recent_for),
            recent_games_against=list(recent_against),
        )
