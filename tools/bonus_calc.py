#!/usr/bin/env python3
"""
Sportsbook Bonus and Promotion Calculator

Calculate optimal strategies for sportsbook bonuses, promos, and free bets.
"""

import argparse


class BonusCalculator:
    """Calculate optimal bonus play strategies"""

    @staticmethod
    def risk_free_bet(stake: float, odds: float) -> dict:
        """
        Calculate optimal hedge for risk-free bet promo

        Risk-free bet: If you lose, get stake back as free bet

        Args:
            stake: Amount of risk-free bet
            odds: Odds you're betting at

        Returns:
            Dictionary with hedge recommendations
        """
        # Calculate potential profit on main bet
        if odds > 0:
            main_profit = stake * (odds / 100)
        else:
            main_profit = stake * (100 / abs(odds))

        # To guarantee profit, we need to hedge
        # Hedge should cover: stake + hedge_stake = hedge_profit
        # This locks in profit regardless of outcome

        # Optimal hedge odds should be opposite side
        # For simplicity, assume -110 on other side
        hedge_odds = -110

        # Calculate hedge size
        # We want: main_profit = hedge_stake * (100/110)
        # So: hedge_stake = main_profit * (110/100)
        hedge_stake = main_profit * (110 / 100)

        # Scenario 1: Main bet wins
        scenario1_profit = main_profit - hedge_stake

        # Scenario 2: Main bet loses (get free bet)
        # Free bet value ~70% of stake (typical conversion)
        free_bet_value = stake * 0.70
        scenario2_profit = (stake * (100 / 110)) - hedge_stake + free_bet_value

        avg_profit = (scenario1_profit + scenario2_profit) / 2

        return {
            'main_stake': stake,
            'main_odds': odds,
            'hedge_stake': hedge_stake,
            'hedge_odds': hedge_odds,
            'scenario1_profit': scenario1_profit,
            'scenario2_profit': scenario2_profit,
            'avg_profit': avg_profit,
            'guaranteed_min': min(scenario1_profit, scenario2_profit)
        }

    @staticmethod
    def deposit_match(deposit: float, match_percent: float, rollover: float) -> dict:
        """
        Calculate deposit match bonus value

        Args:
            deposit: Deposit amount
            match_percent: Match percentage (e.g., 100 for 100% match)
            rollover: Rollover requirement (e.g., 5 for 5x)

        Returns:
            Analysis of bonus value
        """
        bonus_amount = deposit * (match_percent / 100)
        total_bankroll = deposit + bonus_amount
        rollover_requirement = bonus_amount * rollover

        # Estimate expected value
        # Assume -110 odds, 52% win rate (slight edge)
        # Expected ROI at -110 with 52% win rate ≈ -1.5%
        ev_per_dollar = -0.015

        expected_loss = rollover_requirement * abs(ev_per_dollar)
        net_value = bonus_amount - expected_loss

        return {
            'deposit': deposit,
            'bonus': bonus_amount,
            'total_bankroll': total_bankroll,
            'rollover_requirement': rollover_requirement,
            'expected_loss': expected_loss,
            'net_value': net_value,
            'effective_bonus_percent': (net_value / deposit) * 100
        }

    @staticmethod
    def free_bet_conversion(free_bet: float, odds: float, hedge_odds: float = -110) -> dict:
        """
        Calculate free bet conversion value

        Free bets don't return stake, only profit

        Args:
            free_bet: Free bet amount
            odds: Odds for free bet
            hedge_odds: Odds for hedge bet

        Returns:
            Optimal conversion strategy
        """
        # Free bet profit (no stake returned)
        if odds > 0:
            free_bet_profit = free_bet * (odds / 100)
        else:
            free_bet_profit = free_bet * (100 / abs(odds))

        # Hedge to lock in profit
        if hedge_odds > 0:
            hedge_stake = free_bet_profit / (1 + (hedge_odds / 100))
        else:
            hedge_stake = free_bet_profit / (1 + (100 / abs(hedge_odds)))

        # Guaranteed profit
        guaranteed_profit = free_bet_profit - hedge_stake

        # Conversion rate
        conversion_rate = (guaranteed_profit / free_bet) * 100

        return {
            'free_bet_amount': free_bet,
            'free_bet_odds': odds,
            'free_bet_profit': free_bet_profit,
            'hedge_odds': hedge_odds,
            'hedge_stake': hedge_stake,
            'guaranteed_profit': guaranteed_profit,
            'conversion_rate': conversion_rate
        }

    @staticmethod
    def profit_boost(stake: float, odds: float, boost_percent: float) -> dict:
        """
        Calculate value of profit boost

        Args:
            stake: Bet amount
            odds: Original odds
            boost_percent: Boost percentage (e.g., 50 for 50% boost)

        Returns:
            Analysis of boosted bet
        """
        # Original profit
        if odds > 0:
            original_profit = stake * (odds / 100)
        else:
            original_profit = stake * (100 / abs(odds))

        # Boosted profit
        boosted_profit = original_profit * (1 + boost_percent / 100)

        # Calculate boosted odds
        boosted_odds_decimal = (boosted_profit / stake) + 1
        if boosted_odds_decimal >= 2.0:
            boosted_odds = (boosted_odds_decimal - 1) * 100
        else:
            boosted_odds = -100 / (boosted_odds_decimal - 1)

        # Extra value
        extra_value = boosted_profit - original_profit

        return {
            'stake': stake,
            'original_odds': odds,
            'boosted_odds': boosted_odds,
            'original_profit': original_profit,
            'boosted_profit': boosted_profit,
            'extra_value': extra_value,
            'boost_percent': boost_percent
        }

    @staticmethod
    def odds_boost_finder(target_odds: float, desired_boost: float) -> float:
        """
        Find minimum original odds needed for specific boosted odds

        Args:
            target_odds: Desired odds after boost
            desired_boost: Boost percentage

        Returns:
            Minimum original odds needed
        """
        # Work backwards
        # boosted_profit = original_profit * (1 + boost/100)
        # We want boosted_odds, so find original

        if target_odds > 0:
            target_decimal = (target_odds / 100) + 1
        else:
            target_decimal = (100 / abs(target_odds)) + 1

        original_decimal = target_decimal / (1 + desired_boost / 100)

        if original_decimal >= 2.0:
            original_odds = (original_decimal - 1) * 100
        else:
            original_odds = -100 / (original_decimal - 1)

        return original_odds


