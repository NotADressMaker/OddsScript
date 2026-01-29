#!/usr/bin/env python3
"""
Hedge Calculator - CLI tool for sizing a hedge bet to lock in profit.

Usage:
    hedge-calc --odds -110 --stake 100 --hedge-odds +120
"""

import sys
import argparse

from sportsbetlang.tools.base_tool import BaseTool
from sportsbetlang.common.odds import american_to_decimal


class HedgeCalculatorTool(BaseTool):
    """Hedge bet sizing calculator CLI tool"""

    def __init__(self):
        super().__init__(
            name='hedge-calc',
            description='Calculate hedge stake and locked-in profit for a two-way bet'
        )

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--odds', type=float, required=True, help='American odds for original bet')
        parser.add_argument('--stake', type=float, required=True, help='Original stake')
        parser.add_argument('--hedge-odds', type=float, required=True, help='American odds for hedge bet')

    def run(self, args: argparse.Namespace) -> int:
        odds = self.validate_odds(args.odds)
        hedge_odds = self.validate_odds(args.hedge_odds)
        stake = self.validate_stake(args.stake)

        decimal_main = float(american_to_decimal(odds))
        decimal_hedge = float(american_to_decimal(hedge_odds))

        hedge_stake = stake * (decimal_main - 1) / (decimal_hedge - 1)
        total_stake = stake + hedge_stake

        profit_main = (stake * decimal_main) - total_stake
        profit_hedge = (hedge_stake * decimal_hedge) - total_stake
        locked_profit = min(profit_main, profit_hedge)

        result = {
            'original_odds': odds,
            'original_stake': stake,
            'hedge_odds': hedge_odds,
            'hedge_stake': hedge_stake,
            'total_stake': total_stake,
            'profit_if_original_wins': profit_main,
            'profit_if_hedge_wins': profit_hedge,
            'locked_profit': locked_profit,
            'roi_pct': (locked_profit / total_stake) * 100
        }

        if args.output_format == 'json':
            self.print_output(result, 'json')
            return 0

        print(f"Original Odds:   {self.format_odds(odds)}")
        print(f"Hedge Odds:      {self.format_odds(hedge_odds)}")
        print(f"Original Stake:  {self.format_currency(stake)}")
        print(f"Hedge Stake:     {self.format_currency(hedge_stake)}")
        print(f"Total Stake:     {self.format_currency(total_stake)}")
        print()
        print(f"Profit (orig wins): {self.format_currency(profit_main)}")
        print(f"Profit (hedge wins): {self.format_currency(profit_hedge)}")
        print(f"Locked Profit:      {self.format_currency(locked_profit)} ({result['roi_pct']:.2f}%)")

        return 0


def main():
    tool = HedgeCalculatorTool()
    return tool.main()


if __name__ == '__main__':
    sys.exit(main())
