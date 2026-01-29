#!/usr/bin/env python3
"""
NBA Analytics Library

Statistical models and betting tools specifically designed for NBA (Basketball).
Includes pace-adjusted metrics, totals modeling, and player prop analysis.
"""

import math
import random
from typing import Any, Dict, List, Optional, Tuple

from lib.betting_core import make_bet_result


class NBAAnalytics:
    """NBA-specific betting analytics and simulations"""

    # NBA averages (2023-24 season)
    AVG_POINTS_PER_GAME = 115.0
    AVG_TOTAL_POINTS = 230.0
    AVG_HOME_ADVANTAGE = 3.5
    AVG_PACE = 99.5  # Possessions per 48 minutes
    AVG_OFFENSIVE_RATING = 115.0  # Points per 100 possessions
    AVG_DEFENSIVE_RATING = 115.0  # Points allowed per 100 possessions
    REST_ADVANTAGE_MULTIPLIER = 1.0
    MAX_REST_ADVANTAGE = 4.0
    BASE_STD_DEV = 11.0
    TOTAL_STD_DEV = 12.0

    @staticmethod
    def calculate_pace_adjusted_total(
        team1_pace: float,
        team2_pace: float,
        team1_off_rating: float,
        team2_off_rating: float,
        team1_def_rating: float,
        team2_def_rating: float
    ) -> Dict:
        """
        Calculate expected total using pace and efficiency metrics

        Args:
            team1_pace: Team 1 pace (possessions per 48 min)
            team2_pace: Team 2 pace
            team1_off_rating: Team 1 offensive rating (pts per 100 poss)
            team2_off_rating: Team 2 offensive rating
            team1_def_rating: Team 1 defensive rating (pts allowed per 100 poss)
            team2_def_rating: Team 2 defensive rating

        Returns:
            Expected scoring for both teams
        """
        # Combined pace
        game_pace = (team1_pace + team2_pace) / 2

        # Team 1 expected points
        # Based on their offense vs opponent's defense
        team1_efficiency = (team1_off_rating + team2_def_rating) / 2
        team1_expected = (team1_efficiency / 100) * game_pace

        # Team 2 expected points
        team2_efficiency = (team2_off_rating + team1_def_rating) / 2
        team2_expected = (team2_efficiency / 100) * game_pace

        return {
            'team1_expected': team1_expected,
            'team2_expected': team2_expected,
            'total_expected': team1_expected + team2_expected,
            'game_pace': game_pace
        }

    @staticmethod
    def calculate_rest_advantage(
        team_rest_days: int,
        opponent_rest_days: int
    ) -> float:
        """
        Calculate rest advantage impact on game outcome.

        NBA schedules are less compressed than WNBA, but rest still matters.

        Args:
            team_rest_days: Days of rest for team
            opponent_rest_days: Days of rest for opponent

        Returns:
            Rest advantage in points (positive = team advantage)
        """
        rest_diff = team_rest_days - opponent_rest_days
        if rest_diff == 0:
            return 0.0

        base_multiplier = 0.4 * NBAAnalytics.REST_ADVANTAGE_MULTIPLIER
        base_advantage = min(abs(rest_diff), 2) * base_multiplier
        extra_days = max(0, abs(rest_diff) - 2)
        extra_advantage = extra_days * 0.2 * NBAAnalytics.REST_ADVANTAGE_MULTIPLIER

        advantage = (base_advantage + extra_advantage) * (1 if rest_diff > 0 else -1)

        return max(-NBAAnalytics.MAX_REST_ADVANTAGE,
                   min(NBAAnalytics.MAX_REST_ADVANTAGE, advantage))

    @staticmethod
    def calculate_back_to_back_penalty(
        is_back_to_back: bool,
        traveled: bool = False
    ) -> float:
        """
        Calculate penalty for back-to-back games.

        Args:
            is_back_to_back: Whether team is on back-to-back
            traveled: Whether team traveled between games

        Returns:
            Penalty in points (negative)
        """
        if not is_back_to_back:
            return 0.0

        base_penalty = -2.0
        return base_penalty - 1.0 if traveled else base_penalty

    @staticmethod
    def calculate_schedule_adjustment(
        team_rest_days: int,
        opponent_rest_days: int,
        team_travel_penalty: float = 0.0,
        opponent_travel_penalty: float = 0.0
    ) -> float:
        """
        Combine rest and travel adjustments into a single rating tweak.

        Args:
            team_rest_days: Days of rest for team
            opponent_rest_days: Days of rest for opponent
            team_travel_penalty: Travel penalty for team (negative)
            opponent_travel_penalty: Travel penalty for opponent (negative)

        Returns:
            Net rating adjustment in points (positive = team advantage)
        """
        rest_advantage = NBAAnalytics.calculate_rest_advantage(
            team_rest_days, opponent_rest_days
        )
        team_b2b_penalty = NBAAnalytics.calculate_back_to_back_penalty(
            team_rest_days == 0
        )
        opp_b2b_penalty = NBAAnalytics.calculate_back_to_back_penalty(
            opponent_rest_days == 0
        )

        return rest_advantage + team_b2b_penalty - opp_b2b_penalty + team_travel_penalty - opponent_travel_penalty

    @staticmethod
    def calculate_spread_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        is_home: bool = True,
        schedule_adjustment: float = 0.0,
        std_dev: float = None
    ) -> Dict:
        """
        Calculate probability of covering the spread

        Args:
            team_rating: Team power rating (avg points per game)
            opponent_rating: Opponent power rating
            spread: Point spread (negative means favorite)
            is_home: Whether team is playing at home

        Returns:
            Cover probability and analysis
        """
        # Adjust for home court
        home_adj = NBAAnalytics.AVG_HOME_ADVANTAGE if is_home else -NBAAnalytics.AVG_HOME_ADVANTAGE

        # Expected point differential
        expected_diff = (team_rating - opponent_rating) + home_adj + schedule_adjustment

        # Adjusted for spread
        adjusted_diff = expected_diff - spread

        # NBA has lower variance than NFL (~11 points std dev)
        if std_dev is None:
            std_dev = NBAAnalytics.BASE_STD_DEV

        # Z-score
        z_score = adjusted_diff / std_dev

        # Probability
        cover_prob = NBAAnalytics._clamp_probability(NBAAnalytics._normal_cdf(z_score), 0.01, 0.99)

        return {
            'cover_probability': cover_prob,
            'expected_margin': expected_diff,
            'spread': spread,
            'confidence': 'high' if abs(z_score) > 1.5 else 'medium' if abs(z_score) > 0.75 else 'low'
        }

    @staticmethod
    def calculate_total_probability(
        team1_avg: float,
        team2_avg: float,
        total_line: float,
        pace_factor: float = 1.0,
        std_dev: float = None
    ) -> Dict:
        """
        Calculate over/under probability

        Args:
            team1_avg: Team 1 average points
            team2_avg: Team 2 average points
            total_line: Over/under line
            pace_factor: Pace adjustment (1.0 = normal)

        Returns:
            Over/under probabilities
        """
        # Expected total
        expected_total = (team1_avg + team2_avg) * pace_factor

        # Standard deviation for totals ~12 points
        if std_dev is None:
            std_dev = NBAAnalytics.TOTAL_STD_DEV

        # Z-score
        z_score = (total_line - expected_total) / std_dev

        # Probabilities
        under_prob = NBAAnalytics._clamp_probability(NBAAnalytics._normal_cdf(z_score), 0.01, 0.99)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': expected_total,
            'line': total_line,
            'difference': expected_total - total_line,
            'edge': abs(expected_total - total_line) / std_dev  # Edge in std deviations
        }

    @staticmethod
    def calculate_total_probability_from_expected(
        expected_total: float,
        total_line: float,
        std_dev: float = None
    ) -> Dict:
        """
        Calculate total probabilities when expected total is already known.

        Args:
            expected_total: Expected total points
            total_line: Over/under line
            std_dev: Standard deviation for totals

        Returns:
            Over/under probabilities and edge
        """
        if std_dev is None:
            std_dev = NBAAnalytics.TOTAL_STD_DEV

        z_score = (total_line - expected_total) / std_dev
        under_prob = NBAAnalytics._clamp_probability(NBAAnalytics._normal_cdf(z_score), 0.01, 0.99)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': expected_total,
            'line': total_line,
            'difference': expected_total - total_line,
            'edge': abs(expected_total - total_line) / std_dev
        }

    @staticmethod
    def calculate_moneyline_probability(
        team_rating: float,
        opponent_rating: float,
        is_home: bool = True,
        schedule_adjustment: float = 0.0,
        std_dev: float = None
    ) -> Dict:
        """
        Calculate moneyline win probability using rating differentials.

        Args:
            team_rating: Team power rating (avg points per game)
            opponent_rating: Opponent power rating
            is_home: Whether team is playing at home
            schedule_adjustment: Rest/travel adjustment
            std_dev: Standard deviation for margin distribution

        Returns:
            Home/away win probabilities
        """
        home_adj = NBAAnalytics.AVG_HOME_ADVANTAGE if is_home else -NBAAnalytics.AVG_HOME_ADVANTAGE
        expected_diff = (team_rating - opponent_rating) + home_adj + schedule_adjustment

        if std_dev is None:
            std_dev = NBAAnalytics.BASE_STD_DEV

        z_score = expected_diff / std_dev
        home_prob = NBAAnalytics._clamp_probability(NBAAnalytics._normal_cdf(z_score), 0.01, 0.99)
        away_prob = 1 - home_prob

        return {
            'home_win_probability': home_prob,
            'away_win_probability': away_prob,
            'expected_margin': expected_diff
        }

    @staticmethod
    def simulate_game(
        home_rating: float,
        away_rating: float,
        pace_factor: float = 1.0,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a single NBA game

        Args:
            home_rating: Home team rating (avg points)
            away_rating: Away team rating
            pace_factor: Game pace adjustment
            seed: Random seed

        Returns:
            Game result
        """
        rng = random.Random(seed) if seed is not None else random

        # Adjust for home court and pace
        home_adj = (home_rating + NBAAnalytics.AVG_HOME_ADVANTAGE) * pace_factor
        away_adj = away_rating * pace_factor

        # Simulate scores (normal distribution)
        home_score = max(0, int(rng.gauss(home_adj, 11) + 0.5))
        away_score = max(0, int(rng.gauss(away_adj, 11) + 0.5))

        margin = home_score - away_score
        total = home_score + away_score

        if margin > 0:
            result = 'home_win'
        elif margin < 0:
            result = 'away_win'
        else:
            result = 'overtime'  # Simplified - NBA rarely ties

        return {
            'home_score': home_score,
            'away_score': away_score,
            'margin': margin,
            'total': total,
            'result': result
        }

    @staticmethod
    def calculate_player_prop_probability(
        player_avg: float,
        prop_line: float,
        player_std_dev: float = None,
        usage_adjustment: float = 1.0
    ) -> Dict:
        """
        Calculate probability for player prop bet (points, rebounds, assists)

        Args:
            player_avg: Player's average for the stat
            prop_line: Prop line (over/under)
            player_std_dev: Player's standard deviation (if None, estimated)
            usage_adjustment: Adjustment for expected usage (1.0 = normal)

        Returns:
            Over/under probabilities for prop
        """
        # Adjust for usage
        adjusted_avg = player_avg * usage_adjustment

        # Estimate std dev if not provided (typically ~25% of average)
        if player_std_dev is None:
            player_std_dev = player_avg * 0.25

        # Z-score
        z_score = (prop_line - adjusted_avg) / player_std_dev

        # Probabilities
        under_prob = NBAAnalytics._clamp_probability(NBAAnalytics._normal_cdf(z_score), 0.01, 0.99)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'player_average': player_avg,
            'adjusted_average': adjusted_avg,
            'prop_line': prop_line,
            'std_dev': player_std_dev,
            'edge': (adjusted_avg - prop_line) / player_std_dev
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        games_per_team: int = 82,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate NBA season

        Args:
            teams: Team ratings dictionary
            games_per_team: Games per team (NBA = 82)
            seed: Random seed

        Returns:
            Season standings
        """
        rng = random.Random(seed) if seed is not None else random

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'losses': 0, 'pf': 0, 'pa': 0}
                    for team in team_names}

        matches = []
        total_games = (len(team_names) * games_per_team) // 2

        for _ in range(total_games):
            # Random matchup
            home_team = rng.choice(team_names)
            away_team = rng.choice([t for t in team_names if t != home_team])

            # Simulate game
            game = NBAAnalytics.simulate_game(teams[home_team], teams[away_team])

            # Update standings
            standings[home_team]['pf'] += game['home_score']
            standings[home_team]['pa'] += game['away_score']
            standings[away_team]['pf'] += game['away_score']
            standings[away_team]['pa'] += game['home_score']

            if game['result'] == 'home_win':
                standings[home_team]['wins'] += 1
                standings[away_team]['losses'] += 1
            else:
                standings[away_team]['wins'] += 1
                standings[home_team]['losses'] += 1

            matches.append({
                'home': home_team,
                'away': away_team,
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'margin': game['margin']
            })

        # Calculate win percentage
        for team in standings:
            games = standings[team]['wins'] + standings[team]['losses']
            if games > 0:
                standings[team]['win_pct'] = standings[team]['wins'] / games
            else:
                standings[team]['win_pct'] = 0.0

        # Sort by win percentage
        sorted_standings = sorted(
            standings.items(),
            key=lambda x: (x[1]['win_pct'], x[1]['pf'] - x[1]['pa']),
            reverse=True
        )

        return {
            'standings': dict(sorted_standings),
            'matches': matches
        }

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """Cumulative distribution function for standard normal"""
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    @staticmethod
    def _clamp_probability(probability: float, minimum: float, maximum: float) -> float:
        """Clamp a probability to a range."""
        return max(minimum, min(maximum, probability))


