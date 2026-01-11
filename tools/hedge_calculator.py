#!/usr/bin/env python3
"""
Advanced Hedge Calculator

Calculate optimal hedges for:
- Parlays (in-progress and completed legs)
- Futures bets
- Multi-way outcomes
- Live betting scenarios
"""

import argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class ParlayLeg:
    """Represents a parlay leg"""
    description: str
    odds: float
    status: str  # 'pending', 'won', 'lost'


class HedgeCalculator:
    """Advanced hedging calculations"""

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
    def calculate_parlay_hedge(
        original_stake: float,
        parlay_odds: float,
        hedge_odds: float,
        strategy: str = 'guarantee_profit'
    ) -> Dict:
        """
        Calculate hedge for a parlay

        Args:
            original_stake: Amount wagered on parlay
            parlay_odds: Current/original parlay odds (American)
            hedge_odds: Odds for hedge bet (American)
            strategy: 'guarantee_profit', 'maximize_profit', or 'freeroll'

        Returns:
            Hedge calculation details
        """
        # Convert to decimal
        parlay_decimal = HedgeCalculator.american_to_decimal(parlay_odds)
        hedge_decimal = HedgeCalculator.american_to_decimal(hedge_odds)

        # Potential parlay payout
        parlay_payout = original_stake * parlay_decimal

        if strategy == 'guarantee_profit':
            # Hedge stake that guarantees equal profit on both outcomes
            hedge_stake = parlay_payout / hedge_decimal

            # Calculate profits
            profit_if_parlay = parlay_payout - original_stake - hedge_stake
            profit_if_hedge = (hedge_stake * hedge_decimal) - original_stake - hedge_stake

            return {
                'strategy': 'Guarantee Equal Profit',
                'hedge_stake': hedge_stake,
                'parlay_payout': parlay_payout,
                'hedge_payout': hedge_stake * hedge_decimal,
                'profit_if_parlay_wins': profit_if_parlay,
                'profit_if_hedge_wins': profit_if_hedge,
                'total_risk': original_stake + hedge_stake,
                'roi': (profit_if_parlay / (original_stake + hedge_stake)) * 100
            }

        elif strategy == 'maximize_profit':
            # Let the parlay ride but hedge some
            # Hedge half of the profit
            target_hedge_profit = (parlay_payout - original_stake) / 2
            hedge_stake = target_hedge_profit / (hedge_decimal - 1)

            profit_if_parlay = parlay_payout - original_stake - hedge_stake
            profit_if_hedge = (hedge_stake * hedge_decimal) - original_stake - hedge_stake

            return {
                'strategy': 'Maximize Parlay Upside',
                'hedge_stake': hedge_stake,
                'parlay_payout': parlay_payout,
                'hedge_payout': hedge_stake * hedge_decimal,
                'profit_if_parlay_wins': profit_if_parlay,
                'profit_if_hedge_wins': profit_if_hedge,
                'total_risk': original_stake + hedge_stake,
                'roi_if_parlay': (profit_if_parlay / (original_stake + hedge_stake)) * 100,
                'roi_if_hedge': (profit_if_hedge / (original_stake + hedge_stake)) * 100
            }

        elif strategy == 'freeroll':
            # Hedge enough to get original stake back
            # Solve: hedge_stake * hedge_decimal - hedge_stake = original_stake
            hedge_stake = original_stake / (hedge_decimal - 1)

            profit_if_parlay = parlay_payout - original_stake - hedge_stake
            profit_if_hedge = 0  # Breaking even

            return {
                'strategy': 'Freeroll (Get Stakes Back)',
                'hedge_stake': hedge_stake,
                'parlay_payout': parlay_payout,
                'hedge_payout': hedge_stake * hedge_decimal,
                'profit_if_parlay_wins': profit_if_parlay,
                'profit_if_hedge_wins': profit_if_hedge,
                'total_risk': original_stake + hedge_stake,
                'roi_if_parlay': (profit_if_parlay / (original_stake + hedge_stake)) * 100
            }

        return {}

    @staticmethod
    def calculate_futures_hedge(
        original_stake: float,
        original_odds: float,
        current_odds: float,
        hedge_odds: float,
        num_remaining: int = 1
    ) -> Dict:
        """
        Calculate hedge for a futures bet

        Args:
            original_stake: Original bet amount
            original_odds: Original odds when bet was placed (American)
            current_odds: Current odds (American)
            hedge_odds: Odds to hedge against (American)
            num_remaining: Number of remaining competitors

        Returns:
            Futures hedge analysis
        """
        orig_decimal = HedgeCalculator.american_to_decimal(original_odds)
        hedge_decimal = HedgeCalculator.american_to_decimal(hedge_odds)

        # Potential payout if futures bet wins
        futures_payout = original_stake * orig_decimal

        # Calculate hedge for guaranteed profit
        hedge_stake = futures_payout / hedge_decimal

        profit_if_futures = futures_payout - original_stake - hedge_stake
        profit_if_hedge = (hedge_stake * hedge_decimal) - original_stake - hedge_stake

        # Calculate ROI
        total_invested = original_stake + hedge_stake
        roi = (profit_if_futures / total_invested) * 100

        # Calculate value of position
        current_decimal = HedgeCalculator.american_to_decimal(current_odds)
        current_value = original_stake * current_decimal
        unrealized_pl = current_value - original_stake

        return {
            'original_stake': original_stake,
            'original_odds': original_odds,
            'current_odds': current_odds,
            'hedge_odds': hedge_odds,
            'potential_futures_payout': futures_payout,
            'hedge_stake': hedge_stake,
            'total_invested': total_invested,
            'profit_if_futures_wins': profit_if_futures,
            'profit_if_hedge_wins': profit_if_hedge,
            'guaranteed_profit': profit_if_futures,  # Same as profit_if_hedge
            'roi': roi,
            'unrealized_pl': unrealized_pl,
            'num_remaining': num_remaining
        }

    @staticmethod
    def calculate_multiway_hedge(
        original_stake: float,
        original_odds: float,
        hedge_scenarios: List[Tuple[str, float]]
    ) -> Dict:
        """
        Calculate hedges for multiple outcomes

        Args:
            original_stake: Original bet amount
            original_odds: Original bet odds (American)
            hedge_scenarios: List of (description, odds) for hedge options

        Returns:
            Multi-way hedge analysis
        """
        orig_decimal = HedgeCalculator.american_to_decimal(original_odds)
        original_payout = original_stake * orig_decimal

        hedge_info = []
        total_hedge_stake = 0

        for desc, odds in hedge_scenarios:
            hedge_decimal = HedgeCalculator.american_to_decimal(odds)
            # Calculate stake needed to guarantee profit
            hedge_stake = original_payout / hedge_decimal
            hedge_payout = hedge_stake * hedge_decimal

            hedge_info.append({
                'description': desc,
                'odds': odds,
                'stake': hedge_stake,
                'payout': hedge_payout
            })

            total_hedge_stake += hedge_stake

        # Calculate profits
        profit_if_original = original_payout - original_stake - total_hedge_stake
        profit_per_hedge = [(h['payout'] - original_stake - total_hedge_stake) for h in hedge_info]

        return {
            'original_stake': original_stake,
            'original_odds': original_odds,
            'original_payout': original_payout,
            'total_hedge_stake': total_hedge_stake,
            'total_invested': original_stake + total_hedge_stake,
            'hedge_bets': hedge_info,
            'profit_if_original_wins': profit_if_original,
            'profits_if_hedges_win': profit_per_hedge,
            'roi': (profit_if_original / (original_stake + total_hedge_stake)) * 100
        }

    @staticmethod
    def middle_opportunity(
        odds1: float,
        odds2: float,
        spread1: float,
        spread2: float,
        stake_per_side: float = 100
    ) -> Dict:
        """
        Calculate middle opportunity

        Args:
            odds1: Odds for side 1 (American)
            odds2: Odds for side 2 (American)
            spread1: Spread for side 1
            spread2: Spread for side 2
            stake_per_side: Amount to bet on each side

        Returns:
            Middle analysis
        """
        decimal1 = HedgeCalculator.american_to_decimal(odds1)
        decimal2 = HedgeCalculator.american_to_decimal(odds2)

        # Check if middle exists
        has_middle = abs(spread1 - spread2) > 0.5

        # Calculate outcomes
        payout1 = stake_per_side * decimal1
        payout2 = stake_per_side * decimal2

        # If middle hits (both win)
        profit_if_middle = payout1 + payout2 - (2 * stake_per_side)

        # If only one side wins
        profit_if_side1_only = payout1 - (2 * stake_per_side)
        profit_if_side2_only = payout2 - (2 * stake_per_side)

        middle_range = f"{min(spread1, spread2)} to {max(spread1, spread2)}"

        return {
            'has_middle': has_middle,
            'middle_range': middle_range,
            'spread1': spread1,
            'spread2': spread2,
            'odds1': odds1,
            'odds2': odds2,
            'stake_per_side': stake_per_side,
            'total_risk': 2 * stake_per_side,
            'profit_if_middle': profit_if_middle,
            'profit_if_only_side1': profit_if_side1_only,
            'profit_if_only_side2': profit_if_side2_only,
            'worst_case': max(profit_if_side1_only, profit_if_side2_only),
            'best_case': profit_if_middle,
            'roi_if_middle': (profit_if_middle / (2 * stake_per_side)) * 100
        }


