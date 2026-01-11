#!/usr/bin/env python3
"""
Quick Odds Calculator - CLI tool for fast betting calculations

Usage:
    python odds_calc.py american -110
    python odds_calc.py kelly --prob 0.55 --odds -110 --bankroll 1000
    python odds_calc.py ev --prob 0.55 --odds -110 --stake 100
    python odds_calc.py parlay -110 -120 +150
"""

import argparse
import sys


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal"""
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


def decimal_to_american(odds: float) -> float:
    """Convert decimal odds to American"""
    if odds >= 2.0:
        return (odds - 1) * 100
    else:
        return -100 / (odds - 1)


def implied_probability(odds: float) -> float:
    """Calculate implied probability from American odds"""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def calculate_payout(stake: float, odds: float) -> tuple:
    """Calculate profit and total return"""
    if odds > 0:
        profit = stake * (odds / 100)
    else:
        profit = stake * (100 / abs(odds))
    return profit, stake + profit


def kelly_criterion(true_prob: float, odds: float) -> float:
    """Calculate Kelly criterion percentage"""
    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1
    p = true_prob
    q = 1 - p
    kelly = (b * p - q) / b
    return max(0, kelly)


def calculate_ev(true_prob: float, odds: float, stake: float) -> float:
    """Calculate expected value"""
    decimal_odds = american_to_decimal(odds)
    win_amount = stake * (decimal_odds - 1)
    loss_amount = stake
    ev = (true_prob * win_amount) - ((1 - true_prob) * loss_amount)
    return ev


def parlay_odds(*odds_list) -> float:
    """Calculate parlay odds"""
    decimal_odds = [american_to_decimal(o) for o in odds_list]
    combined = 1
    for odd in decimal_odds:
        combined *= odd
    return decimal_to_american(combined)


def vig_calculator(odds1: float, odds2: float) -> float:
    """Calculate bookmaker's vig"""
    prob1 = implied_probability(odds1)
    prob2 = implied_probability(odds2)
    total = prob1 + prob2
    vig = total - 1
    return vig * 100


def format_odds(odds: float) -> str:
    """Format odds with + sign for positive"""
    if odds > 0:
        return f"+{int(odds)}"
    return f"{int(odds)}"


def cmd_convert(args):
    """Convert between odds formats"""
    odds = args.odds
    decimal = american_to_decimal(odds)
    prob = implied_probability(odds)

    print(f"\nOdds Conversion for {format_odds(odds)}")
    print("=" * 40)
    print(f"American:  {format_odds(odds)}")
    print(f"Decimal:   {decimal:.3f}")
    print(f"Fractional: {decimal - 1:.2f}/1")
    print(f"Implied Probability: {prob * 100:.2f}%")
    print(f"Break-even Win Rate: {prob * 100:.2f}%")


def cmd_payout(args):
    """Calculate potential payout"""
    stake = args.stake
    odds = args.odds
    profit, total_return = calculate_payout(stake, odds)

    print(f"\nPayout Calculator")
    print("=" * 40)
    print(f"Stake:     ${stake:.2f}")
    print(f"Odds:      {format_odds(odds)}")
    print(f"Profit:    ${profit:.2f}")
    print(f"Total Return: ${total_return:.2f}")
    print(f"ROI: {(profit / stake) * 100:.2f}%")


def cmd_kelly(args):
    """Calculate Kelly criterion bet size"""
    true_prob = args.prob
    odds = args.odds
    bankroll = args.bankroll

    kelly = kelly_criterion(true_prob, odds)
    full_kelly = bankroll * kelly
    half_kelly = full_kelly * 0.5
    quarter_kelly = full_kelly * 0.25

    market_prob = implied_probability(odds)
    edge = true_prob - market_prob

    print(f"\nKelly Criterion Calculator")
    print("=" * 40)
    print(f"Your Probability: {true_prob * 100:.2f}%")
    print(f"Market Probability: {market_prob * 100:.2f}%")
    print(f"Your Edge: {edge * 100:+.2f}%")
    print(f"Bankroll: ${bankroll:.2f}")
    print()
    print(f"Full Kelly: {kelly * 100:.2f}% (${full_kelly:.2f})")
    print(f"Half Kelly: {kelly * 50:.2f}% (${half_kelly:.2f})")
    print(f"Quarter Kelly: {kelly * 25:.2f}% (${quarter_kelly:.2f})")

    if kelly <= 0:
        print("\n⚠️  No edge - do not bet!")
    elif kelly > 0.1:
        print("\n⚠️  Large Kelly % - consider fractional Kelly for safety")


def cmd_ev(args):
    """Calculate expected value"""
    true_prob = args.prob
    odds = args.odds
    stake = args.stake

    ev = calculate_ev(true_prob, odds, stake)
    ev_percentage = (ev / stake) * 100
    market_prob = implied_probability(odds)

    print(f"\nExpected Value Calculator")
    print("=" * 40)
    print(f"Your Probability: {true_prob * 100:.2f}%")
    print(f"Market Probability: {market_prob * 100:.2f}%")
    print(f"Odds: {format_odds(odds)}")
    print(f"Stake: ${stake:.2f}")
    print()
    print(f"Expected Value: ${ev:+.2f}")
    print(f"EV Percentage: {ev_percentage:+.2f}%")

    if ev > 0:
        print("\n✓ Positive EV - good bet!")
    else:
        print("\n✗ Negative EV - avoid this bet")