class NBABettingInterface:
    """
    SportsBetLang-friendly wrapper for NBA markets.

    Expected (flexible) model method names:
      - moneyline: predict_moneyline / predict_game / predict
        returning dict with home prob key:
          'home_win_prob' OR 'home_win_probability' OR 'p_home' OR 'home_prob'
      - spread: predict_spread / predict_game / predict
        returning dict with:
          'home_cover_prob' OR 'cover_probability' (for home side)
      - total: predict_total / predict_game_total / predict
        returning dict with:
          'expected_total' OR 'total'
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

    def predict_moneyline(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, Any]:
        votes, probs, raw = self._collect_moneyline(home_team, away_team, features)
        if probs:
            p_home = self._avg_or_default(probs, 0.5)
        else:
            p_home = self._fallback_moneyline_prob(features)

        p_home = NBAAnalytics._clamp_probability(p_home, 0.01, 0.99)
        p_away = 1.0 - p_home

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "model_probs_home": probs,
            "model_votes": votes,
            "raw": raw,
        }

        return {
            "HOME": make_bet_result(
                sport="NBA",
                bet_type="MONEY",
                pick="HOME",
                prob=p_home,
                market_odds=market_home_odds,
                model_votes=votes,
                model_probs=probs,
                details=details,
            ),
            "AWAY": make_bet_result(
                sport="NBA",
                bet_type="MONEY",
                pick="AWAY",
                prob=p_away,
                market_odds=market_away_odds,
                model_votes=votes,
                model_probs=probs,
                details=details,
            ),
        }

    def predict_spread(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        line_home: float,
        line_away: float,
        market_home_odds: Optional[float] = None,
        market_away_odds: Optional[float] = None,
    ) -> Dict[str, Any]:
        votes, probs, raw = self._collect_spread(home_team, away_team, features, line_home, line_away)
        if probs:
            p_home_cover = self._avg_or_default(probs, 0.5)
        else:
            p_home_cover = self._fallback_spread_prob(features, line_home)

        p_home_cover = NBAAnalytics._clamp_probability(p_home_cover, 0.01, 0.99)
        p_away_cover = 1.0 - p_home_cover

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "line_home": line_home,
            "line_away": line_away,
            "model_probs_home_cover": probs,
            "model_votes": votes,
            "raw": raw,
        }

        return {
            "HOME": make_bet_result(
                sport="NBA",
                bet_type="SPREAD",
                pick=f"HOME {line_home:+.1f}",
                prob=p_home_cover,
                market_odds=market_home_odds,
                model_votes=votes,
                model_probs=probs,
                details=details,
            ),
            "AWAY": make_bet_result(
                sport="NBA",
                bet_type="SPREAD",
                pick=f"AWAY {line_away:+.1f}",
                prob=p_away_cover,
                market_odds=market_away_odds,
                model_votes=votes,
                model_probs=probs,
                details=details,
            ),
        }

    def predict_total(
        self,
        home_team: str,
        away_team: str,
        features: Dict[str, float],
        total_line: float,
        market_over_odds: Optional[float] = None,
        market_under_odds: Optional[float] = None,
    ) -> Dict[str, Any]:
        expected_total, source = self._expected_total(home_team, away_team, features)
        totals = NBAAnalytics.calculate_total_probability_from_expected(
            expected_total=expected_total,
            total_line=total_line,
        )

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "expected_total": expected_total,
            "total_line": total_line,
            "total_source": source,
        }

        return {
            "OVER": make_bet_result(
                sport="NBA",
                bet_type="TOTAL",
                pick=f"OVER {total_line:.1f}",
                prob=totals["over_probability"],
                market_odds=market_over_odds,
                details=details,
            ),
            "UNDER": make_bet_result(
                sport="NBA",
                bet_type="TOTAL",
                pick=f"UNDER {total_line:.1f}",
                prob=totals["under_probability"],
                market_odds=market_under_odds,
                details=details,
            ),
        }

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
                ["predict_spread", "predict_game", "predict"],
                home, away, features, line_home, line_away
            )
            raw[name] = out
            p = self._extract_home_cover_prob(out)
            if p is not None:
                probs[name] = p
                votes[name] = f"HOME {line_home:+.1f}" if p >= 0.5 else f"AWAY {line_away:+.1f}"

        return votes, probs, raw

    def _expected_total(
        self, home: str, away: str, features: Dict[str, float]
    ) -> Tuple[float, str]:
        for name, model in (("power", self.power), ("similar", self.similar), ("tree", self.tree)):
            if model is None:
                continue
            out = self._safe_call(model, ["predict_total", "predict_game_total", "predict"], home, away, features)
            expected = self._extract_expected_total(out)
            if expected is not None:
                return expected, f"{name}.model"

        pace = features.get("pace", None)
        home_pace = features.get("home_pace", pace)
        away_pace = features.get("away_pace", pace)
        home_off = features.get("home_off_rating", features.get("home_offense"))
        away_off = features.get("away_off_rating", features.get("away_offense"))
        home_def = features.get("home_def_rating", features.get("home_defense"))
        away_def = features.get("away_def_rating", features.get("away_defense"))

        if None not in (home_pace, away_pace, home_off, away_off, home_def, away_def):
            total = NBAAnalytics.calculate_pace_adjusted_total(
                team1_pace=float(home_pace),
                team2_pace=float(away_pace),
                team1_off_rating=float(home_off),
                team2_off_rating=float(away_off),
                team1_def_rating=float(home_def),
                team2_def_rating=float(away_def),
            )["total_expected"]
            return total, "pace_adjusted"

        home_avg = features.get("home_avg_points", features.get("home_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        away_avg = features.get("away_avg_points", features.get("away_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        pace_factor = float(features.get("pace_factor", 1.0))
        total = NBAAnalytics.calculate_total_probability(
            team1_avg=float(home_avg),
            team2_avg=float(away_avg),
            total_line=NBAAnalytics.AVG_TOTAL_POINTS,
            pace_factor=pace_factor,
        )["expected_total"]
        return total, "team_avg"

    def _fallback_moneyline_prob(self, features: Dict[str, float]) -> float:
        home_rating = float(features.get("home_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        away_rating = float(features.get("away_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        schedule_adjustment = float(features.get("schedule_adjustment", 0.0))
        result = NBAAnalytics.calculate_moneyline_probability(
            team_rating=home_rating,
            opponent_rating=away_rating,
            is_home=True,
            schedule_adjustment=schedule_adjustment,
        )
        return float(result["home_win_probability"])

    def _fallback_spread_prob(self, features: Dict[str, float], line_home: float) -> float:
        home_rating = float(features.get("home_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        away_rating = float(features.get("away_rating", NBAAnalytics.AVG_POINTS_PER_GAME))
        schedule_adjustment = float(features.get("schedule_adjustment", 0.0))
        result = NBAAnalytics.calculate_spread_probability(
            team_rating=home_rating,
            opponent_rating=away_rating,
            spread=line_home,
            is_home=True,
            schedule_adjustment=schedule_adjustment,
        )
        return float(result["cover_probability"])

    @staticmethod
    def _safe_call(model: Any, method_names: List[str], *args) -> Any:
        for method in method_names:
            if hasattr(model, method):
                fn = getattr(model, method)
                try:
                    return fn(*args)
                except TypeError:
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
        for key in ("home_win_prob", "home_win_probability", "p_home", "home_prob", "prob_home"):
            if key in out and out[key] is not None:
                try:
                    return float(out[key])
                except Exception:
                    return None
        return None

    @staticmethod
    def _extract_home_cover_prob(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for key in ("home_cover_prob", "cover_probability", "p_home_cover"):
            if key in out and out[key] is not None:
                try:
                    return float(out[key])
                except Exception:
                    return None
        return None

    @staticmethod
    def _extract_expected_total(out: Any) -> Optional[float]:
        if not isinstance(out, dict):
            return None
        for key in ("expected_total", "total", "predicted_total"):
            if key in out and out[key] is not None:
                try:
                    return float(out[key])
                except Exception:
                    return None
        return None

    @staticmethod
    def _avg_or_default(d: Dict[str, float], default: float) -> float:
        if not d:
            return default
        return sum(d.values()) / float(len(d))


if __name__ == '__main__':
    print("NBA Analytics Library")
    print("=" * 70)

    # Example 1: Spread analysis
    print("\nExample 1: Spread Analysis")
    spread_result = NBAAnalytics.calculate_spread_probability(
        team_rating=115.0,
        opponent_rating=108.0,
        spread=-7.5,
        is_home=True
    )
    print(f"Cover Probability: {spread_result['cover_probability']*100:.1f}%")
    print(f"Expected Margin: {spread_result['expected_margin']:.1f}")
    print(f"Confidence: {spread_result['confidence']}")

    # Example 2: Total analysis
    print("\nExample 2: Total Analysis")
    total_result = NBAAnalytics.calculate_total_probability(
        team1_avg=118.5,
        team2_avg=112.3,
        total_line=230.5
    )
    print(f"Over Probability: {total_result['over_probability']*100:.1f}%")
    print(f"Expected Total: {total_result['expected_total']:.1f}")

    # Example 3: Player prop
    print("\nExample 3: Player Prop Analysis")
    prop_result = NBAAnalytics.calculate_player_prop_probability(
        player_avg=28.5,
        prop_line=27.5,
        player_std_dev=7.0
    )
    print(f"Over Probability: {prop_result['over_probability']*100:.1f}%")
    print(f"Edge: {prop_result['edge']:.2f} std devs")