def print_parlay_hedge(result: Dict):
    """Print parlay hedge results"""
    print(f"\n{'='*70}")
    print(f"PARLAY HEDGE CALCULATOR - {result['strategy']}")
    print(f"{'='*70}")

    print(f"\nOriginal Position:")
    print(f"  Parlay Potential Payout: ${result['parlay_payout']:.2f}")

    print(f"\nHedge Recommendation:")
    print(f"  Hedge Stake: ${result['hedge_stake']:.2f}")
    print(f"  Hedge Payout if Wins: ${result['hedge_payout']:.2f}")

    print(f"\nOutcomes:")
    print(f"  If Parlay Wins:  ${result['profit_if_parlay_wins']:+.2f}")
    print(f"  If Hedge Wins:   ${result['profit_if_hedge_wins']:+.2f}")

    print(f"\nSummary:")
    print(f"  Total Invested: ${result['total_risk']:.2f}")
    if 'roi' in result:
        print(f"  Guaranteed ROI: {result['roi']:+.2f}%")
    elif 'roi_if_parlay' in result:
        print(f"  ROI if Parlay: {result['roi_if_parlay']:+.2f}%")
        print(f"  ROI if Hedge: {result['roi_if_hedge']:+.2f}%")

    print(f"\n{'='*70}")


