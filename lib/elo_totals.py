"""
Elo-based totals model for basketball and football over/under markets.

Maintains separate offensive and defensive Elo ratings per team, converts
offense-vs-defense gaps into expected points, and updates ratings based on
point and total errors.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, Iterable, Optional, Tuple, Union


LEAGUE_DEFAULTS = {
    "NBA": {
        "base_total": 220.0,
        "base_total_std": 12.0,
        "home_field_adv": 2.0,
    },
    "NFL": {
        "base_total": 44.0,
        "base_total_std": 7.0,
        "home_field_adv": 1.5,
    },
}


@dataclass
class TeamEloTotals:
    """Team ratings for offense and defense in the totals model."""

    name: str
    offense: float = 1500.0
    defense: float = 1500.0
    games_played: int = 0


class EloTotalsModel:
    """
    Elo-based totals model using separate offense/defense ratings.

    Ratings are stored on an Elo scale, but mapped to expected points using
    points_per_elo. Updates use normalized point errors scaled by a K-factor
    and a total-error multiplier.
    """

    def __init__(
        self,
        league: str = "NBA",
        k_factor: float = 20.0,
        base_total: Optional[float] = None,
        base_total_std: Optional[float] = None,
        points_per_elo: float = 0.025,
    ) -> None:
        league_defaults = LEAGUE_DEFAULTS.get(league.upper(), LEAGUE_DEFAULTS["NBA"])
        self.league = league.upper()
        self.k_factor = k_factor
        self.base_total = base_total if base_total is not None else league_defaults["base_total"]
        self.base_total_std = (
            base_total_std if base_total_std is not None else league_defaults["base_total_std"]
        )
        self.points_per_elo = points_per_elo
        self.teams: Dict[str, TeamEloTotals] = {}

    def get_or_create_team(self, name: str) -> TeamEloTotals:
        """Fetch team ratings, creating defaults when unseen."""
        if name not in self.teams:
            self.teams[name] = TeamEloTotals(name=name)
        return self.teams[name]

    def _expected_points(
        self,
        offense_rating: float,
        defense_rating: float,
        league_avg_total: float,
        home_field_adv: float,
        is_home: bool,
        neutral_site: bool,
    ) -> float:
        base_points = league_avg_total / 2
        rating_gap = offense_rating - defense_rating
        expected = base_points + rating_gap * self.points_per_elo
        if not neutral_site:
            expected += (home_field_adv / 2) if is_home else -(home_field_adv / 2)
        return expected

    def predict_total(
        self,
        home_team: str,
        away_team: str,
        neutral_site: bool = False,
        home_field_adv: Optional[float] = None,
        league_avg_total: Optional[float] = None,
    ) -> float:
        """
        Predict the total points for a matchup.

        Args:
            home_team: Home team name.
            away_team: Away team name.
            neutral_site: Whether the game is on a neutral field.
            home_field_adv: Points added to home, subtracted from away.
            league_avg_total: Override for league average total.
        """
        league_total = league_avg_total or self.base_total
        hfa = home_field_adv if home_field_adv is not None else LEAGUE_DEFAULTS.get(
            self.league, LEAGUE_DEFAULTS["NBA"]
        )["home_field_adv"]

        home = self.get_or_create_team(home_team)
        away = self.get_or_create_team(away_team)

        expected_home = self._expected_points(
            home.offense, away.defense, league_total, hfa, True, neutral_site
        )
        expected_away = self._expected_points(
            away.offense, home.defense, league_total, hfa, False, neutral_site
        )
        return expected_home + expected_away

    def predict_distribution(
        self,
        home_team: str,
        away_team: str,
        neutral_site: bool = False,
        home_field_adv: Optional[float] = None,
        league_avg_total: Optional[float] = None,
    ) -> Tuple[float, float]:
        """Return (mean, std) for the total points distribution."""
        mean = self.predict_total(
            home_team,
            away_team,
            neutral_site=neutral_site,
            home_field_adv=home_field_adv,
            league_avg_total=league_avg_total,
        )
        return mean, self.base_total_std

    def prob_over(
        self,
        home_team: str,
        away_team: str,
        line: float,
        neutral_site: bool = False,
        home_field_adv: Optional[float] = None,
        league_avg_total: Optional[float] = None,
    ) -> float:
        """Return probability total points go over the given line."""
        mean, std = self.predict_distribution(
            home_team,
            away_team,
            neutral_site=neutral_site,
            home_field_adv=home_field_adv,
            league_avg_total=league_avg_total,
        )
        if std <= 0:
            return 0.5
        z = (line - mean) / (std * math.sqrt(2))
        return 1 - 0.5 * (1 + math.erf(z))

    def update(self, game: Union[Dict[str, float], object]) -> None:
        """
        Update ratings based on a completed game.

        Accepts a dict or object with: home_team, away_team, home_score, away_score,
        optional neutral_site, home_field_adv, and league_avg_total.
        """
        game_data = self._coerce_game(game)

        home_team = game_data["home_team"]
        away_team = game_data["away_team"]
        home_score = float(game_data["home_score"])
        away_score = float(game_data["away_score"])
        neutral_site = bool(game_data.get("neutral_site", False))
        home_field_adv = game_data.get("home_field_adv")
        league_avg_total = game_data.get("league_avg_total")

        league_total = league_avg_total or self.base_total
        hfa = home_field_adv if home_field_adv is not None else LEAGUE_DEFAULTS.get(
            self.league, LEAGUE_DEFAULTS["NBA"]
        )["home_field_adv"]

        home = self.get_or_create_team(home_team)
        away = self.get_or_create_team(away_team)

        expected_home = self._expected_points(
            home.offense, away.defense, league_total, hfa, True, neutral_site
        )
        expected_away = self._expected_points(
            away.offense, home.defense, league_total, hfa, False, neutral_site
        )

        total_error = (home_score + away_score) - (expected_home + expected_away)
        total_multiplier = 1 + abs(total_error) / max(league_total, 1)

        home_off_error = (home_score - expected_home) / max(league_total, 1)
        away_off_error = (away_score - expected_away) / max(league_total, 1)
        home_def_error = (expected_away - away_score) / max(league_total, 1)
        away_def_error = (expected_home - home_score) / max(league_total, 1)

        home.offense += self.k_factor * home_off_error * total_multiplier
        home.defense += self.k_factor * home_def_error * total_multiplier
        away.offense += self.k_factor * away_off_error * total_multiplier
        away.defense += self.k_factor * away_def_error * total_multiplier

        home.games_played += 1
        away.games_played += 1

    def fit(self, games: Iterable[Union[Dict[str, float], object]]) -> "EloTotalsModel":
        """Update ratings sequentially for a list of games."""
        for game in games:
            self.update(game)
        return self

    def _coerce_game(self, game: Union[Dict[str, float], object]) -> Dict[str, float]:
        if isinstance(game, dict):
            game_data = dict(game)
        else:
            game_data = {
                "home_team": getattr(game, "home_team"),
                "away_team": getattr(game, "away_team"),
                "home_score": getattr(game, "home_score"),
                "away_score": getattr(game, "away_score"),
            }

        aliases = {
            "home": "home_team",
            "away": "away_team",
            "home_points": "home_score",
            "away_points": "away_score",
        }
        for alias, canonical in aliases.items():
            if alias in game_data and canonical not in game_data:
                game_data[canonical] = game_data[alias]

        required = ["home_team", "away_team", "home_score", "away_score"]
        missing = [key for key in required if key not in game_data]
        if missing:
            raise ValueError(f"Game data missing required fields: {', '.join(missing)}")
        return game_data
