#!/usr/bin/env python3
"""
Dutch Betting Calculator

Dutch betting (or "Dutching") allows you to bet on multiple outcomes in the same
market to guarantee equal profit regardless of which outcome wins.

Named after gangster Dutch Schultz who used this technique at racetracks.
"""

import argparse
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class DutchOutcome:
    """Represents an outcome in a Dutch bet"""
    name: str
    odds: float  # American odds
    stake: float = 0.0
    payout: float = 0.0
    profit: float = 0.0


class DutchCalculator:
    """Calculate Dutch betting stakes"""

    @staticmethod
    def american_to_decimal(odds: float) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def calculate_dutch_equal_profit(
        outcomes: List[DutchOutcome],
        total_stake: float
    ) -> List[DutchOutcome]:
        """
        Calculate stakes for equal profit on all outcomes

        Args:
            outcomes: List of DutchOutcome objects with odds
            total_stake: Total amount to bet across all outcomes

        Returns:
            Updated outcomes with calculated stakes
        """
        # Convert to decimal odds
        decimal_odds = [DutchCalculator.american_to_decimal(o.odds) for o in outcomes]

        # Calculate implied probabilities
        implied_probs = [1 / d for d in decimal_odds]
        total_prob = sum(implied_probs)

        # Check if Dutch is profitable
        is_profitable = total_prob < 1

        # Calculate stakes proportional to implied probability
        for i, outcome in enumerate(outcomes):
            outcome.stake = (implied_probs[i] / total_prob) * total_stake
            outcome.payout = outcome.stake * decimal_odds[i]
            outcome.profit = outcome.payout - total_stake

        return outcomes

    @staticmethod
    def calculate_dutch_target_profit(
        outcomes: List[DutchOutcome],
        target_profit: float
    ) -> Tuple[List[DutchOutcome], float]:
        """
        Calculate stakes to achieve a target profit

        Args:
            outcomes: List of DutchOutcome objects with odds
            target_profit: Desired profit amount

        Returns:
            Tuple of (updated outcomes, total stake required)
        """
        decimal_odds = [DutchCalculator.american_to_decimal(o.odds) for o in outcomes]
        implied_probs = [1 / d for d in decimal_odds]
        total_prob = sum(implied_probs)

        # Calculate required total stake
        # If outcome i wins: stake_i * decimal_odds_i - total_stake = target_profit
        # We need: stake_i * decimal_odds_i = total_stake + target_profit
        # For equal profit: stake_i = (total_stake + target_profit) / decimal_odds_i
        # Sum of all stakes = total_stake
        # So: sum((total_stake + target_profit) / decimal_odds_i) = total_stake
        # total_stake * sum(1/decimal_odds_i) + target_profit * sum(1/decimal_odds_i) = total_stake
        # total_stake * (total_prob - 1) = -target_profit * total_prob
        # total_stake = target_profit * total_prob / (1 - total_prob)

        if total_prob >= 1:
            # Not profitable
            total_stake = target_profit * total_prob / (total_prob - 1)  # Will be negative
        else:
            total_stake = target_profit * total_prob / (1 - total_prob)

        # Calculate individual stakes
        for i, outcome in enumerate(outcomes):
            outcome.stake = (total_stake + target_profit) / decimal_odds[i]
            outcome.payout = outcome.stake * decimal_odds[i]
            outcome.profit = outcome.payout - total_stake

        return outcomes, total_stake

    @staticmethod
    def calculate_dutch_individual_stakes(
        outcomes: List[DutchOutcome],
        stakes: List[float]
    ) -> List[DutchOutcome]:
        """
        Calculate profit for given individual stakes

        Args:
            outcomes: List of DutchOutcome objects
            stakes: List of stake amounts for each outcome

        Returns:
            Updated outcomes with profits
        """
        total_stake = sum(stakes)
        decimal_odds = [DutchCalculator.american_to_decimal(o.odds) for o in outcomes]

        for i, outcome in enumerate(outcomes):
            outcome.stake = stakes[i]
            outcome.payout = stakes[i] * decimal_odds[i]
            outcome.profit = outcome.payout - total_stake

        return outcomes