def print_futures_hedge(result: Dict):
    """Print futures hedge results"""
    print(f"\n{'='*70}")
    print(f"FUTURES HEDGE CALCULATOR")
    print(f"{'='*70}")

    print(f"\nOriginal Position:")
    print(f"  Original Stake: ${result['original_stake']:.2f}")
    print(f"  Original Odds: {result['original_odds']:+.0f}")
    print(f"  Current Odds: {result['current_odds']:+.0f}")
    print(f"  Unrealized P/L: ${result['unrealized_pl']:+.2f}")

    print(f"\nHedge Recommendation:")
    print(f"  Hedge Odds: {result['hedge_odds']:+.0f}")
    print(f"  Hedge Stake: ${result['hedge_stake']:.2f}")

    print(f"\nOutcomes:")
    print(f"  If Futures Wins: ${result['profit_if_futures_wins']:+.2f}")
    print(f"  If Hedge Wins:   ${result['profit_if_hedge_wins']:+.2f}")

    print(f"\nSummary:")
    print(f"  Total Invested: ${result['total_invested']:.2f}")
    print(f"  Guaranteed Profit: ${result['guaranteed_profit']:+.2f}")
    print(f"  ROI: {result['roi']:+.2f}%")

    if result['num_remaining'] > 1:
        print(f"\n  Note: {result['num_remaining']} competitors remaining")

    print(f"\n{'='*70}")


