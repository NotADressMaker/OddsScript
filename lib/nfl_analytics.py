#!/usr/bin/env python3
"""
NFL Analytics Library

Statistical models and betting tools specifically designed for NFL (American Football).
Includes point spread analysis, totals modeling, and NFL-specific betting calculations.
"""

import math
import random
from typing import Dict, List, Tuple, Optional


class NFLAnalytics:
    """NFL-specific betting analytics and simulations"""

    # NFL key numbers (most common winning margins)
    KEY_NUMBERS = {
        3: 0.145,   # Field goal - most common margin
        7: 0.095,   # Touchdown
        10: 0.062,  # FG + TD
        14: 0.043,  # 2 TDs
        4: 0.041,   # TD + missed XP
        6: 0.039,   # 2 FGs
        1: 0.033,   # Last second FG/Safety
        2: 0.026,   # Safety
        17: 0.025,  # FG + 2 TDs
        21: 0.022   # 3 TDs
    }

    # Average NFL statistics (2023 season)
    AVG_POINTS_PER_GAME = 22.8
    AVG_HOME_ADVANTAGE = 2.5
    AVG_TOTAL_POINTS = 45.6

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
            team_rating: Team power rating (e.g., Elo, point differential)
            opponent_rating: Opponent power rating
            spread: Point spread (negative means team is favorite)
            is_home: Whether team is playing at home

        Returns:
            Dictionary with cover probability and analysis
        """
        # Adjust for home field advantage
        home_adj = NFLAnalytics.AVG_HOME_ADVANTAGE if is_home else -NFLAnalytics.AVG_HOME_ADVANTAGE

        # Expected point differential
        expected_diff = (team_rating - opponent_rating) + home_adj

        # Adjusted differential accounting for spread
        adjusted_diff = expected_diff - spread

        # Use normal distribution (NFL scoring approximates normal)
        # Standard deviation for NFL games ~13.5 points
        std_dev = 13.5

        # Calculate z-score
        z_score = adjusted_diff / std_dev

        # Convert to probability using cumulative normal distribution
        cover_prob = NFLAnalytics._normal_cdf(z_score)

        # Push probability (for key numbers)
        push_prob = 0.0
        if abs(spread) in NFLAnalytics.KEY_NUMBERS:
            push_prob = NFLAnalytics.KEY_NUMBERS[abs(spread)] * 0.5  # Approximate

        return {
            'cover_probability': cover_prob * (1 - push_prob),
            'push_probability': push_prob,
            'lose_probability': (1 - cover_prob) * (1 - push_prob),
            'expected_margin': expected_diff,
            'spread': spread,
            'is_key_number': abs(spread) in NFLAnalytics.KEY_NUMBERS
        }

    @staticmethod
    def calculate_total_probability(
        team1_avg: float,
        team2_avg: float,
        total_line: float,
        pace_factor: float = 1.0
    ) -> Dict:
        """
        Calculate over/under probability for game total

        Args:
            team1_avg: Team 1 average points per game
            team2_avg: Team 2 average points per game
            total_line: Over/under line
            pace_factor: Game pace adjustment (1.0 = normal)

        Returns:
            Dictionary with over/under probabilities
        """
        # Expected total
        expected_total = (team1_avg + team2_avg) * pace_factor

        # Standard deviation for total points ~13 points
        std_dev = 13.0

        # Calculate z-score for over
        z_score = (total_line - expected_total) / std_dev

        # Under probability = CDF(z)
        under_prob = NFLAnalytics._normal_cdf(z_score)
        over_prob = 1 - under_prob

        return {
            'over_probability': over_prob,
            'under_probability': under_prob,
            'expected_total': expected_total,
            'line': total_line,
            'difference': expected_total - total_line
        }

    @staticmethod
    def simulate_game(
        home_rating: float,
        away_rating: float,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate a single NFL game

        Args:
            home_rating: Home team rating (average points)
            away_rating: Away team rating (average points)
            seed: Random seed for reproducibility

        Returns:
            Dictionary with game result
        """
        if seed is not None:
            random.seed(seed)

        # Add home field advantage
        home_adj = home_rating + NFLAnalytics.AVG_HOME_ADVANTAGE
        away_adj = away_rating

        # Simulate scores using normal distribution
        # NFL scoring roughly follows normal distribution
        home_score = max(0, int(random.gauss(home_adj, 10) + 0.5))
        away_score = max(0, int(random.gauss(away_adj, 10) + 0.5))

        margin = home_score - away_score
        total = home_score + away_score

        if margin > 0:
            result = 'home_win'
        elif margin < 0:
            result = 'away_win'
        else:
            result = 'tie'  # Rare in NFL but possible

        return {
            'home_score': home_score,
            'away_score': away_score,
            'margin': margin,
            'total': total,
            'result': result,
            'is_key_number': abs(margin) in NFLAnalytics.KEY_NUMBERS
        }

    @staticmethod
    def simulate_season(
        teams: Dict[str, float],
        games_per_team: int = 17,
        seed: Optional[int] = None
    ) -> Dict:
        """
        Simulate an NFL season

        Args:
            teams: Dictionary of team names to ratings
            games_per_team: Games per team (NFL = 17)
            seed: Random seed

        Returns:
            Season results with standings
        """
        if seed is not None:
            random.seed(seed)

        team_names = list(teams.keys())
        standings = {team: {'wins': 0, 'losses': 0, 'ties': 0, 'pf': 0, 'pa': 0}
                    for team in team_names}

        matches = []
        total_games = (len(team_names) * games_per_team) // 2

        for _ in range(total_games):
            # Random matchup
            home_team = random.choice(team_names)
            away_team = random.choice([t for t in team_names if t != home_team])

            # Simulate game
            game = NFLAnalytics.simulate_game(teams[home_team], teams[away_team])

            # Update standings
            standings[home_team]['pf'] += game['home_score']
            standings[home_team]['pa'] += game['away_score']
            standings[away_team]['pf'] += game['away_score']
            standings[away_team]['pa'] += game['home_score']

            if game['result'] == 'home_win':
                standings[home_team]['wins'] += 1
                standings[away_team]['losses'] += 1
            elif game['result'] == 'away_win':
                standings[away_team]['wins'] += 1
                standings[home_team]['losses'] += 1
            else:
                standings[home_team]['ties'] += 1
                standings[away_team]['ties'] += 1

            matches.append({
                'home': home_team,
                'away': away_team,
                'home_score': game['home_score'],
                'away_score': game['away_score'],
                'margin': game['margin']
            })

        # Calculate winning percentage
        for team in standings:
            games = standings[team]['wins'] + standings[team]['losses'] + standings[team]['ties']
            if games > 0:
                standings[team]['win_pct'] = (standings[team]['wins'] + 0.5 * standings[team]['ties']) / games
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
    def analyze_key_numbers(spread: float) -> Dict:
        """
        Analyze the importance of key numbers for a given spread

        Args:
            spread: Point spread to analyze

        Returns:
            Analysis of key number proximity and impact
        """
        spread_val = abs(spread)

        # Find nearest key numbers
        key_nums = sorted(NFLAnalytics.KEY_NUMBERS.keys())
        nearest_below = max([k for k in key_nums if k <= spread_val], default=0)
        nearest_above = min([k for k in key_nums if k >= spread_val], default=max(key_nums))

        is_key = spread_val in NFLAnalytics.KEY_NUMBERS
        frequency = NFLAnalytics.KEY_NUMBERS.get(spread_val, 0.0)

        return {
            'is_key_number': is_key,
            'spread': spread,
            'frequency': frequency,
            'nearest_key_below': nearest_below,
            'nearest_key_above': nearest_above,
            'advice': NFLAnalytics._get_key_number_advice(spread_val)
        }

    @staticmethod
    def _get_key_number_advice(spread: float) -> str:
        """Get betting advice based on key numbers"""
        if spread in [3, 7]:
            return "CRITICAL KEY NUMBER - Shop for best line, 0.5 point matters significantly"
        elif spread in [10, 14, 4, 6]:
            return "Important key number - Line shopping recommended"
        elif abs(spread - 3) <= 0.5 or abs(spread - 7) <= 0.5:
            return "Near critical key number - Be cautious"
        else:
            return "Not a key number - Standard spread"

    @staticmethod
    def _normal_cdf(z: float) -> float:
        """
        Cumulative distribution function for standard normal distribution
        Using error function approximation
        """
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def calculate_nfl_elo_probability(elo1: float, elo2: float, home_advantage: float = 65) -> float:
    """
    Calculate win probability based on Elo ratings

    Args:
        elo1: Team 1 Elo rating
        elo2: Team 2 Elo rating
        home_advantage: Elo points for home field (default 65)

    Returns:
        Probability of team 1 winning
    """
    elo_diff = elo1 + home_advantage - elo2
    return 1 / (1 + 10 ** (-elo_diff / 400))


if __name__ == '__main__':
    # Example usage
    print("NFL Analytics Library")
    print("=" * 70)

    # Example 1: Spread analysis
    print("\nExample 1: Spread Analysis")
    result = NFLAnalytics.calculate_spread_probability(
        team_rating=24.5,
        opponent_rating=20.0,
        spread=-3.5,
        is_home=True
    )
    print(f"Cover Probability: {result['cover_probability']*100:.1f}%")
    print(f"Expected Margin: {result['expected_margin']:.1f}")

    # Example 2: Total analysis
    print("\nExample 2: Total Analysis")
    total = NFLAnalytics.calculate_total_probability(
        team1_avg=25.5,
        team2_avg=22.3,
        total_line=47.5
    )
    print(f"Over Probability: {total['over_probability']*100:.1f}%")
    print(f"Expected Total: {total['expected_total']:.1f}")

    # Example 3: Key numbers
    print("\nExample 3: Key Number Analysis")
    key_analysis = NFLAnalytics.analyze_key_numbers(-3.0)
    print(f"Spread: {key_analysis['spread']}")
    print(f"Is Key Number: {key_analysis['is_key_number']}")
    print(f"Advice: {key_analysis['advice']}")
