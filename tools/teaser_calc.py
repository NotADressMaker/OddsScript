#!/usr/bin/env python3
"""
Teaser Calculator for NFL and NBA

Calculate teaser odds and payouts for point adjustments.
"""

import argparse
from typing import List, Tuple


class TeaserCalculator:
    """Calculate teaser odds and payouts"""

    # Standard teaser point adjustments and odds
    NFL_TEASERS = {
        6: {2: -110, 3: 180, 4: 300, 5: 450, 6: 600},
        6.5: {2: -120, 3: 150, 4: 250, 5: 400, 6: 550},
        7: {2: -130, 3: 120, 4: 200, 5: 350, 6: 500},
    }

    NBA_TEASERS = {
        4: {2: -110, 3: 180, 4: 300, 5: 450},
        4.5: {2: -120, 3: 150, 4: 250, 5: 400},
        5: {2: -130, 3: 120, 4: 200, 5: 350},
    }

    def __init__(self, sport: str = 'nfl'):
        """
        Initialize teaser calculator

        Args:
            sport: 'nfl' or 'nba'
        """
        self.sport = sport.lower()
        self.teaser_odds = self.NFL_TEASERS if self.sport == 'nfl' else self.NBA_TEASERS

    def available_teasers(self) -> List[float]:
        """Get available teaser points for this sport"""
        return list(self.teaser_odds.keys())

    def get_odds(self, points: float, num_teams: int) -> int:
        """
        Get odds for a teaser

        Args:
            points: Teaser points (e.g., 6, 6.5, 7)
            num_teams: Number of teams in teaser

        Returns:
            American odds
        """
        if points not in self.teaser_odds:
            raise ValueError(f"Invalid teaser points: {points}. "
                           f"Available: {self.available_teasers()}")

        if num_teams not in self.teaser_odds[points]:
            raise ValueError(f"Invalid number of teams: {num_teams}. "
                           f"Available: {list(self.teaser_odds[points].keys())}")

        return self.teaser_odds[points][num_teams]

    def calculate_new_line(self, original_line: float, points: float, teasing_favorite: bool) -> float:
        """
        Calculate new line after teaser adjustment

        Args:
            original_line: Original point spread
            points: Teaser points
            teasing_favorite: True if teasing the favorite

        Returns:
            New line
        """
        if teasing_favorite:
            # Teasing favorite: add points to favorite (make it easier to cover)
            # If favorite is -7, teasing by 6 makes it -1
            return original_line + points
        else:
            # Teasing underdog: subtract points (move line in your favor)
            # If underdog is +3, teasing by 6 makes it +9
            return original_line + points

    def calculate_payout(self, stake: float, points: float, num_teams: int) -> Tuple[float, float]:
        """
        Calculate teaser payout

        Args:
            stake: Amount wagered
            points: Teaser points
            num_teams: Number of teams

        Returns:
            (profit, total_return)
        """
        odds = self.get_odds(points, num_teams)

        if odds > 0:
            profit = stake * (odds / 100)
        else:
            profit = stake * (100 / abs(odds))

        return profit, stake + profit

    def is_wong_teaser(self, lines: List[float], points: float = 6) -> bool:
        """
        Check if this is a Wong teaser (NFL only)

        Wong teasers cross key numbers (3 and 7) for +EV
        Valid Wong teaser: tease through 3 and/or 7

        Args:
            lines: Original lines (positive for underdog, negative for favorite)
            points: Teaser points

        Returns:
            True if valid Wong teaser
        """
        if self.sport != 'nfl':
            return False

        key_numbers = {3, 7}
        crosses_key = False

        for line in lines:
            original = abs(line)
            new = original + points

            # Check if we cross 3 or 7
            for key in key_numbers:
                if original < key < new or original > key > new:
                    crosses_key = True
                    break

        return crosses_key

    def analyze_teaser(self, legs: List[Tuple[str, float]], points: float, stake: float = 100):
        """
        Analyze a teaser bet

        Args:
            legs: List of (team_name, original_line) tuples
            points: Teaser points
            stake: Stake amount
        """
        num_teams = len(legs)

        print(f"\n{'='*60}")
        print(f"{self.sport.upper()} {points}-point Teaser ({num_teams} teams)")
        print(f"{'='*60}")

        print(f"\nOriginal Lines → Teased Lines:")
        for team, line in legs:
            is_favorite = line < 0
            if is_favorite:
                new_line = line + points
                print(f"  {team:20s} {line:+6.1f} → {new_line:+6.1f}")
            else:
                new_line = line + points
                print(f"  {team:20s} {line:+6.1f} → {new_line:+6.1f}")

        # Get odds and payout
        try:
            odds = self.get_odds(points, num_teams)
            profit, total_return = self.calculate_payout(stake, points, num_teams)

            print(f"\nTeaser Odds: {odds:+d}")
            print(f"Stake: ${stake:.2f}")
            print(f"Potential Profit: ${profit:.2f}")
            print(f"Total Return: ${total_return:.2f}")

            # Calculate break-even
            if odds > 0:
                implied_prob = 100 / (odds + 100)
            else:
                implied_prob = abs(odds) / (abs(odds) + 100)

            prob_per_leg = implied_prob ** (1/num_teams)

            print(f"\nImplied Probability: {implied_prob*100:.2f}%")
            print(f"Per-Leg Break-Even: {prob_per_leg*100:.2f}%")

            # Wong teaser check
            if self.sport == 'nfl' and points == 6:
                original_lines = [line for _, line in legs]
                is_wong = self.is_wong_teaser(original_lines, points)
                if is_wong:
                    print(f"\n✓ This is a Wong Teaser (crosses key numbers 3 and/or 7)")
                    print(f"  Wong teasers have historically shown +EV")
                else:
                    print(f"\n✗ Not a Wong Teaser (doesn't cross key numbers)")

        except ValueError as e:
            print(f"\nError: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Teaser Calculator for NFL and NBA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # NFL 6-point, 2-team teaser
  %(prog)s nfl 6 -l "Chiefs" -7 -l "Bills" -3 -s 100

  # NBA 4.5-point, 3-team teaser
  %(prog)s nba 4.5 -l "Lakers" -5.5 -l "Celtics" -4 -l "Warriors" -6.5 -s 50

  # Check Wong teaser
  %(prog)s nfl 6 -l "Team1" -8.5 -l "Team2" -2.5 --wong
        """
    )

    parser.add_argument('sport', choices=['nfl', 'nba'], help='Sport type')
    parser.add_argument('points', type=float, help='Teaser points (e.g., 6, 6.5, 7)')
    parser.add_argument('-l', '--leg', action='append', nargs=2, metavar=('TEAM', 'LINE'),
                       required=True, help='Add a leg (team name and line)')
    parser.add_argument('-s', '--stake', type=float, default=100, help='Stake amount')
    parser.add_argument('--wong', action='store_true', help='Check if Wong teaser (NFL only)')
    parser.add_argument('--list', action='store_true', help='List available teasers')

    args = parser.parse_args()

    calc = TeaserCalculator(args.sport)

    if args.list:
        print(f"\nAvailable {args.sport.upper()} Teasers:")
        for points in calc.available_teasers():
            print(f"\n  {points}-point teaser:")
            for num_teams, odds in calc.teaser_odds[points].items():
                print(f"    {num_teams} teams: {odds:+d}")
        return

    # Parse legs
    legs = []
    for team, line in args.leg:
        legs.append((team, float(line)))

    # Analyze teaser
    calc.analyze_teaser(legs, args.points, args.stake)


if __name__ == '__main__':
    main()
