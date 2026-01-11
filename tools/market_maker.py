#!/usr/bin/env python3
"""
Market Maker Tool

Calculate fair odds, remove vig, and set profitable betting lines.
Useful for understanding true probabilities and identifying value.
"""

import argparse
from typing import List, Dict, Tuple, Optional
import math


class MarketMaker:
    """Tools for market making and fair odds calculation"""

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
    def probability_to_american(prob: float) -> float:
        """Convert probability to American odds"""
        decimal = 1 / prob
        return MarketMaker.decimal_to_american(decimal)

    @staticmethod
    def calculate_vig(odds_list: List[float], american: bool = True) -> Dict:
        """
        Calculate bookmaker's vig/overround

        Args:
            odds_list: List of odds for all outcomes in market
            american: Whether odds are in American format

        Returns:
            Dictionary with vig analysis
        """
        # Convert to decimal
        if american:
            decimal_odds = [MarketMaker.american_to_decimal(o) for o in odds_list]
        else:
            decimal_odds = odds_list

        # Calculate implied probabilities
        implied_probs = [1 / d for d in decimal_odds]

        # Total probability (overround)
        total_prob = sum(implied_probs)

        # Vig percentage
        vig = (total_prob - 1) * 100

        # Individual prob with vig
        probs_with_vig = implied_probs

        # Fair probabilities (proportional method)
        fair_probs = [p / total_prob for p in implied_probs]

        # Fair odds
        fair_decimal = [1 / p for p in fair_probs]
        fair_american = [MarketMaker.decimal_to_american(d) for d in fair_decimal]

        return {
            'vig_percentage': vig,
            'total_probability': total_prob * 100,
            'implied_probabilities': probs_with_vig,
            'fair_probabilities': fair_probs,
            'original_odds_american': odds_list if american else [MarketMaker.decimal_to_american(d) for d in odds_list],
            'fair_odds_american': fair_american,
            'original_odds_decimal': decimal_odds,
            'fair_odds_decimal': fair_decimal
        }

    @staticmethod
    def remove_vig_power(odds_list: List[float], american: bool = True) -> Dict:
        """
        Remove vig using power method (multiplicative)

        This method is more accurate for markets with unequal probabilities.

        Args:
            odds_list: List of odds
            american: Whether odds are American format

        Returns:
            No-vig odds and probabilities
        """
        if american:
            decimal_odds = [MarketMaker.american_to_decimal(o) for o in odds_list]
        else:
            decimal_odds = odds_list

        implied_probs = [1 / d for d in decimal_odds]
        total_prob = sum(implied_probs)

        # Power method: p_fair = p_implied^(1/n) / sum(p_implied^(1/n))
        n = len(implied_probs)
        power_adjusted = [p ** (1/n) for p in implied_probs]
        sum_power = sum(power_adjusted)

        fair_probs = [p / sum_power for p in power_adjusted]
        fair_decimal = [1 / p for p in fair_probs]
        fair_american = [MarketMaker.decimal_to_american(d) for d in fair_decimal]

        return {
            'method': 'Power Method',
            'fair_probabilities': fair_probs,
            'fair_odds_decimal': fair_decimal,
            'fair_odds_american': fair_american
        }

    @staticmethod
    def set_odds_with_margin(
        true_probs: List[float],
        target_margin: float = 5.0
    ) -> Dict:
        """
        Set betting odds with a target profit margin

        Args:
            true_probs: List of true probabilities (must sum to 1.0)
            target_margin: Desired profit margin percentage (default 5%)

        Returns:
            Odds with margin built in
        """
        # Validate probabilities
        if abs(sum(true_probs) - 1.0) > 0.001:
            raise ValueError("Probabilities must sum to 1.0")

        # Add margin proportionally
        margin_multiplier = 1 + (target_margin / 100)

        # Adjust probabilities to include margin
        adjusted_probs = [p * margin_multiplier for p in true_probs]

        # Convert to odds
        decimal_odds = [1 / p for p in adjusted_probs]
        american_odds = [MarketMaker.decimal_to_american(d) for d in decimal_odds]

        # Calculate actual margin
        actual_margin = (sum(adjusted_probs) - 1) * 100

        return {
            'true_probabilities': true_probs,
            'target_margin': target_margin,
            'actual_margin': actual_margin,
            'adjusted_probabilities': adjusted_probs,
            'decimal_odds': decimal_odds,
            'american_odds': american_odds,
            'total_probability': sum(adjusted_probs) * 100
        }

    @staticmethod
    def find_value_bets(
        market_odds: List[Tuple[str, float]],
        true_probs: List[float],
        min_edge: float = 0.05
    ) -> List[Dict]:
        """
        Find value bets by comparing market odds to true probabilities

        Args:
            market_odds: List of (outcome_name, odds) tuples
            true_probs: List of true probabilities for each outcome
            min_edge: Minimum edge required to flag as value

        Returns:
            List of value betting opportunities
        """
        value_bets = []

        for i, (name, odds) in enumerate(market_odds):
            decimal = MarketMaker.american_to_decimal(odds)
            implied_prob = 1 / decimal
            true_prob = true_probs[i]

            edge = true_prob - implied_prob
            edge_pct = (edge / implied_prob) * 100

            if edge >= min_edge:
                # Calculate EV for $100 bet
                ev = (true_prob * (decimal - 1) * 100) - ((1 - true_prob) * 100)

                value_bets.append({
                    'outcome': name,
                    'market_odds': odds,
                    'implied_probability': implied_prob,
                    'true_probability': true_prob,
                    'edge': edge,
                    'edge_percentage': edge_pct,
                    'ev_per_100': ev
                })

        return sorted(value_bets, key=lambda x: x['edge'], reverse=True)

    @staticmethod
    def calculate_spread_odds(
        win_probability: float,
        target_margin: float = 4.55  # Standard -110/-110 margin
    ) -> Dict:
        """
        Calculate spread odds for a given win probability

        Args:
            win_probability: Probability of covering spread
            target_margin: Target vig (default 4.55% for -110/-110)

        Returns:
            Spread odds for both sides
        """
        # For spread, probabilities should be complementary
        lose_probability = 1 - win_probability

        # Set odds with margin
        result = MarketMaker.set_odds_with_margin(
            [win_probability, lose_probability],
            target_margin
        )

        return {
            'favorite_odds': result['american_odds'][0],
            'underdog_odds': result['american_odds'][1],
            'favorite_probability': win_probability,
            'underdog_probability': lose_probability,
            'margin': result['actual_margin']
        }

    @staticmethod
    def moneyline_to_spread(
        favorite_ml: float,
        points_per_unit: float = 4.0
    ) -> float:
        """
        Convert moneyline to approximate point spread

        Args:
            favorite_ml: Favorite's moneyline odds (negative)
            points_per_unit: Points per unit of odds (sport-specific)

        Returns:
            Approximate point spread
        """
        if favorite_ml >= 0:
            raise ValueError("Favorite moneyline must be negative")

        # Convert to decimal
        decimal = MarketMaker.american_to_decimal(favorite_ml)
        implied_prob = 1 / decimal

        # Rough conversion: each 0.1 probability ≈ 2-4 points
        prob_over_50 = implied_prob - 0.5
        spread = prob_over_50 * points_per_unit * 10

        return round(spread * 2) / 2  # Round to nearest 0.5