def cmd_risk_free(args):
    """Handle risk-free bet calculation"""
    calc = BonusCalculator()
    result = calc.risk_free_bet(args.stake, args.odds)

    print(f"\n{'='*60}")
    print(f"Risk-Free Bet Analysis")
    print(f"{'='*60}")
    print(f"\nMain Bet:")
    print(f"  Stake: ${result['main_stake']:.2f}")
    print(f"  Odds: {result['main_odds']:+.0f}")

    print(f"\nRecommended Hedge:")
    print(f"  Stake: ${result['hedge_stake']:.2f}")
    print(f"  Odds: {result['hedge_odds']:+.0f}")

    print(f"\nOutcomes:")
    print(f"  If main bet wins: ${result['scenario1_profit']:+.2f}")
    print(f"  If main bet loses: ${result['scenario2_profit']:+.2f}")
    print(f"  Average profit: ${result['avg_profit']:+.2f}")
    print(f"  Guaranteed minimum: ${result['guaranteed_min']:+.2f}")


def cmd_deposit(args):
    """Handle deposit match calculation"""
    calc = BonusCalculator()
    result = calc.deposit_match(args.deposit, args.match, args.rollover)

    print(f"\n{'='*60}")
    print(f"Deposit Match Bonus Analysis")
    print(f"{'='*60}")
    print(f"\nBonus Terms:")
    print(f"  Deposit: ${result['deposit']:.2f}")
    print(f"  Bonus ({args.match}%): ${result['bonus']:.2f}")
    print(f"  Total Bankroll: ${result['total_bankroll']:.2f}")

    print(f"\nRollover:")
    print(f"  Requirement ({args.rollover}x): ${result['rollover_requirement']:.2f}")
    print(f"  Expected Loss: ${result['expected_loss']:.2f}")

    print(f"\nValue:")
    print(f"  Net Bonus Value: ${result['net_value']:.2f}")
    print(f"  Effective Bonus: {result['effective_bonus_percent']:.1f}%")

    if result['net_value'] > 0:
        print(f"\n✓ This bonus has positive expected value")
    else:
        print(f"\n✗ This bonus has negative expected value")


