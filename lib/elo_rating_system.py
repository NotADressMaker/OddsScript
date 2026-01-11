#!/usr/bin/env python3
"""
Elo Rating System for Sports Betting

Track team strength using the Elo rating system and predict match outcomes.
Originally developed for chess, adapted for sports with home advantage and
margin of victory adjustments.
"""

import argparse
import csv
import json
import math
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Team:
    """Represents a team with Elo rating"""
    name: str
    rating: float
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0


@dataclass
class Match:
    """Represents a completed match"""
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int


class EloRatingSystem:
    """Elo rating system for sports"""

    # Default parameters
    DEFAULT_RATING = 1500
    DEFAULT_K_FACTOR = 32

    def __init__(
        self,
        k_factor: float = 32,
        home_advantage: float = 100,
        mov_multiplier: bool = True
    ):
        """
        Initialize Elo system

        Args:
            k_factor: K-factor (how much ratings change per game)
            home_advantage: Home field advantage in Elo points
            mov_multiplier: Apply margin of victory multiplier
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.mov_multiplier = mov_multiplier
        self.teams: Dict[str, Team] = {}

    def get_or_create_team(self, name: str) -> Team:
        """Get team or create with default rating"""
        if name not in self.teams:
            self.teams[name] = Team(name=name, rating=self.DEFAULT_RATING)
        return self.teams[name]

    @staticmethod
    def expected_score(rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score using Elo formula

        Args:
            rating_a: Team A's rating
            rating_b: Team B's rating

        Returns:
            Expected score for team A (0-1)
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def calculate_mov_multiplier(
        self,
        score_diff: int,
        winning_rating: float,
        losing_rating: float
    ) -> float:
        """
        Calculate margin of victory multiplier

        Larger wins against stronger opponents = bigger rating change

        Args:
            score_diff: Point difference
            winning_rating: Winner's Elo rating
            losing_rating: Loser's Elo rating

        Returns:
            Multiplier (>= 1.0)
        """
        # Base multiplier from score differential
        if score_diff <= 0:
            return 1.0

        # Logarithmic scaling for MOV
        mov_mult = math.log(abs(score_diff) + 1) * 2.2 / ((winning_rating - losing_rating) * 0.001 + 2.2)

        return max(1.0, mov_mult)

    def update_ratings(
        self,
        home_team_name: str,
        away_team_name: str,
        home_score: int,
        away_score: int
    ) -> Tuple[float, float]:
        """
        Update Elo ratings based on match result

        Args:
            home_team_name: Home team name
            away_team_name: Away team name
            home_score: Home team's score
            away_score: Away team's score

        Returns:
            Tuple of (home_rating_change, away_rating_change)
        """
        home_team = self.get_or_create_team(home_team_name)
        away_team = self.get_or_create_team(away_team_name)

        # Adjust for home advantage
        home_rating_adj = home_team.rating + self.home_advantage
        away_rating_adj = away_team.rating

        # Calculate expected scores
        home_expected = self.expected_score(home_rating_adj, away_rating_adj)
        away_expected = 1 - home_expected

        # Actual scores
        if home_score > away_score:
            home_actual = 1.0
            away_actual = 0.0
        elif home_score < away_score:
            home_actual = 0.0
            away_actual = 1.0
        else:  # Draw
            home_actual = 0.5
            away_actual = 0.5

        # Apply margin of victory multiplier if enabled
        k = self.k_factor
        if self.mov_multiplier and home_score != away_score:
            score_diff = abs(home_score - away_score)
            if home_score > away_score:
                mov_mult = self.calculate_mov_multiplier(score_diff, home_team.rating, away_team.rating)
            else:
                mov_mult = self.calculate_mov_multiplier(score_diff, away_team.rating, home_team.rating)

            k = k * mov_mult

        # Calculate rating changes
        home_change = k * (home_actual - home_expected)
        away_change = k * (away_actual - away_expected)

        # Update ratings
        home_team.rating += home_change
        away_team.rating += away_change

        # Update stats
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

    def predict_match(
        self,
        home_team_name: str,
        away_team_name: str
    ) -> Dict:
        """
        Predict match outcome using current Elo ratings

        Args:
            home_team_name: Home team name
            away_team_name: Away team name

        Returns:
            Prediction dictionary
        """
        home_team = self.get_or_create_team(home_team_name)
        away_team = self.get_or_create_team(away_team_name)

        # Adjust for home advantage
        home_rating_adj = home_team.rating + self.home_advantage
        away_rating_adj = away_team.rating

        # Calculate win probabilities
        home_win_prob = self.expected_score(home_rating_adj, away_rating_adj)
        away_win_prob = 1 - home_win_prob

        # Estimate draw probability (sport-specific, simplified here)
        # For sports without draws, this would be 0
        draw_prob = 0.15 * min(home_win_prob, away_win_prob)  # Rough approximation

        # Adjust win probabilities
        home_win_prob = home_win_prob * (1 - draw_prob)
        away_win_prob = away_win_prob * (1 - draw_prob)

        # Calculate spread (point differential)
        rating_diff = home_rating_adj - away_rating_adj
        spread = rating_diff / 25  # Rough conversion: 25 Elo = 1 point

        return {
            'home_team': home_team_name,
            'away_team': away_team_name,
            'home_rating': home_team.rating,
            'away_rating': away_team.rating,
            'rating_difference': home_team.rating - away_team.rating,
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'predicted_spread': spread,
            'home_advantage_points': self.home_advantage
        }

    def get_rankings(self, top_n: Optional[int] = None) -> List[Team]:
        """
        Get team rankings

        Args:
            top_n: Number of top teams to return (None = all)

        Returns:
            List of teams sorted by rating
        """
        sorted_teams = sorted(
            self.teams.values(),
            key=lambda t: t.rating,
            reverse=True
        )

        if top_n:
            return sorted_teams[:top_n]
        return sorted_teams


def probability_to_american_odds(prob: float) -> float:
    """Convert probability to American odds"""
    if prob >= 0.5:
        return -100 * prob / (1 - prob)
    else:
        return 100 * (1 - prob) / prob


def print_prediction(prediction: Dict):
    """Print match prediction"""
    print(f"\n{'='*80}")
    print(f"ELO MATCH PREDICTION")
    print(f"{'='*80}")

    print(f"\n🏟️  {prediction['home_team']} (Home) vs {prediction['away_team']} (Away)")

    print(f"\n📊 Elo Ratings:")
    print(f"  {prediction['home_team']}: {prediction['home_rating']:.0f}")
    print(f"  {prediction['away_team']}: {prediction['away_rating']:.0f}")
    print(f"  Difference: {prediction['rating_difference']:+.0f}")
    print(f"  Home Advantage: {prediction['home_advantage_points']:.0f} points")

    print(f"\n🎯 Win Probabilities:")
    print(f"  {prediction['home_team']} Win:  {prediction['home_win_prob']*100:>6.2f}%  "
          f"(Odds: {probability_to_american_odds(prediction['home_win_prob']):>+7.0f})")

    if prediction['draw_prob'] > 0.01:
        print(f"  Draw:            {prediction['draw_prob']*100:>6.2f}%  "
              f"(Odds: {probability_to_american_odds(prediction['draw_prob']):>+7.0f})")

    print(f"  {prediction['away_team']} Win:  {prediction['away_win_prob']*100:>6.2f}%  "
          f"(Odds: {probability_to_american_odds(prediction['away_win_prob']):>+7.0f})")

    print(f"\n📏 Predicted Spread: {prediction['predicted_spread']:+.1f}")
    print(f"   (Based on {prediction['predicted_spread']/1:+.1f} points per 25 Elo)")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Elo Rating System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update ratings from match
  %(prog)s update --home "Patriots" --away "Bills" --score 24-17

  # Predict upcoming match
  %(prog)s predict --home "Chiefs" --away "Raiders"

  # Update from CSV file and show rankings
  %(prog)s batch --csv matches.csv --rankings 10

  # Customize K-factor and home advantage
  %(prog)s predict --home "Team A" --away "Team B" -k 40 --home-adv 120

CSV Format for batch mode:
  date,home_team,away_team,home_score,away_score
  2024-01-15,Chiefs,Bills,27,24
  2024-01-16,49ers,Packers,21,14

What is Elo?
  Elo is a rating system that tracks relative skill levels. After each game,
  the winner takes points from the loser. The amount depends on the rating
  difference and the margin of victory.

How to Use for Betting:
  1. Track all games in a league throughout the season
  2. Update Elo ratings after each game
  3. Use ratings to predict future matches
  4. Compare Elo probabilities to bookmaker odds to find value
        """
    )

    parser.add_argument('-k', '--k-factor', type=float, default=32,
                       help='K-factor (default: 32)')
    parser.add_argument('--home-adv', type=float, default=100,
                       help='Home advantage in Elo points (default: 100)')
    parser.add_argument('--no-mov', action='store_true',
                       help='Disable margin of victory adjustment')

    subparsers = parser.add_subparsers(dest='command')

    # Update ratings
    update_parser = subparsers.add_parser('update', help='Update ratings from match')
    update_parser.add_argument('--home', required=True, help='Home team name')
    update_parser.add_argument('--away', required=True, help='Away team name')
    update_parser.add_argument('--score', required=True, help='Score (format: 24-17)')

    # Predict match
    predict_parser = subparsers.add_parser('predict', help='Predict match')
    predict_parser.add_argument('--home', required=True, help='Home team name')
    predict_parser.add_argument('--away', required=True, help='Away team name')

    # Batch process
    batch_parser = subparsers.add_parser('batch', help='Process multiple matches from CSV')
    batch_parser.add_argument('--csv', required=True, help='CSV file with match data')
    batch_parser.add_argument('--rankings', type=int, help='Show top N teams')

    args = parser.parse_args()

    # Initialize Elo system
    elo = EloRatingSystem(
        k_factor=args.k_factor,
        home_advantage=args.home_adv,
        mov_multiplier=not args.no_mov
    )

    if args.command == 'update':
        # Parse score
        try:
            home_score, away_score = map(int, args.score.split('-'))
        except:
            print("Error: Score must be in format '24-17'")
            return

        # Update ratings
        home_change, away_change = elo.update_ratings(
            args.home, args.away, home_score, away_score
        )

        print(f"\n✅ Ratings Updated")
        print(f"\n{args.home}:")
        print(f"  New Rating: {elo.teams[args.home].rating:.0f} ({home_change:+.1f})")
        print(f"  Record: {elo.teams[args.home].wins}-{elo.teams[args.home].losses}")

        print(f"\n{args.away}:")
        print(f"  New Rating: {elo.teams[args.away].rating:.0f} ({away_change:+.1f})")
        print(f"  Record: {elo.teams[args.away].wins}-{elo.teams[args.away].losses}")

    elif args.command == 'predict':
        prediction = elo.predict_match(args.home, args.away)
        print_prediction(prediction)

    elif args.command == 'batch':
        # Load matches from CSV
        with open(args.csv, 'r') as f:
            reader = csv.DictReader(f)
            matches_processed = 0

            for row in reader:
                elo.update_ratings(
                    row['home_team'],
                    row['away_team'],
                    int(row['home_score']),
                    int(row['away_score'])
                )
                matches_processed += 1

        print(f"\n✅ Processed {matches_processed} matches")

        if args.rankings:
            rankings = elo.get_rankings(args.rankings)

            print(f"\n🏆 TOP {args.rankings} TEAMS")
            print(f"\n{'Rank':<6} {'Team':<25} {'Rating':<10} {'Record':<15}")
            print(f"{'-'*60}")

            for i, team in enumerate(rankings, 1):
                record = f"{team.wins}-{team.losses}"
                if team.draws > 0:
                    record += f"-{team.draws}"

                print(f"{i:<6} {team.name:<25} {team.rating:<10.0f} {record:<15}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