def print_vig_analysis(result: Dict):
    """Print vig analysis results"""
    print(f"\n{'='*70}")
    print(f"VIG/OVERROUND ANALYSIS")
    print(f"{'='*70}")

    print(f"\nMarket Summary:")
    print(f"  Vig/Overround: {result['vig_percentage']:.2f}%")
    print(f"  Total Probability: {result['total_probability']:.2f}%")

    print(f"\n{'Outcome':<10} {'Market Odds':<15} {'Fair Odds':<15} {'Implied%':<12} {'Fair%':<12}")
    print(f"{'-'*70}")

    num_outcomes = len(result['original_odds_american'])
    for i in range(num_outcomes):
        market_odds = result['original_odds_american'][i]
        fair_odds = result['fair_odds_american'][i]
        implied_prob = result['implied_probabilities'][i] * 100
        fair_prob = result['fair_probabilities'][i] * 100

        print(f"Out #{i+1:<5} {market_odds:>+8.0f}      {fair_odds:>+8.0f}      "
              f"{implied_prob:>7.2f}%     {fair_prob:>7.2f}%")

    print(f"\n{'='*70}")


def print_value_bets(value_bets: List[Dict]):
    """Print value betting opportunities"""
    print(f"\n{'='*70}")
    print(f"VALUE BETTING OPPORTUNITIES")
    print(f"{'='*70}")

    if not value_bets:
        print(f"\n❌ No value bets found with specified criteria")
        print(f"\n{'='*70}")
        return

    print(f"\n✅ {len(value_bets)} value bet(s) found!\n")

    print(f"{'Outcome':<20} {'Odds':<10} {'Implied%':<12} {'True%':<12} {'Edge':<10} {'EV/100':<10}")
    print(f"{'-'*70}")

    for vb in value_bets:
        print(f"{vb['outcome']:<20} {vb['market_odds']:>+8.0f}  "
              f"{vb['implied_probability']*100:>7.2f}%    "
              f"{vb['true_probability']*100:>7.2f}%    "
              f"{vb['edge']*100:>+6.2f}%   "
              f"${vb['ev_per_100']:>+7.2f}")

    print(f"\n{'='*70}")