def cmd_freebet(args):
    """Handle free bet conversion"""
    calc = BonusCalculator()
    result = calc.free_bet_conversion(args.amount, args.odds, args.hedge)

    print(f"\n{'='*60}")
    print(f"Free Bet Conversion")
    print(f"{'='*60}")
    print(f"\nFree Bet:")
    print(f"  Amount: ${result['free_bet_amount']:.2f}")
    print(f"  Odds: {result['free_bet_odds']:+.0f}")
    print(f"  Potential Profit: ${result['free_bet_profit']:.2f}")

    print(f"\nHedge Bet:")
    print(f"  Stake: ${result['hedge_stake']:.2f}")
    print(f"  Odds: {result['hedge_odds']:+.0f}")

    print(f"\nResult:")
    print(f"  Guaranteed Profit: ${result['guaranteed_profit']:.2f}")
    print(f"  Conversion Rate: {result['conversion_rate']:.1f}%")

    if result['conversion_rate'] >= 70:
        print(f"\n✓ EXCELLENT conversion rate")
    elif result['conversion_rate'] >= 60:
        print(f"\n✓ GOOD conversion rate")
    else:
        print(f"\n~ Consider looking for better odds")


def cmd_boost(args):
    """Handle profit boost calculation"""
    calc = BonusCalculator()
    result = calc.profit_boost(args.stake, args.odds, args.boost)

    print(f"\n{'='*60}")
    print(f"Profit Boost Analysis")
    print(f"{'='*60}")
    print(f"\nBet Details:")
    print(f"  Stake: ${result['stake']:.2f}")
    print(f"  Original Odds: {result['original_odds']:+.0f}")
    print(f"  Boosted Odds: {result['boosted_odds']:+.0f}")
    print(f"  Boost: {result['boost_percent']:.0f}%")

    print(f"\nProfit:")
    print(f"  Original: ${result['original_profit']:.2f}")
    print(f"  Boosted: ${result['boosted_profit']:.2f}")
    print(f"  Extra Value: ${result['extra_value']:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description='Sportsbook Bonus Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Bonus type')

    # Risk-free bet
    rf_parser = subparsers.add_parser('riskfree', help='Risk-free bet hedge')
    rf_parser.add_argument('stake', type=float, help='Risk-free bet amount')
    rf_parser.add_argument('odds', type=float, help='Odds for risk-free bet')

    # Deposit match
    dep_parser = subparsers.add_parser('deposit', help='Deposit match bonus')
    dep_parser.add_argument('deposit', type=float, help='Deposit amount')
    dep_parser.add_argument('match', type=float, help='Match percent (e.g., 100)')
    dep_parser.add_argument('rollover', type=float, help='Rollover (e.g., 5)')

    # Free bet
    fb_parser = subparsers.add_parser('freebet', help='Free bet conversion')
    fb_parser.add_argument('amount', type=float, help='Free bet amount')
    fb_parser.add_argument('odds', type=float, help='Odds for free bet')
    fb_parser.add_argument('-hg', '--hedge', type=float, default=-110,
                          help='Hedge odds (default: -110)')

    # Profit boost
    boost_parser = subparsers.add_parser('boost', help='Profit boost')
    boost_parser.add_argument('stake', type=float, help='Bet amount')
    boost_parser.add_argument('odds', type=float, help='Original odds')
    boost_parser.add_argument('boost', type=float, help='Boost percent (e.g., 50)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'riskfree':
        cmd_risk_free(args)
    elif args.command == 'deposit':
        cmd_deposit(args)
    elif args.command == 'freebet':
        cmd_freebet(args)
    elif args.command == 'boost':
        cmd_boost(args)


if __name__ == '__main__':
    main()