def print_dutch_results(
    outcomes: List[DutchOutcome],
    total_stake: float,
    method: str = "Equal Profit"
):
    """Print Dutch betting results"""
    print(f"\n{'='*80}")
    print(f"DUTCH BETTING CALCULATOR - {method}")
    print(f"{'='*80}")

    # Calculate metrics
    decimal_odds = [DutchCalculator.american_to_decimal(o.odds) for o in outcomes]
    implied_probs = [1 / d for d in decimal_odds]
    total_prob = sum(implied_probs)

    is_profitable = total_prob < 1
    edge = (1 - total_prob) * 100

    print(f"\nMarket Analysis:")
    print(f"  Total Implied Probability: {total_prob * 100:.2f}%")
    print(f"  Overround/Edge: {edge:+.2f}%")

    if is_profitable:
        print(f"  ✅ PROFITABLE DUTCH - Market has value!")
    else:
        print(f"  ⚠️  UNPROFITABLE - Betting into the vig")

    print(f"\nTotal Stake: ${total_stake:.2f}")

    print(f"\n{'Outcome':<25} {'Odds':<10} {'Stake':<12} {'Payout':<12} {'Profit':<12}")
    print(f"{'-'*80}")

    for outcome in outcomes:
        print(f"{outcome.name:<25} {outcome.odds:>+8.0f}  "
              f"${outcome.stake:>9.2f}  "
              f"${outcome.payout:>9.2f}  "
              f"${outcome.profit:>+9.2f}")

    # Verify all profits are equal (for equal profit method)
    profits = [o.profit for o in outcomes]
    if len(set([round(p, 2) for p in profits])) == 1:
        print(f"\n✓ Guaranteed Profit: ${profits[0]:+.2f} (regardless of outcome)")
        roi = (profits[0] / total_stake) * 100
        print(f"  ROI: {roi:+.2f}%")
    else:
        print(f"\nProfit Range: ${min(profits):+.2f} to ${max(profits):+.2f}")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Dutch Betting Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Horse racing - bet on 3 horses with $100 total
  %(prog)s equal -s 100 \
    --outcome "Horse A" +300 \
    --outcome "Horse B" +500 \
    --outcome "Horse C" +800

  # Soccer - Dutch home and draw to cover against away win
  %(prog)s equal -s 200 \
    --outcome "Home Win" -110 \
    --outcome "Draw" +220

  # Target $50 profit on a race
  %(prog)s target -p 50 \
    --outcome "Option 1" +200 \
    --outcome "Option 2" +300 \
    --outcome "Option 3" +400

  # Custom stakes (calculate profit)
  %(prog)s custom \
    --outcome "Team A" +150 --stake 60 \
    --outcome "Team B" +200 --stake 40

What is Dutching?
  Dutching splits your stake across multiple outcomes to guarantee equal profit
  (or minimize loss) regardless of which outcome wins. It's profitable when the
  combined implied probability is less than 100%.

When to Use:
  - Horse racing (back multiple horses)
  - Soccer (cover 2 of 3 outcomes)
  - Tennis (back multiple players in a tournament)
  - Any market where you like multiple outcomes
        """
    )

    subparsers = parser.add_subparsers(dest='method', help='Dutch method')

    # Equal profit method
    equal_parser = subparsers.add_parser('equal', help='Equal profit on all outcomes')
    equal_parser.add_argument('-s', '--stake', type=float, required=True,
                             help='Total stake across all outcomes')
    equal_parser.add_argument('--outcome', nargs=2, action='append',
                             metavar=('NAME', 'ODDS'),
                             help='Add outcome: name odds (e.g., "Horse A" +300)')

    # Target profit method
    target_parser = subparsers.add_parser('target', help='Target specific profit amount')
    target_parser.add_argument('-p', '--profit', type=float, required=True,
                              help='Target profit amount')
    target_parser.add_argument('--outcome', nargs=2, action='append',
                              metavar=('NAME', 'ODDS'),
                              help='Add outcome: name odds')

    # Custom stakes method
    custom_parser = subparsers.add_parser('custom', help='Custom stakes per outcome')
    custom_parser.add_argument('--outcome', nargs=2, action='append',
                              metavar=('NAME', 'ODDS'),
                              help='Add outcome: name odds')
    custom_parser.add_argument('--stake', nargs=1, action='append', type=float,
                              metavar='AMOUNT',
                              help='Stake for corresponding outcome')

    args = parser.parse_args()

    if not args.method:
        parser.print_help()
        return

    if not args.outcome or len(args.outcome) < 2:
        print("Error: Need at least 2 outcomes for Dutch betting")
        return

    if args.method == 'equal':
        # Parse outcomes
        outcomes = [
            DutchOutcome(name=name, odds=float(odds))
            for name, odds in args.outcome
        ]

        # Calculate
        outcomes = DutchCalculator.calculate_dutch_equal_profit(outcomes, args.stake)

        # Print results
        print_dutch_results(outcomes, args.stake, "Equal Profit")

    elif args.method == 'target':
        # Parse outcomes
        outcomes = [
            DutchOutcome(name=name, odds=float(odds))
            for name, odds in args.outcome
        ]

        # Calculate
        outcomes, total_stake = DutchCalculator.calculate_dutch_target_profit(
            outcomes, args.profit
        )

        # Print results
        print_dutch_results(outcomes, total_stake, f"Target Profit: ${args.profit:.2f}")

    elif args.method == 'custom':
        if not args.stake or len(args.stake) != len(args.outcome):
            print("Error: Must provide --stake for each --outcome")
            return

        # Parse outcomes
        outcomes = [
            DutchOutcome(name=name, odds=float(odds))
            for name, odds in args.outcome
        ]

        # Parse stakes
        stakes = [s[0] for s in args.stake]

        # Calculate
        outcomes = DutchCalculator.calculate_dutch_individual_stakes(outcomes, stakes)

        # Print results
        total_stake = sum(stakes)
        print_dutch_results(outcomes, total_stake, "Custom Stakes")


if __name__ == '__main__':
    main()