def main():
    parser = argparse.ArgumentParser(
        description='Market Maker Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate vig for a two-way market
  %(prog)s vig -110 -110

  # Calculate vig for three-way market (soccer)
  %(prog)s vig +180 +220 +150

  # Set odds with 5% margin
  %(prog)s set-odds --probs 0.55 0.45 --margin 5

  # Find value bets
  %(prog)s value --market "Team A" +150 --market "Team B" -170 \
    --true-probs 0.45 0.55 --min-edge 0.03

  # Calculate spread odds
  %(prog)s spread --prob 0.55 --margin 4.55

  # Convert moneyline to spread
  %(prog)s ml-to-spread -180
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command')

    # Vig calculator
    vig_parser = subparsers.add_parser('vig', help='Calculate vig/overround')
    vig_parser.add_argument('odds', nargs='+', type=float,
                           help='Odds for all outcomes (American format)')

    # Set odds with margin
    set_parser = subparsers.add_parser('set-odds', help='Set odds with target margin')
    set_parser.add_argument('--probs', nargs='+', type=float, required=True,
                           help='True probabilities (must sum to 1.0)')
    set_parser.add_argument('--margin', type=float, default=5.0,
                           help='Target profit margin percentage (default: 5)')

    # Find value
    value_parser = subparsers.add_parser('value', help='Find value bets')
    value_parser.add_argument('--market', nargs=2, action='append',
                             metavar=('NAME', 'ODDS'),
                             help='Market odds: name odds (e.g., "TeamA" -110)')
    value_parser.add_argument('--true-probs', nargs='+', type=float, required=True,
                             help='True probabilities for each outcome')
    value_parser.add_argument('--min-edge', type=float, default=0.05,
                             help='Minimum edge to flag (default: 0.05)')

    # Spread odds
    spread_parser = subparsers.add_parser('spread', help='Calculate spread odds')
    spread_parser.add_argument('--prob', type=float, required=True,
                              help='Win probability (0-1)')
    spread_parser.add_argument('--margin', type=float, default=4.55,
                              help='Target margin (default: 4.55 for -110/-110)')

    # ML to spread
    ml_parser = subparsers.add_parser('ml-to-spread', help='Convert moneyline to spread')
    ml_parser.add_argument('moneyline', type=float,
                          help='Favorite moneyline (negative)')
    ml_parser.add_argument('--points-per-unit', type=float, default=4.0,
                          help='Points per unit (default: 4.0 for NFL)')

    args = parser.parse_args()

    if args.command == 'vig':
        result = MarketMaker.calculate_vig(args.odds, american=True)
        print_vig_analysis(result)

    elif args.command == 'set-odds':
        try:
            result = MarketMaker.set_odds_with_margin(args.probs, args.margin)

            print(f"\n{'='*70}")
            print(f"SET ODDS WITH MARGIN")
            print(f"{'='*70}")

            print(f"\nTarget Margin: {result['target_margin']:.2f}%")
            print(f"Actual Margin: {result['actual_margin']:.2f}%")
            print(f"Total Probability: {result['total_probability']:.2f}%")

            print(f"\n{'Outcome':<12} {'True Prob':<12} {'Adj Prob':<12} {'Decimal':<10} {'American':<10}")
            print(f"{'-'*70}")

            for i in range(len(result['true_probabilities'])):
                print(f"Outcome {i+1:<3} {result['true_probabilities'][i]:>8.4f}    "
                      f"{result['adjusted_probabilities'][i]:>8.4f}    "
                      f"{result['decimal_odds'][i]:>6.3f}    "
                      f"{result['american_odds'][i]:>+8.0f}")

            print(f"\n{'='*70}")

        except ValueError as e:
            print(f"Error: {e}")

    elif args.command == 'value':
        if not args.market:
            parser.error("--market required")

        market_odds = [(name, float(odds)) for name, odds in args.market]
        value_bets = MarketMaker.find_value_bets(
            market_odds,
            args.true_probs,
            args.min_edge
        )

        print_value_bets(value_bets)

    elif args.command == 'spread':
        result = MarketMaker.calculate_spread_odds(args.prob, args.margin)

        print(f"\n{'='*70}")
        print(f"SPREAD ODDS CALCULATOR")
        print(f"{'='*70}")

        print(f"\nWin Probability: {result['favorite_probability']:.2%}")
        print(f"Target Margin: {result['margin']:.2f}%")

        print(f"\nRecommended Odds:")
        print(f"  Favorite: {result['favorite_odds']:+.0f}")
        print(f"  Underdog: {result['underdog_odds']:+.0f}")

        print(f"\n{'='*70}")

    elif args.command == 'ml-to-spread':
        spread = MarketMaker.moneyline_to_spread(
            args.moneyline,
            args.points_per_unit
        )

        print(f"\n{'='*70}")
        print(f"MONEYLINE TO SPREAD CONVERTER")
        print(f"{'='*70}")

        print(f"\nFavorite Moneyline: {args.moneyline:+.0f}")
        print(f"Approximate Spread: {spread:+.1f}")

        print(f"\n(Using {args.points_per_unit} points per unit)")
        print(f"\n{'='*70}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
