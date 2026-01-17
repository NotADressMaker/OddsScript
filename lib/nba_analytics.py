#!/usr/bin/env python3
"""
NBA Analytics Library

Statistical models and betting tools specifically designed for NBA (Basketball).
Includes pace-adjusted metrics, totals modeling, and player prop analysis.
"""

import math
import random
from typing import Dict, List, Tuple, Optional


class NBAAnalytics:
    """NBA-specific betting analytics and simulations"""

    # NBA averages (2023-24 season)
    AVG_POINTS_PER_GAME = 115.0
    AVG_TOTAL_POINTS = 230.0
    AVG_HOME_ADVANTAGE = 3.5
    AVG_PACE = 99.5  # Possessions per 48 minutes
    AVG_OFFENSIVE_RATING = 115.0  # Points per 100 possessions

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
    def calculate_spread_probability(
        team_rating: float,
        opponent_rating: float,
        spread: float,
        is_home: bool = True
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
        expected_diff = (team_rating - opponent_rating) + home_adj

        # Adjusted for spread
        adjusted_diff = expected_diff - spread

        # NBA has lower variance than NFL (~11 points std dev)
        std_dev = 11.0

        # Z-score
        z_score = adjusted_diff / std_dev

        # Probability
        cover_prob = NBAAnalytics._normal_cdf(z_score)

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
        pace_factor: float = 1.0
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
        std_dev = 12.0

        # Z-score
        z_score = (total_line - expected_total) / std_dev

        # Probabilities
        under_prob = NBAAnalytics._normal_cdf(z_score)
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
        if seed is not None:
            random.seed(seed)

        # Adjust for home court and pace
        home_adj = (home_rating + NBAAnalytics.AVG_HOME_ADVANTAGE) * pace_factor
        away_adj = away_rating * pace_factor

        # Simulate scores (normal distribution)
        home_score = max(0, int(random.gauss(home_adj, 11) + 0.5))
        away_score = max(0, int(random.gauss(away_adj, 11) + 0.5))

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
        under_prob = NBAAnalytics._normal_cdf(z_score)
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
        if seed is not None:
            random.seed(seed)

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'losses': 0, 'pf': 0, 'pa': 0}
                    for team in team_names}

        matches = []
        total_games = (len(team_names) * games_per_team) // 2

        for _ in range(total_games):
            # Random matchup
            home_team = random.choice(team_names)
            away_team = random.choice([t for t in team_names if t != home_team])

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