def cmd_parlay(args):
    """Calculate parlay odds and payout"""
    odds_list = args.odds
    stake = args.stake

    combined_odds = parlay_odds(*odds_list)
    decimal_combined = american_to_decimal(combined_odds)

    # Calculate individual probabilities
    probs = [implied_probability(o) for o in odds_list]
    combined_prob = 1
    for p in probs:
        combined_prob *= p

    profit, total_return = calculate_payout(stake, combined_odds)

    print(f"\nParlay Calculator")
    print("=" * 40)
    print(f"Number of legs: {len(odds_list)}")
    for i, odds in enumerate(odds_list, 1):
        print(f"  Leg {i}: {format_odds(odds)} ({implied_probability(odds) * 100:.1f}%)")

    print()
    print(f"Combined Odds: {format_odds(combined_odds)}")
    print(f"Combined Probability: {combined_prob * 100:.2f}%")
    print(f"Stake: ${stake:.2f}")
    print(f"Potential Profit: ${profit:.2f}")
    print(f"Total Return: ${total_return:.2f}")
    print(f"Potential ROI: {(profit / stake) * 100:.2f}%")


def cmd_vig(args):
    """Calculate bookmaker's vig"""
    odds1 = args.odds1
    odds2 = args.odds2

    vig = vig_calculator(odds1, odds2)
    prob1 = implied_probability(odds1)
    prob2 = implied_probability(odds2)

    # Calculate fair odds (no vig)
    total_prob = prob1 + prob2
    fair_prob1 = prob1 / total_prob
    fair_prob2 = prob2 / total_prob

    if fair_prob1 >= 0.5:
        fair_odds1 = -100 * fair_prob1 / (1 - fair_prob1)
        fair_odds2 = 100 * (1 - fair_prob2) / fair_prob2
    else:
        fair_odds1 = 100 * (1 - fair_prob1) / fair_prob1
        fair_odds2 = -100 * fair_prob2 / (1 - fair_prob2)

    print(f"\nVig Calculator")
    print("=" * 40)
    print(f"Side A: {format_odds(odds1)} ({prob1 * 100:.2f}%)")
    print(f"Side B: {format_odds(odds2)} ({prob2 * 100:.2f}%)")
    print(f"Total: {total_prob * 100:.2f}%")
    print()
    print(f"Vig: {vig:.2f}%")
    print()
    print("Fair Odds (no vig):")
    print(f"  Side A: {format_odds(fair_odds1)}")
    print(f"  Side B: {format_odds(fair_odds2)}")


def main():
    parser = argparse.ArgumentParser(
        description='Quick Odds Calculator for Sports Betting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s convert -110
  %(prog)s payout -110 -s 100
  %(prog)s kelly -p 0.55 -o -110 -b 1000
  %(prog)s ev -p 0.55 -o -110 -s 100
  %(prog)s parlay -110 -120 +150 -s 50
  %(prog)s vig -110 -110
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Calculator mode')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert odds formats')
    convert_parser.add_argument('odds', type=float, help='American odds')

    # Payout command
    payout_parser = subparsers.add_parser('payout', help='Calculate payout')
    payout_parser.add_argument('odds', type=float, help='American odds')
    payout_parser.add_argument('-s', '--stake', type=float, default=100, help='Stake amount')

    # Kelly command
    kelly_parser = subparsers.add_parser('kelly', help='Kelly criterion')
    kelly_parser.add_argument('-p', '--prob', type=float, required=True, help='True probability (0-1)')
    kelly_parser.add_argument('-o', '--odds', type=float, required=True, help='American odds')
    kelly_parser.add_argument('-b', '--bankroll', type=float, required=True, help='Total bankroll')

    # EV command
    ev_parser = subparsers.add_parser('ev', help='Expected value')
    ev_parser.add_argument('-p', '--prob', type=float, required=True, help='True probability (0-1)')
    ev_parser.add_argument('-o', '--odds', type=float, required=True, help='American odds')
    ev_parser.add_argument('-s', '--stake', type=float, default=100, help='Stake amount')

    # Parlay command
    parlay_parser = subparsers.add_parser('parlay', help='Parlay calculator')
    parlay_parser.add_argument('odds', type=float, nargs='+', help='American odds for each leg')
    parlay_parser.add_argument('-s', '--stake', type=float, default=100, help='Stake amount')

    # Vig command
    vig_parser = subparsers.add_parser('vig', help='Calculate vig')
    vig_parser.add_argument('odds1', type=float, help='Odds for side A')
    vig_parser.add_argument('odds2', type=float, help='Odds for side B')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate command
    commands = {
        'convert': cmd_convert,
        'payout': cmd_payout,
        'kelly': cmd_kelly,
        'ev': cmd_ev,
        'parlay': cmd_parlay,
        'vig': cmd_vig
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
