#!/usr/bin/env python3
"""
Advanced Arbitrage Calculator

Find guaranteed profit opportunities across multiple sportsbooks.
Supports 2-way and 3-way markets.
"""

import argparse
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MarketType(Enum):
    """Types of betting markets"""
    TWO_WAY = "two_way"      # Moneyline, spread, total
    THREE_WAY = "three_way"  # Soccer 1X2, regulation time


@dataclass
class Book:
    """Represents a sportsbook offering"""
    name: str
    odds: float
    outcome: str  # "team1", "team2", "draw", "over", "under", etc.


class ArbitrageCalculator:
    """Calculate arbitrage opportunities"""

    @staticmethod
    def american_to_decimal(odds: float) -> float:
        """Convert American odds to decimal"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def decimal_to_american(odds: float) -> float:
        """Convert decimal odds to American"""
        if odds >= 2.0:
            return (odds - 1) * 100
        else:
            return -100 / (odds - 1)

    @staticmethod
    def implied_probability(odds: float, american: bool = True) -> float:
        """Calculate implied probability from odds"""
        if american:
            decimal_odds = ArbitrageCalculator.american_to_decimal(odds)
        else:
            decimal_odds = odds

        return 1 / decimal_odds

    @staticmethod
    def calculate_two_way_arb(
        odds1: float,
        odds2: float,
        american: bool = True
    ) -> Dict:
        """
        Calculate two-way arbitrage (e.g., over/under, team1/team2)

        Args:
            odds1: Odds for outcome 1
            odds2: Odds for outcome 2
            american: Whether odds are in American format

        Returns:
            Dictionary with arbitrage details
        """
        # Convert to decimal if American
        if american:
            decimal1 = ArbitrageCalculator.american_to_decimal(odds1)
            decimal2 = ArbitrageCalculator.american_to_decimal(odds2)
        else:
            decimal1 = odds1
            decimal2 = odds2

        # Calculate implied probabilities
        prob1 = 1 / decimal1
        prob2 = 1 / decimal2

        # Total probability (should be < 1 for arbitrage)
        total_prob = prob1 + prob2

        # Check for arbitrage
        is_arb = total_prob < 1
        profit_margin = (1 / total_prob - 1) * 100 if total_prob < 1 else 0

        # Calculate stakes for $100 total investment
        total_stake = 100
        stake1 = (prob1 / total_prob) * total_stake
        stake2 = (prob2 / total_prob) * total_stake

        # Calculate guaranteed profit
        profit1 = (stake1 * decimal1) - total_stake
        profit2 = (stake2 * decimal2) - total_stake

        return {
            'is_arbitrage': is_arb,
            'profit_margin': profit_margin,
            'total_probability': total_prob * 100,
            'stakes': {
                'outcome1': stake1,
                'outcome2': stake2,
                'total': total_stake
            },
            'returns': {
                'if_outcome1': stake1 * decimal1,
                'if_outcome2': stake2 * decimal2
            },
            'profit': {
                'guaranteed': profit1,  # Should equal profit2 for true arb
                'per_100': profit1
            },
            'decimal_odds': {
                'outcome1': decimal1,
                'outcome2': decimal2
            }
        }

    @staticmethod
    def calculate_three_way_arb(
        odds1: float,
        odds2: float,
        odds3: float,
        american: bool = True
    ) -> Dict:
        """
        Calculate three-way arbitrage (e.g., soccer 1X2)

        Args:
            odds1: Odds for outcome 1 (e.g., home win)
            odds2: Odds for outcome 2 (e.g., draw)
            odds3: Odds for outcome 3 (e.g., away win)
            american: Whether odds are in American format

        Returns:
            Dictionary with arbitrage details
        """
        # Convert to decimal if American
        if american:
            decimal1 = ArbitrageCalculator.american_to_decimal(odds1)
            decimal2 = ArbitrageCalculator.american_to_decimal(odds2)
            decimal3 = ArbitrageCalculator.american_to_decimal(odds3)
        else:
            decimal1 = odds1
            decimal2 = odds2
            decimal3 = odds3

        # Calculate implied probabilities
        prob1 = 1 / decimal1
        prob2 = 1 / decimal2
        prob3 = 1 / decimal3

        # Total probability
        total_prob = prob1 + prob2 + prob3

        # Check for arbitrage
        is_arb = total_prob < 1
        profit_margin = (1 / total_prob - 1) * 100 if total_prob < 1 else 0

        # Calculate stakes for $100 total investment
        total_stake = 100
        stake1 = (prob1 / total_prob) * total_stake
        stake2 = (prob2 / total_prob) * total_stake
        stake3 = (prob3 / total_prob) * total_stake

        # Calculate returns
        return1 = stake1 * decimal1
        return2 = stake2 * decimal2
        return3 = stake3 * decimal3

        # Guaranteed profit (should be same for all outcomes)
        profit = return1 - total_stake

        return {
            'is_arbitrage': is_arb,
            'profit_margin': profit_margin,
            'total_probability': total_prob * 100,
            'stakes': {
                'outcome1': stake1,
                'outcome2': stake2,
                'outcome3': stake3,
                'total': total_stake
            },
            'returns': {
                'if_outcome1': return1,
                'if_outcome2': return2,
                'if_outcome3': return3
            },
            'profit': {
                'guaranteed': profit,
                'per_100': profit
            },
            'decimal_odds': {
                'outcome1': decimal1,
                'outcome2': decimal2,
                'outcome3': decimal3
            }
        }

    @staticmethod
    def find_best_arb(books: List[Book], market_type: MarketType) -> Optional[Dict]:
        """
        Find best arbitrage opportunity from multiple books

        Args:
            books: List of Book objects with odds from different sportsbooks
            market_type: TWO_WAY or THREE_WAY

        Returns:
            Best arbitrage opportunity or None
        """
        if market_type == MarketType.TWO_WAY:
            # Find best odds for each outcome
            outcomes = set(b.outcome for b in books)
            if len(outcomes) != 2:
                return None

            outcome_list = list(outcomes)
            best_odds = {}

            for outcome in outcomes:
                outcome_books = [b for b in books if b.outcome == outcome]
                best_book = max(outcome_books, key=lambda b: b.odds)
                best_odds[outcome] = best_book

            # Calculate arbitrage
            arb = ArbitrageCalculator.calculate_two_way_arb(
                best_odds[outcome_list[0]].odds,
                best_odds[outcome_list[1]].odds,
                american=True
            )

            arb['best_books'] = {
                outcome_list[0]: best_odds[outcome_list[0]].name,
                outcome_list[1]: best_odds[outcome_list[1]].name
            }
            arb['best_odds'] = {
                outcome_list[0]: best_odds[outcome_list[0]].odds,
                outcome_list[1]: best_odds[outcome_list[1]].odds
            }

            return arb

        elif market_type == MarketType.THREE_WAY:
            # Find best odds for each outcome
            outcomes = set(b.outcome for b in books)
            if len(outcomes) != 3:
                return None

            outcome_list = list(outcomes)
            best_odds = {}

            for outcome in outcomes:
                outcome_books = [b for b in books if b.outcome == outcome]
                best_book = max(outcome_books, key=lambda b: b.odds)
                best_odds[outcome] = best_book

            # Calculate arbitrage
            arb = ArbitrageCalculator.calculate_three_way_arb(
                best_odds[outcome_list[0]].odds,
                best_odds[outcome_list[1]].odds,
                best_odds[outcome_list[2]].odds,
                american=True
            )

            arb['best_books'] = {
                outcome_list[0]: best_odds[outcome_list[0]].name,
                outcome_list[1]: best_odds[outcome_list[1]].name,
                outcome_list[2]: best_odds[outcome_list[2]].name
            }
            arb['best_odds'] = {
                outcome_list[0]: best_odds[outcome_list[0]].odds,
                outcome_list[1]: best_odds[outcome_list[1]].odds,
                outcome_list[2]: best_odds[outcome_list[2]].odds
            }

            return arb

        return None

    @staticmethod
    def calculate_custom_stake_arb(
        odds: List[float],
        total_stake: float,
        american: bool = True
    ) -> Dict:
        """
        Calculate arbitrage with custom total stake

        Args:
            odds: List of odds for each outcome
            total_stake: Total amount to invest
            american: Whether odds are in American format

        Returns:
            Arbitrage calculation with custom stake
        """
        # Convert to decimal
        if american:
            decimal_odds = [ArbitrageCalculator.american_to_decimal(o) for o in odds]
        else:
            decimal_odds = odds

        # Calculate implied probabilities
        probs = [1 / d for d in decimal_odds]
        total_prob = sum(probs)

        # Calculate stakes proportionally
        stakes = [(p / total_prob) * total_stake for p in probs]

        # Calculate returns
        returns = [s * d for s, d in zip(stakes, decimal_odds)]

        # Profit (should be same for all outcomes in true arb)
        profit = returns[0] - total_stake

        is_arb = total_prob < 1
        profit_margin = (1 / total_prob - 1) * 100 if is_arb else 0

        return {
            'is_arbitrage': is_arb,
            'profit_margin': profit_margin,
            'total_stake': total_stake,
            'stakes': stakes,
            'returns': returns,
            'guaranteed_profit': profit if is_arb else 0,
            'roi': (profit / total_stake * 100) if is_arb else 0
        }


def print_arb_result(result: Dict, market_type: MarketType, total_stake: float = 100):
    """Print formatted arbitrage result"""
    print(f"\n{'='*70}")
    print(f"ARBITRAGE OPPORTUNITY ANALYSIS")
    print(f"{'='*70}")

    if result['is_arbitrage']:
        print(f"\n✅ ARBITRAGE FOUND!")
        print(f"   Profit Margin: {result['profit_margin']:.3f}%")
        print(f"   Guaranteed Profit: ${result['profit']['guaranteed']:.2f} per ${total_stake:.0f} invested")
        print(f"   ROI: {result['profit']['per_100']:.2f}%")
    else:
        print(f"\n❌ NO ARBITRAGE")
        print(f"   Total Probability: {result['total_probability']:.2f}%")
        print(f"   (Needs to be < 100% for arbitrage)")
        print(f"   Overround: {result['total_probability'] - 100:.2f}%")

    print(f"\nOdds (Decimal):")
    if market_type == MarketType.TWO_WAY:
        print(f"  Outcome 1: {result['decimal_odds']['outcome1']:.3f}")
        print(f"  Outcome 2: {result['decimal_odds']['outcome2']:.3f}")
    else:
        print(f"  Outcome 1: {result['decimal_odds']['outcome1']:.3f}")
        print(f"  Outcome 2: {result['decimal_odds']['outcome2']:.3f}")
        print(f"  Outcome 3: {result['decimal_odds']['outcome3']:.3f}")

    if 'best_books' in result:
        print(f"\nBest Books:")
        for outcome, book in result['best_books'].items():
            odds = result['best_odds'][outcome]
            print(f"  {outcome}: {book} ({odds:+.0f})")

    print(f"\nStake Distribution (Total: ${total_stake:.2f}):")
    if market_type == MarketType.TWO_WAY:
        print(f"  Outcome 1: ${result['stakes']['outcome1']:.2f}")
        print(f"  Outcome 2: ${result['stakes']['outcome2']:.2f}")
    else:
        print(f"  Outcome 1: ${result['stakes']['outcome1']:.2f}")
        print(f"  Outcome 2: ${result['stakes']['outcome2']:.2f}")
        print(f"  Outcome 3: ${result['stakes']['outcome3']:.2f}")

    print(f"\nReturns:")
    if market_type == MarketType.TWO_WAY:
        print(f"  If Outcome 1: ${result['returns']['if_outcome1']:.2f}")
        print(f"  If Outcome 2: ${result['returns']['if_outcome2']:.2f}")
    else:
        print(f"  If Outcome 1: ${result['returns']['if_outcome1']:.2f}")
        print(f"  If Outcome 2: ${result['returns']['if_outcome2']:.2f}")
        print(f"  If Outcome 3: ${result['returns']['if_outcome3']:.2f}")

    print(f"\n{'='*70}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Arbitrage Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Two-way arbitrage (e.g., Over/Under)
  %(prog)s --two-way -o1 -105 -o2 +100

  # Three-way arbitrage (e.g., Soccer 1X2)
  %(prog)s --three-way -o1 +200 -o2 +250 -o3 -110

  # Multi-book comparison (two-way)
  %(prog)s --multi-book \
    --book FanDuel over -110 \
    --book DraftKings over -108 \
    --book BetMGM under +105 \
    --book Caesars under +100

  # Three-way with custom stake
  %(prog)s --three-way -o1 +180 -o2 +220 -o3 +140 --stake 1000

  # Find arbitrage in real scenario
  %(prog)s --two-way -o1 +105 -o2 -110  # NBA Over/Under
  %(prog)s --three-way -o1 +150 -o2 +200 -o3 +180  # Soccer match
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--two-way', action='store_true',
                           help='Calculate two-way arbitrage')
    mode_group.add_argument('--three-way', action='store_true',
                           help='Calculate three-way arbitrage')
    mode_group.add_argument('--multi-book', action='store_true',
                           help='Find best arbitrage from multiple books')

    # Odds arguments
    parser.add_argument('-o1', '--odds1', type=float,
                       help='Odds for outcome 1 (American format)')
    parser.add_argument('-o2', '--odds2', type=float,
                       help='Odds for outcome 2 (American format)')
    parser.add_argument('-o3', '--odds3', type=float,
                       help='Odds for outcome 3 (American format, three-way only)')

    # Multi-book mode
    parser.add_argument('--book', nargs=3, action='append',
                       metavar=('NAME', 'OUTCOME', 'ODDS'),
                       help='Add book odds: name outcome odds (e.g., FanDuel over -110)')

    # Custom stake
    parser.add_argument('-s', '--stake', type=float, default=100,
                       help='Total stake amount (default: 100)')

    # Market type for multi-book
    parser.add_argument('--market', choices=['two', 'three'], default='two',
                       help='Market type for multi-book mode (default: two)')

    args = parser.parse_args()

    calc = ArbitrageCalculator()

    if args.two_way:
        if not args.odds1 or not args.odds2:
            parser.error("--two-way requires -o1 and -o2")

        result = calc.calculate_two_way_arb(args.odds1, args.odds2, american=True)

        # Adjust for custom stake
        if args.stake != 100:
            stake_ratio = args.stake / 100
            result['stakes']['outcome1'] *= stake_ratio
            result['stakes']['outcome2'] *= stake_ratio
            result['stakes']['total'] = args.stake
            result['returns']['if_outcome1'] *= stake_ratio
            result['returns']['if_outcome2'] *= stake_ratio
            result['profit']['guaranteed'] *= stake_ratio
            result['profit']['per_100'] = (result['profit']['guaranteed'] / args.stake) * 100

        print_arb_result(result, MarketType.TWO_WAY, args.stake)

    elif args.three_way:
        if not args.odds1 or not args.odds2 or not args.odds3:
            parser.error("--three-way requires -o1, -o2, and -o3")

        result = calc.calculate_three_way_arb(
            args.odds1, args.odds2, args.odds3, american=True
        )

        # Adjust for custom stake
        if args.stake != 100:
            stake_ratio = args.stake / 100
            result['stakes']['outcome1'] *= stake_ratio
            result['stakes']['outcome2'] *= stake_ratio
            result['stakes']['outcome3'] *= stake_ratio
            result['stakes']['total'] = args.stake
            result['returns']['if_outcome1'] *= stake_ratio
            result['returns']['if_outcome2'] *= stake_ratio
            result['returns']['if_outcome3'] *= stake_ratio
            result['profit']['guaranteed'] *= stake_ratio
            result['profit']['per_100'] = (result['profit']['guaranteed'] / args.stake) * 100

        print_arb_result(result, MarketType.THREE_WAY, args.stake)

    elif args.multi_book:
        if not args.book:
            parser.error("--multi-book requires at least one --book argument")

        # Parse book data
        books = []
        for book_data in args.book:
            name, outcome, odds = book_data
            books.append(Book(name=name, outcome=outcome, odds=float(odds)))

        # Determine market type
        market_type = MarketType.TWO_WAY if args.market == 'two' else MarketType.THREE_WAY

        result = calc.find_best_arb(books, market_type)

        if result is None:
            print("Error: Invalid number of outcomes for selected market type")
            return

        # Adjust for custom stake
        if args.stake != 100:
            stake_ratio = args.stake / 100
            for key in result['stakes']:
                if key != 'total':
                    result['stakes'][key] *= stake_ratio
            result['stakes']['total'] = args.stake
            for key in result['returns']:
                result['returns'][key] *= stake_ratio
            result['profit']['guaranteed'] *= stake_ratio
            result['profit']['per_100'] = (result['profit']['guaranteed'] / args.stake) * 100

        print_arb_result(result, market_type, args.stake)


if __name__ == '__main__':
    main()
