"""
Multi-market ratings model for spread and totals across multiple sports.

Maintains offense/defense (and optional pace) ratings per team to predict
expected scores, spreads, totals, and cover/over probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union


@dataclass
class TeamState:
    """Team ratings for multi-market predictions."""

    name: str
    offense: float = 0.0
    defense: float = 0.0
    pace: float = 0.0
    games_played: int = 0


@dataclass(frozen=True)
class SportConfig:
    """Configuration defaults for a sport."""

    sport: str
    base_total: float
    home_advantage: float
    spread_stdev: float
    total_stdev: float
    scoring_scale: float
    k_off: float
    k_def: float
    k_pace: float


SPORT_CONFIGS: Dict[str, SportConfig] = {
    "NBA": SportConfig(
        sport="NBA",
        base_total=225.0,
        home_advantage=2.0,
        spread_stdev=12.0,
        total_stdev=14.0,
        scoring_scale=112.5,
        k_off=0.20,
        k_def=0.20,
        k_pace=0.10,
    ),
    "NFL": SportConfig(
        sport="NFL",
        base_total=44.0,
        home_advantage=1.5,
        spread_stdev=13.5,
        total_stdev=10.5,
        scoring_scale=22.0,
        k_off=0.25,
        k_def=0.25,
        k_pace=0.12,
    ),
    "NHL": SportConfig(
        sport="NHL",
        base_total=6.2,
        home_advantage=0.25,
        spread_stdev=1.4,
        total_stdev=1.2,
        scoring_scale=3.1,
        k_off=0.35,
        k_def=0.35,
        k_pace=0.15,
    ),
    "MLB": SportConfig(
        sport="MLB",
        base_total=8.6,
        home_advantage=0.2,
        spread_stdev=1.6,
        total_stdev=1.4,
        scoring_scale=4.3,
        k_off=0.30,
        k_def=0.30,
        k_pace=0.12,
    ),
}


CSV_ALIASES: Dict[str, str] = {
    "home": "home_team",
    "away": "away_team",
    "home_points": "home_score",
    "away_points": "away_score",
    "home_runs": "home_score",
    "away_runs": "away_score",
    "home_goals": "home_score",
    "away_goals": "away_score",
    "neutral": "neutral_site",
    "neutral_flag": "neutral_site",
}


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _prob_over(mean: float, stdev: float, line: float) -> float:
    if stdev <= 0:
        return 0.5
    z = (line - mean) / stdev
    return 1.0 - _normal_cdf(z)


def _prob_under(mean: float, stdev: float, line: float) -> float:
    if stdev <= 0:
        return 0.5
    z = (line - mean) / stdev
    return _normal_cdf(z)


def normalize_game_row(row: Dict[str, Any], sport: Optional[str] = None) -> Dict[str, Any]:
    """Normalize a CSV row or dict into the canonical game schema."""

    normalized = dict(row)
    for alias, canonical in CSV_ALIASES.items():
        if alias in normalized and canonical not in normalized:
            normalized[canonical] = normalized[alias]

    if sport and "sport" not in normalized:
        normalized["sport"] = sport

    if "neutral_site" in normalized:
        neutral_value = normalized["neutral_site"]
        if isinstance(neutral_value, str):
            normalized["neutral_site"] = neutral_value.strip().lower() in {
                "1",
                "true",
                "yes",
                "y",
            }
        else:
            normalized["neutral_site"] = bool(neutral_value)

    required = ["home_team", "away_team", "home_score", "away_score"]
    missing = [key for key in required if key not in normalized]
    if missing:
        raise ValueError(f"Game data missing required fields: {', '.join(missing)}")

    return normalized


def parse_games_csv(path: Union[str, Path], sport: Optional[str] = None) -> List[Dict[str, Any]]:
    """Parse a CSV file of games into canonical game dictionaries."""

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [normalize_game_row(row, sport=sport) for row in reader]


class MultiMarketRatingsModel:
    """Baseline multi-market ratings model for spreads and totals."""

    def __init__(
        self,
        sport: str,
        window: Optional[int] = None,
        k_off: Optional[float] = None,
        k_def: Optional[float] = None,
        home_adv: Optional[float] = None,
        base_total: Optional[float] = None,
        base_spread: float = 0.0,
        spread_stdev: Optional[float] = None,
        total_stdev: Optional[float] = None,
        scoring_scale: Optional[float] = None,
        k_pace: Optional[float] = None,
    ) -> None:
        sport_key = sport.upper()
        if sport_key not in SPORT_CONFIGS:
            raise ValueError(f"Unsupported sport '{sport}'.")
        config = SPORT_CONFIGS[sport_key]

        self.sport = sport_key
        self.window = window
        self.base_spread = base_spread
        self.base_total = base_total if base_total is not None else config.base_total
        self.home_advantage = home_adv if home_adv is not None else config.home_advantage
        self.spread_stdev = spread_stdev if spread_stdev is not None else config.spread_stdev
        self.total_stdev = total_stdev if total_stdev is not None else config.total_stdev
        self.scoring_scale = scoring_scale if scoring_scale is not None else config.scoring_scale
        self.k_off = k_off if k_off is not None else config.k_off
        self.k_def = k_def if k_def is not None else config.k_def
        self.k_pace = k_pace if k_pace is not None else config.k_pace
        self.teams: Dict[str, TeamState] = {}

    def get_team(self, name: str) -> Optional[TeamState]:
        return self.teams.get(name)

    def get_or_create_team(self, name: str) -> TeamState:
        if name not in self.teams:
            self.teams[name] = TeamState(name=name)
        return self.teams[name]

    def _window_weight(self, team: TeamState) -> float:
        if not self.window:
            return 1.0
        return min(1.0, self.window / max(1, team.games_played))

    def _expected_scores(
        self,
        home: TeamState,
        away: TeamState,
        neutral_site: bool,
    ) -> Dict[str, float]:
        pace_total = self.base_total + home.pace + away.pace
        hfa = 0.0 if neutral_site else self.home_advantage
        expected_home = (
            pace_total / 2
            + hfa / 2
            + home.offense
            - away.defense
        )
        expected_away = (
            pace_total / 2
            - hfa / 2
            + away.offense
            - home.defense
        )
        return {"home": expected_home, "away": expected_away}

    def predict(self, home_team: str, away_team: str, neutral_site: bool = False) -> Dict[str, float]:
        home = self.get_or_create_team(home_team)
        away = self.get_or_create_team(away_team)
        expected = self._expected_scores(home, away, neutral_site)
        spread = (expected["home"] - expected["away"]) + self.base_spread
        total = expected["home"] + expected["away"]
        return {
            "home_score": expected["home"],
            "away_score": expected["away"],
            "spread": spread,
            "total": total,
        }

    def predict_spread(self, home_team: str, away_team: str, neutral_site: bool = False) -> float:
        return self.predict(home_team, away_team, neutral_site)["spread"]

    def predict_total(self, home_team: str, away_team: str, neutral_site: bool = False) -> float:
        return self.predict(home_team, away_team, neutral_site)["total"]

    def prob_cover(
        self,
        home_team: str,
        away_team: str,
        spread_line: float,
        stdev: Optional[float] = None,
        neutral_site: bool = False,
    ) -> float:
        mean = self.predict_spread(home_team, away_team, neutral_site)
        sigma = stdev if stdev is not None else self.spread_stdev
        return _prob_over(mean, sigma, spread_line)

    def prob_away_cover(
        self,
        home_team: str,
        away_team: str,
        spread_line: float,
        stdev: Optional[float] = None,
        neutral_site: bool = False,
    ) -> float:
        mean = self.predict_spread(home_team, away_team, neutral_site)
        sigma = stdev if stdev is not None else self.spread_stdev
        return _prob_under(mean, sigma, spread_line)

    def prob_over(
        self,
        home_team: str,
        away_team: str,
        total_line: float,
        stdev: Optional[float] = None,
        neutral_site: bool = False,
    ) -> float:
        mean = self.predict_total(home_team, away_team, neutral_site)
        sigma = stdev if stdev is not None else self.total_stdev
        return _prob_over(mean, sigma, total_line)

    def prob_under(
        self,
        home_team: str,
        away_team: str,
        total_line: float,
        stdev: Optional[float] = None,
        neutral_site: bool = False,
    ) -> float:
        mean = self.predict_total(home_team, away_team, neutral_site)
        sigma = stdev if stdev is not None else self.total_stdev
        return _prob_under(mean, sigma, total_line)

    def update(self, game: Union[Dict[str, Any], object]) -> None:
        game_data = self._coerce_game(game)

        home_team = game_data["home_team"]
        away_team = game_data["away_team"]
        home_score = float(game_data["home_score"])
        away_score = float(game_data["away_score"])
        neutral_site = bool(game_data.get("neutral_site", False))

        home = self.get_or_create_team(home_team)
        away = self.get_or_create_team(away_team)

        expected = self._expected_scores(home, away, neutral_site)
        expected_home = expected["home"]
        expected_away = expected["away"]

        scale = max(self.scoring_scale, 1.0)
        total_error = (home_score + away_score) - (expected_home + expected_away)
        pace_step = self.k_pace * (total_error / scale)

        home_off_error = (home_score - expected_home) / scale
        away_off_error = (away_score - expected_away) / scale
        home_def_error = (expected_away - away_score) / scale
        away_def_error = (expected_home - home_score) / scale

        home_weight = self._window_weight(home)
        away_weight = self._window_weight(away)

        home.offense += self.k_off * home_off_error * home_weight
        home.defense += self.k_def * home_def_error * home_weight
        away.offense += self.k_off * away_off_error * away_weight
        away.defense += self.k_def * away_def_error * away_weight

        home.pace += pace_step * home_weight
        away.pace += pace_step * away_weight

        home.games_played += 1
        away.games_played += 1

    def fit(self, games: Iterable[Union[Dict[str, Any], object]]) -> "MultiMarketRatingsModel":
        for game in games:
            self.update(game)
        return self

    def _coerce_game(self, game: Union[Dict[str, Any], object]) -> Dict[str, Any]:
        if isinstance(game, dict):
            game_data = dict(game)
        else:
            game_data = {
                "home_team": getattr(game, "home_team"),
                "away_team": getattr(game, "away_team"),
                "home_score": getattr(game, "home_score"),
                "away_score": getattr(game, "away_score"),
            }
            if hasattr(game, "neutral_site"):
                game_data["neutral_site"] = getattr(game, "neutral_site")

        for alias, canonical in CSV_ALIASES.items():
            if alias in game_data and canonical not in game_data:
                game_data[canonical] = game_data[alias]

        required = ["home_team", "away_team", "home_score", "away_score"]
        missing = [key for key in required if key not in game_data]
        if missing:
            raise ValueError(f"Game data missing required fields: {', '.join(missing)}")
        return game_data