def main():
    parser = argparse.ArgumentParser(
        description='Advanced Hedge Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parlay hedge (guarantee profit)
  %(prog)s parlay --stake 100 --parlay-odds +800 --hedge-odds -110

  # Parlay hedge (maximize upside)
  %(prog)s parlay --stake 100 --parlay-odds +1200 --hedge-odds -105 --strategy maximize

  # Parlay freeroll
  %(prog)s parlay --stake 50 --parlay-odds +500 --hedge-odds -110 --strategy freeroll

  # Futures hedge
  %(prog)s futures --stake 100 --original-odds +2000 --current-odds +500 --hedge-odds -150

  # Middle opportunity
  %(prog)s middle --odds1 -110 --odds2 -110 --spread1 -3 --spread2 +3.5 --stake 100
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Hedge type')

    # Parlay hedge
    parlay_parser = subparsers.add_parser('parlay', help='Hedge a parlay')
    parlay_parser.add_argument('-s', '--stake', type=float, required=True,
                              help='Original parlay stake')
    parlay_parser.add_argument('-p', '--parlay-odds', type=float, required=True,
                              help='Parlay odds (American)')
    parlay_parser.add_argument('-h', '--hedge-odds', type=float, required=True,
                              help='Hedge bet odds (American)', dest='hedge_odds_parlay')
    parlay_parser.add_argument('--strategy', choices=['guarantee', 'maximize', 'freeroll'],
                              default='guarantee',
                              help='Hedging strategy (default: guarantee)')

    # Futures hedge
    futures_parser = subparsers.add_parser('futures', help='Hedge a futures bet')
    futures_parser.add_argument('-s', '--stake', type=float, required=True,
                               help='Original futures stake')
    futures_parser.add_argument('-o', '--original-odds', type=float, required=True,
                               help='Original futures odds (American)')
    futures_parser.add_argument('-c', '--current-odds', type=float, required=True,
                               help='Current odds for your selection (American)')
    futures_parser.add_argument('-h', '--hedge-odds', type=float, required=True,
                               help='Hedge odds (American)', dest='hedge_odds_futures')
    futures_parser.add_argument('-n', '--num-remaining', type=int, default=1,
                               help='Number of remaining competitors (default: 1)')

    # Middle opportunity
    middle_parser = subparsers.add_parser('middle', help='Calculate middle opportunity')
    middle_parser.add_argument('--odds1', type=float, required=True,
                              help='Odds for side 1 (American)')
    middle_parser.add_argument('--odds2', type=float, required=True,
                              help='Odds for side 2 (American)')
    middle_parser.add_argument('--spread1', type=float, required=True,
                              help='Spread for side 1')
    middle_parser.add_argument('--spread2', type=float, required=True,
                              help='Spread for side 2')
    middle_parser.add_argument('-s', '--stake', type=float, default=100,
                              help='Stake per side (default: 100)')

    args = parser.parse_args()

    if args.command == 'parlay':
        strategy_map = {
            'guarantee': 'guarantee_profit',
            'maximize': 'maximize_profit',
            'freeroll': 'freeroll'
        }

        result = HedgeCalculator.calculate_parlay_hedge(
            args.stake,
            args.parlay_odds,
            args.hedge_odds_parlay,
            strategy=strategy_map[args.strategy]
        )

        print_parlay_hedge(result)

    elif args.command == 'futures':
        result = HedgeCalculator.calculate_futures_hedge(
            args.stake,
            args.original_odds,
            args.current_odds,
            args.hedge_odds_futures,
            args.num_remaining
        )

        print_futures_hedge(result)

    elif args.command == 'middle':
        result = HedgeCalculator.middle_opportunity(
            args.odds1,
            args.odds2,
            args.spread1,
            args.spread2,
            args.stake
        )

        print(f"\n{'='*70}")
        print(f"MIDDLE OPPORTUNITY CALCULATOR")
        print(f"{'='*70}")

        if result['has_middle']:
            print(f"\n✅ MIDDLE EXISTS!")
            print(f"   Middle Range: {result['middle_range']}")
        else:
            print(f"\n❌ NO MIDDLE")

        print(f"\nSpreads:")
        print(f"  Side 1: {result['spread1']:+.1f} @ {result['odds1']:+.0f}")
        print(f"  Side 2: {result['spread2']:+.1f} @ {result['odds2']:+.0f}")

        print(f"\nStakes:")
        print(f"  Per Side: ${result['stake_per_side']:.2f}")
        print(f"  Total Risk: ${result['total_risk']:.2f}")

        print(f"\nPotential Outcomes:")
        print(f"  If Middle Hits (both win): ${result['profit_if_middle']:+.2f} ({result['roi_if_middle']:+.2f}%)")
        print(f"  If Only Side 1 Wins: ${result['profit_if_only_side1']:+.2f}")
        print(f"  If Only Side 2 Wins: ${result['profit_if_only_side2']:+.2f}")

        print(f"\nWorst Case: ${result['worst_case']:+.2f}")
        print(f"Best Case: ${result['best_case']:+.2f}")

        print(f"\n{'='*70}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
