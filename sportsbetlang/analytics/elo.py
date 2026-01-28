"""
SportsBetLang Analytics - Elo Ratings

Provides an Elo rating system for predicting match outcomes with configurable
home advantage and optional margin-of-victory scaling.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class TeamRating:
    """Represents a team with an Elo rating."""

    name: str
    rating: float
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0


class EloRatingSystem:
    """Elo rating system for sports."""

    DEFAULT_RATING = 1500.0
    DEFAULT_K_FACTOR = 32.0

    def __init__(
        self,
        k_factor: float = DEFAULT_K_FACTOR,
        home_advantage: float = 100.0,
        mov_multiplier: bool = True,
        draw_probability: float = 0.15,
    ) -> None:
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.mov_multiplier = mov_multiplier
        self.draw_probability = draw_probability
        self.teams: Dict[str, TeamRating] = {}

    def get_or_create_team(self, name: str) -> TeamRating:
        if name not in self.teams:
            self.teams[name] = TeamRating(name=name, rating=self.DEFAULT_RATING)
        return self.teams[name]

    @staticmethod
    def expected_score(rating_a: float, rating_b: float) -> float:
        """Calculate expected score using Elo formula."""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    @staticmethod
    def _mov_multiplier(score_diff: int, winning_rating: float, losing_rating: float) -> float:
        if score_diff <= 0:
            return 1.0
        return max(
            1.0,
            math.log(abs(score_diff) + 1) * 2.2 / ((winning_rating - losing_rating) * 0.001 + 2.2),
        )

    def update_ratings(
        self,
        home_team_name: str,
        away_team_name: str,
        home_score: int,
        away_score: int,
    ) -> Tuple[float, float]:
        home_team = self.get_or_create_team(home_team_name)
        away_team = self.get_or_create_team(away_team_name)

        home_rating_adj = home_team.rating + self.home_advantage
        away_rating_adj = away_team.rating

        home_expected = self.expected_score(home_rating_adj, away_rating_adj)
        away_expected = 1 - home_expected

        if home_score > away_score:
            home_actual = 1.0
            away_actual = 0.0
        elif home_score < away_score:
            home_actual = 0.0
            away_actual = 1.0
        else:
            home_actual = 0.5
            away_actual = 0.5

        k = self.k_factor
        if self.mov_multiplier and home_score != away_score:
            score_diff = abs(home_score - away_score)
            if home_score > away_score:
                k *= self._mov_multiplier(score_diff, home_team.rating, away_team.rating)
            else:
                k *= self._mov_multiplier(score_diff, away_team.rating, home_team.rating)

        home_change = k * (home_actual - home_expected)
        away_change = k * (away_actual - away_expected)

        home_team.rating += home_change
        away_team.rating += away_change

        home_team.games_played += 1
        away_team.games_played += 1

        if home_score > away_score:
            home_team.wins += 1
            away_team.losses += 1
        elif home_score < away_score:
            home_team.losses += 1
            away_team.wins += 1
        else:
            home_team.draws += 1
            away_team.draws += 1

        return home_change, away_change

    def predict_match(self, home_team_name: str, away_team_name: str) -> Dict[str, float]:
        home_team = self.get_or_create_team(home_team_name)
        away_team = self.get_or_create_team(away_team_name)

        home_rating_adj = home_team.rating + self.home_advantage
        away_rating_adj = away_team.rating

        home_win_prob = self.expected_score(home_rating_adj, away_rating_adj)
        away_win_prob = 1 - home_win_prob

        draw_prob = 0.0
        if self.draw_probability > 0:
            draw_prob = min(self.draw_probability, 1.0)
            draw_prob *= min(home_win_prob, away_win_prob)

        home_win_prob *= 1 - draw_prob
        away_win_prob *= 1 - draw_prob

        rating_diff = home_rating_adj - away_rating_adj
        spread = rating_diff / 25

        return {
            "home_team": home_team_name,
            "away_team": away_team_name,
            "home_rating": home_team.rating,
            "away_rating": away_team.rating,
            "rating_difference": home_team.rating - away_team.rating,
            "home_win_prob": home_win_prob,
            "draw_prob": draw_prob,
            "away_win_prob": away_win_prob,
            "predicted_spread": spread,
            "home_advantage_points": self.home_advantage,
        }

    def get_rankings(self, top_n: Optional[int] = None) -> List[TeamRating]:
        sorted_teams = sorted(self.teams.values(), key=lambda team: team.rating, reverse=True)
        if top_n is None:
            return sorted_teams
        return sorted_teams[:top_n]
