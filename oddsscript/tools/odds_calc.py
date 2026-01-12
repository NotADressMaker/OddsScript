#!/usr/bin/env python3
"""
Quick Odds Calculator - CLI tool for fast betting calculations

Refactored to use oddsscript.common utilities (eliminates code duplication).

Usage:
    odds-calc convert -110
    odds-calc kelly --prob 0.55 --odds -110 --bankroll 1000
    odds-calc ev --prob 0.55 --odds -110 --stake 100
    odds-calc parlay -110 -120 +150
    odds-calc vig -110 -110
"""

import sys
import argparse
from typing import List

from oddsscript.tools.base_tool import BaseTool
from oddsscript.common.odds import (
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    remove_vig,
    calculate_vig
)
from oddsscript.common.kelly import calculate_kelly
from oddsscript.common.validators import ValidationError


class OddsCalculatorTool(BaseTool):
    """Quick odds calculator CLI tool"""

    def __init__(self):
        super().__init__(
            name='odds-calc',
            description='Quick calculator for betting odds and expected value'
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        """Add odds calculator specific arguments"""
        subparsers = parser.add_subparsers(dest='command', help='Calculation type')

        # Convert odds
        convert = subparsers.add_parser('convert', help='Convert odds between formats')
        convert.add_argument('odds', type=float, help='American odds (e.g., -110)')
        convert.add_argument('--to', choices=['decimal', 'fractional'], default='decimal',
                           help='Target format (default: decimal)')

        # Calculate payout
        payout = subparsers.add_parser('payout', help='Calculate payout for a bet')
        payout.add_argument('--odds', type=float, required=True, help='American odds')
        payout.add_argument('--stake', type=float, required=True, help='Stake amount')

        # Kelly criterion
        kelly = subparsers.add_parser('kelly', help='Calculate Kelly criterion bet size')
        kelly.add_argument('--prob', type=float, required=True, help='True probability (0-1)')
        kelly.add_argument('--odds', type=float, required=True, help='American odds')
        kelly.add_argument('--bankroll', type=float, help='Bankroll (optional)')
        kelly.add_argument('--fraction', type=float, default=0.25,
                         help='Kelly fraction (default: 0.25)')

        # Expected value
        ev = subparsers.add_parser('ev', help='Calculate expected value')
        ev.add_argument('--prob', type=float, required=True, help='True probability (0-1)')
        ev.add_argument('--odds', type=float, required=True, help='American odds')
        ev.add_argument('--stake', type=float, default=100, help='Stake amount (default: 100)')

        # Parlay odds
        parlay = subparsers.add_parser('parlay', help='Calculate parlay odds')
        parlay.add_argument('odds', type=float, nargs='+', help='American odds for each leg')

        # Vig calculator
        vig = subparsers.add_parser('vig', help='Calculate bookmaker vig')
        vig.add_argument('odds1', type=float, help='First odds')
        vig.add_argument('odds2', type=float, help='Second odds')
        vig.add_argument('--remove', action='store_true', help='Show fair odds with vig removed')

    def run(self, args: argparse.Namespace) -> int:
        """Run the odds calculator"""
        if not args.command:
            self.parser.print_help()
            return 1

        try:
            if args.command == 'convert':
                return self._convert_odds(args)
            elif args.command == 'payout':
                return self._calculate_payout(args)
            elif args.command == 'kelly':
                return self._calculate_kelly(args)
            elif args.command == 'ev':
                return self._calculate_ev(args)
            elif args.command == 'parlay':
                return self._calculate_parlay(args)
            elif args.command == 'vig':
                return self._calculate_vig(args)
            else:
                self.print_error(f"Unknown command: {args.command}")
                return 1

        except ValidationError as e:
            self.print_error(str(e))
            return 1

    def _convert_odds(self, args) -> int:
        """Convert odds to different format"""
        odds = self.validate_odds(args.odds)

        if args.to == 'decimal':
            result = float(american_to_decimal(odds))
            if args.output_format == 'json':
                self.print_output({
                    'american': odds,
                    'decimal': result
                }, 'json')
            else:
                print(f"American: {self.format_odds(odds)}")
                print(f"Decimal:  {result:.4f}")
        elif args.to == 'fractional':
            from oddsscript.common.odds import OddsConverter
            result = OddsConverter.american_to_fractional(odds)
            if args.output_format == 'json':
                self.print_output({
                    'american': odds,
                    'fractional': result
                }, 'json')
            else:
                print(f"American:   {self.format_odds(odds)}")
                print(f"Fractional: {result}")

        return 0

    def _calculate_payout(self, args) -> int:
        """Calculate payout for a bet"""
        odds = self.validate_odds(args.odds)
        stake = self.validate_stake(args.stake)

        decimal = float(american_to_decimal(odds))
        profit = stake * (decimal - 1)
        total_return = stake + profit

        if args.output_format == 'json':
            self.print_output({
                'stake': stake,
                'odds': odds,
                'profit': profit,
                'total_return': total_return,
                'roi': (profit / stake) * 100
            }, 'json')
        else:
            print(f"Odds:         {self.format_odds(odds)}")
            print(f"Stake:        {self.format_currency(stake)}")
            print(f"Profit:       {self.format_currency(profit)}")
            print(f"Total Return: {self.format_currency(total_return)}")
            print(f"ROI:          {self.format_percentage(profit / stake)}")

        return 0

    def _calculate_kelly(self, args) -> int:
        """Calculate Kelly criterion bet size"""
        prob = self.validate_probability(args.prob)
        odds = self.validate_odds(args.odds)

        if args.bankroll:
            bankroll = self.validate_bankroll(args.bankroll)
        else:
            bankroll = None

        # Use shared Kelly calculation
        result = calculate_kelly(
            odds=odds,
            true_prob=prob,
            kelly_fraction=args.fraction,
            bankroll=bankroll
        )

        if args.output_format == 'json':
            self.print_output(result, 'json')
        else:
            print(f"True Probability:    {self.format_probability(prob)}")
            print(f"Market Probability:  {self.format_probability(result['market_prob'])}")
            print(f"Edge:                {self.format_percentage(result['edge'])}")
            print(f"Full Kelly:          {self.format_percentage(result['kelly_pct'])}")
            print(f"Fractional Kelly:    {self.format_percentage(result['fractional_kelly'])}")

            if bankroll:
                print(f"\nBankroll:            {self.format_currency(bankroll)}")
                print(f"Recommended Stake:   {self.format_currency(result['stake'])}")
                print(f"Expected Profit:     {self.format_currency(result['expected_profit'])}")

            print(f"\n{result['recommended']}")

        return 0

    def _calculate_ev(self, args) -> int:
        """Calculate expected value"""
        prob = self.validate_probability(args.prob)
        odds = self.validate_odds(args.odds)
        stake = self.validate_stake(args.stake)

        decimal = float(american_to_decimal(odds))
        win_amount = stake * (decimal - 1)
        loss_amount = stake
        ev = (prob * win_amount) - ((1 - prob) * loss_amount)

        market_prob = float(implied_probability(odds))
        edge = prob - market_prob

        if args.output_format == 'json':
            self.print_output({
                'stake': stake,
                'odds': odds,
                'true_prob': prob,
                'market_prob': market_prob,
                'edge': edge,
                'ev': ev,
                'ev_percent': (ev / stake) * 100,
                'positive_ev': ev > 0
            }, 'json')
        else:
            print(f"Stake:               {self.format_currency(stake)}")
            print(f"Odds:                {self.format_odds(odds)}")
            print(f"True Probability:    {self.format_probability(prob)}")
            print(f"Market Probability:  {self.format_probability(market_prob)}")
            print(f"Edge:                {self.format_percentage(edge)}")
            print(f"\nExpected Value:      {self.format_currency(ev)}")
            print(f"EV %:                {self.format_percentage(ev / stake)}")

            if ev > 0:
                print(f"\n✅ Positive EV - Good bet!")
            else:
                print(f"\n❌ Negative EV - Skip this bet")

        return 0

    def _calculate_parlay(self, args) -> int:
        """Calculate parlay odds"""
        # Validate all odds
        odds_list = [self.validate_odds(o) for o in args.odds]

        # Convert to decimal
        decimal_odds = [float(american_to_decimal(o)) for o in odds_list]

        # Calculate combined odds
        combined_decimal = 1
        for odd in decimal_odds:
            combined_decimal *= odd

        combined_american = decimal_to_american(combined_decimal)

        # Calculate combined probability (assuming independent)
        individual_probs = [float(implied_probability(o)) for o in odds_list]
        combined_prob = 1
        for prob in individual_probs:
            combined_prob *= prob

        if args.output_format == 'json':
            self.print_output({
                'legs': len(odds_list),
                'individual_odds': odds_list,
                'parlay_odds_american': combined_american,
                'parlay_odds_decimal': combined_decimal,
                'combined_probability': combined_prob,
                'implied_prob_pct': combined_prob * 100
            }, 'json')
        else:
            print(f"Parlay ({len(odds_list)} legs):")
            print("=" * 40)
            for i, (odd, prob) in enumerate(zip(odds_list, individual_probs), 1):
                print(f"  Leg {i}: {self.format_odds(odd)} ({self.format_probability(prob)})")

            print(f"\nCombined Odds:       {self.format_odds(combined_american)}")
            print(f"Decimal Odds:        {combined_decimal:.2f}")
            print(f"Combined Probability: {self.format_probability(combined_prob)}")

        return 0

    def _calculate_vig(self, args) -> int:
        """Calculate bookmaker vig"""
        odds1 = self.validate_odds(args.odds1)
        odds2 = self.validate_odds(args.odds2)

        prob1 = float(implied_probability(odds1))
        prob2 = float(implied_probability(odds2))

        vig = calculate_vig(prob1, prob2)

        if args.output_format == 'json':
            result = {
                'odds1': odds1,
                'odds2': odds2,
                'implied_prob1': prob1,
                'implied_prob2': prob2,
                'total_prob': prob1 + prob2,
                'vig_percent': vig
            }

            if args.remove:
                fair1, fair2 = remove_vig(prob1, prob2)
                result['fair_prob1'] = fair1
                result['fair_prob2'] = fair2
                result['fair_odds1'] = decimal_to_american(1 / fair1)
                result['fair_odds2'] = decimal_to_american(1 / fair2)

            self.print_output(result, 'json')
        else:
            print(f"Side 1 Odds:         {self.format_odds(odds1)} ({self.format_probability(prob1)})")
            print(f"Side 2 Odds:         {self.format_odds(odds2)} ({self.format_probability(prob2)})")
            print(f"Total Probability:   {self.format_percentage(prob1 + prob2)}")
            print(f"\nVig:                 {vig:.2f}%")

            if args.remove:
                fair1, fair2 = remove_vig(prob1, prob2)
                fair_odds1 = decimal_to_american(1 / fair1)
                fair_odds2 = decimal_to_american(1 / fair2)

                print(f"\nFair Odds (vig removed):")
                print(f"  Side 1: {self.format_odds(fair_odds1)} ({self.format_probability(fair1)})")
                print(f"  Side 2: {self.format_odds(fair_odds2)} ({self.format_probability(fair2)})")

        return 0


def main():
    """Main entry point"""
    tool = OddsCalculatorTool()
    return tool.main()


if __name__ == '__main__':
    sys.exit(main())
