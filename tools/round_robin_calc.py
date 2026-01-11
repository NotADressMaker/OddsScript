#!/usr/bin/env python3
"""
Round Robin Parlay Calculator

Calculate all possible parlay combinations for round robin bets.
"""

import argparse
from itertools import combinations
from typing import List, Tuple


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal"""
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


def calculate_parlay_odds(odds_list: List[float]) -> float:
    """Calculate parlay odds from multiple legs"""
    decimal_odds = [american_to_decimal(o) for o in odds_list]
    combined = 1
    for odd in decimal_odds:
        combined *= odd

    # Convert back to American
    if combined >= 2.0:
        return (combined - 1) * 100
    else:
        return -100 / (combined - 1)


def calculate_payout(stake: float, odds: float) -> Tuple[float, float]:
    """Calculate profit and total return"""
    if odds > 0:
        profit = stake * (odds / 100)
    else:
        profit = stake * (100 / abs(odds))
    return profit, stake + profit


class RoundRobinCalculator:
    """Calculate round robin parlays"""

    def __init__(self, selections: List[Tuple[str, float]]):
        """
        Initialize calculator

        Args:
            selections: List of (team_name, odds) tuples
        """
        self.selections = selections
        self.num_selections = len(selections)

    def get_combinations(self, parlay_size: int) -> List[List[Tuple[str, float]]]:
        """
        Get all combinations for a given parlay size

        Args:
            parlay_size: Number of teams per parlay (2, 3, 4, etc.)

        Returns:
            List of parlay combinations
        """
        if parlay_size < 2:
            raise ValueError("Parlay size must be at least 2")
        if parlay_size > self.num_selections:
            raise ValueError(f"Parlay size cannot exceed {self.num_selections} selections")

        combos = list(combinations(self.selections, parlay_size))
        return [list(combo) for combo in combos]

    def calculate_round_robin(
        self,
        parlay_sizes: List[int],
        stake_per_parlay: float
    ) -> dict:
        """
        Calculate full round robin

        Args:
            parlay_sizes: List of parlay sizes to include (e.g., [2, 3] for 2s and 3s)
            stake_per_parlay: Stake amount per individual parlay

        Returns:
            Dictionary with round robin details
        """
        all_parlays = []
        total_parlays = 0
        total_stake = 0

        for size in parlay_sizes:
            combos = self.get_combinations(size)
            total_parlays += len(combos)

            for combo in combos:
                # Extract odds
                odds_list = [odds for _, odds in combo]
                parlay_odds = calculate_parlay_odds(odds_list)
                profit, total_return = calculate_payout(stake_per_parlay, parlay_odds)

                all_parlays.append({
                    'size': size,
                    'teams': [name for name, _ in combo],
                    'odds': odds_list,
                    'parlay_odds': parlay_odds,
                    'stake': stake_per_parlay,
                    'profit': profit,
                    'return': total_return
                })

        total_stake = total_parlays * stake_per_parlay

        return {
            'num_selections': self.num_selections,
            'parlay_sizes': parlay_sizes,
            'total_parlays': total_parlays,
            'stake_per_parlay': stake_per_parlay,
            'total_stake': total_stake,
            'parlays': all_parlays
        }

    def calculate_scenarios(
        self,
        parlay_sizes: List[int],
        stake_per_parlay: float,
        wins: int
    ) -> dict:
        """
        Calculate potential returns based on number of wins

        Args:
            parlay_sizes: Parlay sizes included
            stake_per_parlay: Stake per parlay
            wins: Number of selections that win

        Returns:
            Payout scenarios
        """
        if wins > self.num_selections:
            wins = self.num_selections

        rr = self.calculate_round_robin(parlay_sizes, stake_per_parlay)

        # Determine which selections won (simplified - just take first N)
        winning_selections = set(range(wins))

        total_profit = 0
        winning_parlays = 0

        for parlay in rr['parlays']:
            # Check if all teams in this parlay are winners
            parlay_indices = []
            for team_name in parlay['teams']:
                for i, (name, _) in enumerate(self.selections):
                    if name == team_name:
                        parlay_indices.append(i)
                        break

            if all(idx in winning_selections for idx in parlay_indices):
                # This parlay won
                total_profit += parlay['profit']
                winning_parlays += 1
            else:
                # This parlay lost
                total_profit -= parlay['stake']

        net_profit = total_profit

        return {
            'wins': wins,
            'losses': self.num_selections - wins,
            'winning_parlays': winning_parlays,
            'losing_parlays': rr['total_parlays'] - winning_parlays,
            'total_stake': rr['total_stake'],
            'gross_profit': total_profit + rr['total_stake'] if total_profit > 0 else 0,
            'net_profit': net_profit,
            'roi': (net_profit / rr['total_stake']) * 100 if rr['total_stake'] > 0 else 0
        }

    def print_summary(self, parlay_sizes: List[int], stake_per_parlay: float):
        """Print round robin summary"""
        rr = self.calculate_round_robin(parlay_sizes, stake_per_parlay)

        print(f"\n{'='*70}")
        print(f"Round Robin Calculator")
        print(f"{'='*70}")

        print(f"\nSelections ({self.num_selections}):")
        for i, (name, odds) in enumerate(self.selections, 1):
            print(f"  {i}. {name:20s} {odds:+7.0f}")

        print(f"\nRound Robin Configuration:")
        print(f"  Parlay Sizes: {parlay_sizes}")
        print(f"  Total Parlays: {rr['total_parlays']}")
        print(f"  Stake Per Parlay: ${stake_per_parlay:.2f}")
        print(f"  Total Risk: ${rr['total_stake']:.2f}")

        # Break down by parlay size
        print(f"\nParlay Breakdown:")
        for size in parlay_sizes:
            count = sum(1 for p in rr['parlays'] if p['size'] == size)
            print(f"  {size}-team parlays: {count}")

        # Show first few parlays as examples
        print(f"\nExample Parlays:")
        for i, parlay in enumerate(rr['parlays'][:5], 1):
            teams_str = " + ".join(parlay['teams'])
            print(f"  {i}. {teams_str}")
            print(f"     Odds: {parlay['parlay_odds']:+.0f} | "
                  f"Stake: ${parlay['stake']:.2f} | "
                  f"To Win: ${parlay['profit']:.2f}")

        if len(rr['parlays']) > 5:
            print(f"  ... and {len(rr['parlays']) - 5} more parlays")

        # Show scenarios
        print(f"\n{'='*70}")
        print(f"Payout Scenarios")
        print(f"{'='*70}")
        print(f"{'Wins':<6} {'Win Parlays':<12} {'Net Profit':<15} {'ROI':<10}")
        print(f"{'-'*70}")

        for wins in range(self.num_selections + 1):
            scenario = self.calculate_scenarios(parlay_sizes, stake_per_parlay, wins)
            print(f"{scenario['wins']:<6} "
                  f"{scenario['winning_parlays']}/{rr['total_parlays']:<11} "
                  f"${scenario['net_profit']:>+12.2f}  "
                  f"{scenario['roi']:>+8.2f}%")


def main():
    parser = argparse.ArgumentParser(
        description='Round Robin Parlay Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 4-team round robin, 2s and 3s, $10 per parlay
  %(prog)s -l Chiefs -110 -l Bills -120 -l Ravens +150 -l Bengals -105 \\
           --sizes 2 3 --stake 10

  # 5-team round robin, just 2-teamers
  %(prog)s -l T1 -110 -l T2 -110 -l T3 -110 -l T4 -110 -l T5 -110 \\
           --sizes 2 --stake 20
        """
    )

    parser.add_argument('-l', '--leg', action='append', nargs=2,
                       metavar=('TEAM', 'ODDS'), required=True,
                       help='Add a selection (team and odds)')
    parser.add_argument('--sizes', type=int, nargs='+', required=True,
                       help='Parlay sizes to include (e.g., 2 3 4)')
    parser.add_argument('-s', '--stake', type=float, default=10,
                       help='Stake per parlay')

    args = parser.parse_args()

    # Parse selections
    selections = []
    for team, odds in args.leg:
        selections.append((team, float(odds)))

    # Validate
    if len(selections) < 2:
        print("Error: Need at least 2 selections for round robin")
        return

    for size in args.sizes:
        if size > len(selections):
            print(f"Error: Cannot create {size}-team parlays with only {len(selections)} selections")
            return

    # Calculate and display
    calc = RoundRobinCalculator(selections)
    calc.print_summary(args.sizes, args.stake)


if __name__ == '__main__':
    main()
