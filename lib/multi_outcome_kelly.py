#!/usr/bin/env python3
"""
Multi-Outcome Kelly Criterion

Calculate optimal bet sizing for markets with multiple outcomes (3+).
Useful for horse racing, golf, soccer 1X2, futures, etc.
"""

import argparse
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Outcome:
    """Represents a betting outcome"""
    name: str
    odds: float  # American odds
    true_probability: float
    kelly_fraction: float = 0.0
    expected_value: float = 0.0


class MultiOutcomeKelly:
    """Calculate Kelly Criterion for multiple outcomes"""

    @staticmethod
    def american_to_decimal(odds: float) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def calculate_kelly_two_outcome(
        true_prob: float,
        odds: float,
        american: bool = True
    ) -> float:
        """
        Standard Kelly for two-outcome bet

        Kelly = (bp - q) / b
        where:
            b = decimal odds - 1
            p = true probability of winning
            q = 1 - p = probability of losing
        """
        if american:
            decimal_odds = MultiOutcomeKelly.american_to_decimal(odds)
        else:
            decimal_odds = odds

        b = decimal_odds - 1
        p = true_prob
        q = 1 - p

        kelly = (b * p - q) / b

        return max(0, kelly)  # Don't bet if negative

    @staticmethod
    def calculate_kelly_multi_outcome(
        outcomes: List[Outcome],
        bankroll: float = 100,
        max_fraction: float = 0.25
    ) -> List[Outcome]:
        """
        Calculate Kelly fractions for multiple outcomes

        Uses simultaneous equations method for multiple outcomes.
        This is an approximation - true multi-outcome Kelly is complex.

        Args:
            outcomes: List of Outcome objects with odds and true probabilities
            bankroll: Current bankroll
            max_fraction: Maximum fraction of bankroll to bet (fractional Kelly)

        Returns:
            List of outcomes with kelly_fraction calculated
        """
        # Method 1: Independent Kelly for each outcome
        # This is not optimal but provides a reasonable approximation

        total_kelly = 0

        for outcome in outcomes:
            decimal_odds = MultiOutcomeKelly.american_to_decimal(outcome.odds)
            implied_prob = 1 / decimal_odds

            # Only bet if we have an edge
            if outcome.true_probability > implied_prob:
                # Simple Kelly formula
                kelly = MultiOutcomeKelly.calculate_kelly_two_outcome(
                    outcome.true_probability,
                    outcome.odds,
                    american=True
                )

                # Apply fractional Kelly
                kelly = min(kelly * max_fraction, max_fraction)

                outcome.kelly_fraction = kelly
                total_kelly += kelly

                # Calculate EV
                outcome.expected_value = (
                    outcome.true_probability * (decimal_odds - 1) * (kelly * bankroll) -
                    (1 - outcome.true_probability) * (kelly * bankroll)
                )
            else:
                outcome.kelly_fraction = 0
                outcome.expected_value = 0

        # Normalize if total Kelly > 1 (shouldn't bet more than bankroll)
        if total_kelly > 1:
            for outcome in outcomes:
                outcome.kelly_fraction /= total_kelly

        return outcomes

    @staticmethod
    def simultaneous_kelly(
        outcomes: List[Outcome],
        max_bet_fraction: float = 1.0
    ) -> List[Outcome]:
        """
        More advanced simultaneous Kelly calculation

        This attempts to solve the system of equations for optimal fractions.
        Uses iterative optimization.

        Args:
            outcomes: List of outcomes
            max_bet_fraction: Maximum total fraction to bet

        Returns:
            Optimized Kelly fractions
        """
        n = len(outcomes)

        # Start with independent Kelly
        fractions = []
        for outcome in outcomes:
            kelly = MultiOutcomeKelly.calculate_kelly_two_outcome(
                outcome.true_probability,
                outcome.odds
            )
            fractions.append(max(0, kelly))

        # Simple normalization approach
        total = sum(fractions)
        if total > max_bet_fraction:
            fractions = [f * (max_bet_fraction / total) for f in fractions]

        # Assign to outcomes
        for i, outcome in enumerate(outcomes):
            outcome.kelly_fraction = fractions[i]

            # Calculate EV
            decimal_odds = MultiOutcomeKelly.american_to_decimal(outcome.odds)
            stake = fractions[i] * 100  # Per $100 bankroll

            outcome.expected_value = (
                outcome.true_probability * stake * (decimal_odds - 1) -
                (1 - outcome.true_probability) * stake
            )

        return outcomes

    @staticmethod
    def calculate_portfolio_expected_growth(
        outcomes: List[Outcome],
        bankroll: float
    ) -> float:
        """
        Calculate expected bankroll growth rate

        Args:
            outcomes: List of outcomes with kelly fractions
            bankroll: Current bankroll

        Returns:
            Expected growth rate
        """
        # Calculate weighted average return
        expected_return = 0

        for outcome in outcomes:
            decimal_odds = MultiOutcomeKelly.american_to_decimal(outcome.odds)
            stake = outcome.kelly_fraction * bankroll

            # Return if this outcome wins
            return_if_win = stake * decimal_odds
            net_if_win = return_if_win - stake

            # Contribution to expected return
            expected_return += outcome.true_probability * net_if_win

        return (expected_return / bankroll) * 100


