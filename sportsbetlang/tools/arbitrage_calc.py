#!/usr/bin/env python3
"""
Arbitrage Calculator - CLI tool for two-way arbitrage sizing.

Usage:
    arbitrage-calc --odds1 -110 --odds2 +105 --stake 100
"""

import sys
import argparse

from sportsbetlang.tools.base_tool import BaseTool
from sportsbetlang.common.odds import american_to_decimal


class ArbitrageCalculatorTool(BaseTool):
    """Two-way arbitrage calculator CLI tool"""

    def __init__(self):
        super().__init__(
            name='arbitrage-calc',
            description='Calculate two-way arbitrage stakes and profit'
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--odds1', type=float, required=True, help='American odds for side 1')
        parser.add_argument('--odds2', type=float, required=True, help='American odds for side 2')
        parser.add_argument('--stake', type=float, default=100.0, help='Total stake to allocate')
        parser.add_argument('--label1', type=str, default='Side 1', help='Label for side 1')
        parser.add_argument('--label2', type=str, default='Side 2', help='Label for side 2')

    def run(self, args: argparse.Namespace) -> int:
        odds1 = self.validate_odds(args.odds1)
        odds2 = self.validate_odds(args.odds2)
        total_stake = self.validate_stake(args.stake)

        decimal1 = float(american_to_decimal(odds1))
        decimal2 = float(american_to_decimal(odds2))

        implied1 = 1 / decimal1
        implied2 = 1 / decimal2
        total_implied = implied1 + implied2

        stake1 = total_stake * (implied1 / total_implied)
        stake2 = total_stake * (implied2 / total_implied)

        payout1 = stake1 * decimal1
        payout2 = stake2 * decimal2
        profit = min(payout1, payout2) - total_stake
        roi = (profit / total_stake) * 100

        result = {
            'odds1': odds1,
            'odds2': odds2,
            'label1': args.label1,
            'label2': args.label2,
            'stake_total': total_stake,
            'stake1': stake1,
            'stake2': stake2,
            'implied_prob1': implied1,
            'implied_prob2': implied2,
            'total_implied': total_implied,
            'arb_margin_pct': (1 - total_implied) * 100,
            'profit': profit,
            'roi_pct': roi
        }

        if args.output_format == 'json':
            self.print_output(result, 'json')
            return 0

        print(f"{args.label1}: {self.format_odds(odds1)}")
        print(f"{args.label2}: {self.format_odds(odds2)}")
        print(f"Total Implied: {self.format_percentage(total_implied)}")
        print(f"Arb Margin:    {result['arb_margin_pct']:.2f}%")
        print()
        self.print_table(
            headers=['Side', 'Stake', 'Payout'],
            rows=[
                [args.label1, self.format_currency(stake1), self.format_currency(payout1)],
                [args.label2, self.format_currency(stake2), self.format_currency(payout2)],
            ],
            title='Recommended Stakes'
        )
        print(f"Total Stake:   {self.format_currency(total_stake)}")
        print(f"Guaranteed P&L: {self.format_currency(profit)} ({roi:.2f}%)")

        if total_implied >= 1:
            self.print_warning('No true arbitrage detected (total implied >= 100%).')

        return 0


def main():
    tool = ArbitrageCalculatorTool()
    return tool.main()


if __name__ == '__main__':
    sys.exit(main())