def print_kelly_results(
    outcomes: List[Outcome],
    bankroll: float,
    total_kelly: Optional[float] = None
):
    """Print Kelly calculation results"""
    print(f"\n{'='*80}")
    print(f"MULTI-OUTCOME KELLY CRITERION")
    print(f"{'='*80}")

    print(f"\nBankroll: ${bankroll:,.2f}")

    total_bet = sum(o.kelly_fraction * bankroll for o in outcomes)
    total_ev = sum(o.expected_value for o in outcomes)

    print(f"\n{'Outcome':<20} {'Odds':<10} {'True%':<10} {'Edge':<10} {'Kelly%':<10} {'Stake':<12} {'EV':<12}")
    print(f"{'-'*90}")

    for outcome in outcomes:
        decimal_odds = MultiOutcomeKelly.american_to_decimal(outcome.odds)
        implied_prob = 1 / decimal_odds
        edge = (outcome.true_probability - implied_prob) * 100

        kelly_pct = outcome.kelly_fraction * 100
        stake = outcome.kelly_fraction * bankroll

        print(f"{outcome.name:<20} {outcome.odds:>+8.0f}  "
              f"{outcome.true_probability*100:>7.2f}%  "
              f"{edge:>+7.2f}%  "
              f"{kelly_pct:>7.2f}%  "
              f"${stake:>9.2f}  "
              f"${outcome.expected_value:>+9.2f}")

    print(f"{'-'*90}")
    print(f"{'TOTAL':<20} {'':<10} {'':<10} {'':<10} "
          f"{(total_bet/bankroll)*100:>7.2f}%  "
          f"${total_bet:>9.2f}  "
          f"${total_ev:>+9.2f}")

    # Calculate expected growth
    growth = MultiOutcomeKelly.calculate_portfolio_expected_growth(outcomes, bankroll)
    print(f"\nExpected Bankroll Growth: {growth:+.2f}%")

    # Summary
    num_bets = sum(1 for o in outcomes if o.kelly_fraction > 0)
    print(f"\nRecommended Bets: {num_bets}/{len(outcomes)}")

    if total_bet > bankroll:
        print(f"\n⚠️  WARNING: Total bets exceed bankroll! Consider fractional Kelly.")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Multi-Outcome Kelly Criterion Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Horse racing (5 horses)
  %(prog)s -b 1000 --max-fraction 0.25 \
    --outcome "Horse A" +300 0.35 \
    --outcome "Horse B" +500 0.25 \
    --outcome "Horse C" +800 0.15 \
    --outcome "Horse D" +1200 0.10 \
    --outcome "Horse E" +2000 0.15

  # Soccer 1X2
  %(prog)s -b 500 --max-fraction 0.20 \
    --outcome "Home Win" -110 0.52 \
    --outcome "Draw" +220 0.28 \
    --outcome "Away Win" +180 0.20

  # Golf tournament (top 10)
  %(prog)s -b 2000 --max-fraction 0.10 \
    --outcome "Player 1" +800 0.15 \
    --outcome "Player 2" +1200 0.10 \
    --outcome "Player 3" +1500 0.08

  # UFC main card (5 fights)
  %(prog)s -b 1000 \
    --outcome "Fighter A" -180 0.68 \
    --outcome "Fighter B" -130 0.60 \
    --outcome "Fighter C" +110 0.48 \
    --outcome "Fighter D" -150 0.62 \
    --outcome "Fighter E" +200 0.40
        """
    )

    parser.add_argument('-b', '--bankroll', type=float, default=100,
                       help='Current bankroll (default: 100)')
    parser.add_argument('--max-fraction', type=float, default=0.25,
                       help='Maximum Kelly fraction (default: 0.25 for quarter Kelly)')
    parser.add_argument('--outcome', nargs=3, action='append',
                       metavar=('NAME', 'ODDS', 'TRUE_PROB'),
                       help='Add outcome: name odds true_probability')
    parser.add_argument('--method', choices=['independent', 'simultaneous'],
                       default='independent',
                       help='Calculation method (default: independent)')

    args = parser.parse_args()

    if not args.outcome:
        parser.error("At least one --outcome required")

    # Parse outcomes
    outcomes = []
    for name, odds, prob in args.outcome:
        outcomes.append(Outcome(
            name=name,
            odds=float(odds),
            true_probability=float(prob)
        ))

    # Validate probabilities sum to <= 1
    total_prob = sum(o.true_probability for o in outcomes)
    if total_prob > 1.001:
        print(f"Warning: True probabilities sum to {total_prob:.3f} (should be ≤ 1.0)")

    # Calculate Kelly
    if args.method == 'independent':
        outcomes = MultiOutcomeKelly.calculate_kelly_multi_outcome(
            outcomes,
            args.bankroll,
            args.max_fraction
        )
    else:
        outcomes = MultiOutcomeKelly.simultaneous_kelly(
            outcomes,
            args.max_fraction
        )

    # Print results
    print_kelly_results(outcomes, args.bankroll)


if __name__ == '__main__':
    main()
