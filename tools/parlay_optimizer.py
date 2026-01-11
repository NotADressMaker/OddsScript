#!/usr/bin/env python3
"""
Intelligent Parlay Optimizer

Build optimal parlays by selecting bets based on edge, correlation, and EV.
Avoids common parlay mistakes like correlated legs and low-edge selections.
"""

import argparse
import itertools
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Bet:
    """Represents a single betting opportunity"""
    id: str
    description: str
    odds: float  # American odds
    true_prob: float  # Your true probability (0-1)
    game_id: str  # For correlation detection
    bet_type: str  # "moneyline", "spread", "total", etc.


class ParlayOptimizer:
    """Optimize parlay construction"""

    @staticmethod
    def american_to_decimal(odds: float) -> float:
        """Convert American to decimal odds"""
        if odds > 0:
            return (odds / 100) + 1
        else:
            return (100 / abs(odds)) + 1

    @staticmethod
    def calculate_edge(bet: Bet) -> float:
        """Calculate edge for a bet"""
        decimal_odds = ParlayOptimizer.american_to_decimal(bet.odds)
        implied_prob = 1 / decimal_odds
        return bet.true_prob - implied_prob

    @staticmethod
    def calculate_ev(bet: Bet, stake: float = 100) -> float:
        """Calculate expected value"""
        decimal_odds = ParlayOptimizer.american_to_decimal(bet.odds)
        return (bet.true_prob * (decimal_odds - 1) * stake) - ((1 - bet.true_prob) * stake)

    @staticmethod
    def calculate_parlay_odds(bets: List[Bet]) -> float:
        """Calculate parlay odds (American)"""
        decimal_product = 1.0
        for bet in bets:
            decimal_product *= ParlayOptimizer.american_to_decimal(bet.odds)

        if decimal_product >= 2.0:
            return (decimal_product - 1) * 100
        else:
            return -100 / (decimal_product - 1)

    @staticmethod
    def calculate_parlay_true_prob(bets: List[Bet]) -> float:
        """Calculate true probability of parlay hitting"""
        prob = 1.0
        for bet in bets:
            prob *= bet.true_prob
        return prob

    @staticmethod
    def detect_correlation(bet1: Bet, bet2: Bet) -> float:
        """
        Estimate correlation between two bets

        Returns correlation coefficient (0 = none, 1 = perfect)
        """
        # Same game = potential correlation
        if bet1.game_id == bet2.game_id:
            # High correlation if same game, different types
            if bet1.bet_type == "moneyline" and bet2.bet_type == "spread":
                return 0.85
            elif bet1.bet_type in ["moneyline", "spread"] and bet2.bet_type == "total":
                return 0.20
            else:
                return 0.30  # Generic same-game correlation

        return 0.0  # Different games = no correlation

    @staticmethod
    def score_parlay(bets: List[Bet], weights: Dict[str, float] = None) -> Dict:
        """
        Score a parlay combination

        Args:
            bets: List of bets in parlay
            weights: Scoring weights for different factors

        Returns:
            Score dictionary
        """
        if weights is None:
            weights = {
                'edge': 1.0,
                'ev': 0.5,
                'correlation_penalty': -2.0,
                'leg_count_bonus': 0.1
            }

        # Calculate parlay metrics
        parlay_odds = ParlayOptimizer.calculate_parlay_odds(bets)
        parlay_true_prob = ParlayOptimizer.calculate_parlay_true_prob(bets)
        parlay_decimal = ParlayOptimizer.american_to_decimal(parlay_odds)
        parlay_implied_prob = 1 / parlay_decimal
        parlay_edge = parlay_true_prob - parlay_implied_prob
        parlay_ev = (parlay_true_prob * (parlay_decimal - 1) * 100) - ((1 - parlay_true_prob) * 100)

        # Calculate individual bet edges
        avg_edge = sum(ParlayOptimizer.calculate_edge(bet) for bet in bets) / len(bets)
        min_edge = min(ParlayOptimizer.calculate_edge(bet) for bet in bets)

        # Check for correlations
        max_correlation = 0
        total_correlation = 0
        correlation_count = 0

        for i in range(len(bets)):
            for j in range(i + 1, len(bets)):
                corr = ParlayOptimizer.detect_correlation(bets[i], bets[j])
                max_correlation = max(max_correlation, corr)
                total_correlation += corr
                correlation_count += 1

        avg_correlation = total_correlation / correlation_count if correlation_count > 0 else 0

        # Calculate composite score
        score = (
            parlay_edge * weights['edge'] +
            parlay_ev * weights['ev'] / 100 +
            avg_correlation * weights['correlation_penalty'] +
            len(bets) * weights['leg_count_bonus']
        )

        return {
            'score': score,
            'bets': bets,
            'num_legs': len(bets),
            'parlay_odds': parlay_odds,
            'parlay_true_prob': parlay_true_prob,
            'parlay_edge': parlay_edge,
            'parlay_ev': parlay_ev,
            'avg_edge': avg_edge,
            'min_edge': min_edge,
            'max_correlation': max_correlation,
            'avg_correlation': avg_correlation,
            'has_correlation_issue': max_correlation > 0.5
        }

    @staticmethod
    def find_optimal_parlays(
        bets: List[Bet],
        min_legs: int = 2,
        max_legs: int = 4,
        min_edge_per_leg: float = 0.02,
        max_correlation: float = 0.3,
        top_n: int = 10
    ) -> List[Dict]:
        """
        Find optimal parlay combinations

        Args:
            bets: Available bets
            min_legs: Minimum number of legs
            max_legs: Maximum number of legs
            min_edge_per_leg: Minimum edge required per bet
            max_correlation: Maximum allowed correlation
            top_n: Number of top parlays to return

        Returns:
            List of top scoring parlays
        """
        # Filter bets by edge
        qualifying_bets = [b for b in bets if ParlayOptimizer.calculate_edge(b) >= min_edge_per_leg]

        if len(qualifying_bets) < min_legs:
            return []

        all_parlays = []

        # Generate all possible combinations
        for leg_count in range(min_legs, min(max_legs + 1, len(qualifying_bets) + 1)):
            for combo in itertools.combinations(qualifying_bets, leg_count):
                parlay = ParlayOptimizer.score_parlay(list(combo))

                # Filter by correlation
                if parlay['max_correlation'] <= max_correlation:
                    all_parlays.append(parlay)

        # Sort by score
        all_parlays.sort(key=lambda x: x['score'], reverse=True)

        return all_parlays[:top_n]


def print_parlay_analysis(parlay: Dict, rank: int = None):
    """Print parlay analysis"""
    header = f"PARLAY #{rank}" if rank else "PARLAY ANALYSIS"

    print(f"\n{'='*80}")
    print(f"{header}")
    print(f"{'='*80}")

    print(f"\n📊 Parlay Metrics:")
    print(f"  Legs: {parlay['num_legs']}")
    print(f"  Parlay Odds: {parlay['parlay_odds']:+.0f}")
    print(f"  True Probability: {parlay['parlay_true_prob']*100:.2f}%")
    print(f"  Parlay Edge: {parlay['parlay_edge']*100:+.2f}%")
    print(f"  Expected Value (per $100): ${parlay['parlay_ev']:+.2f}")
    print(f"  Composite Score: {parlay['score']:.3f}")

    print(f"\n🎯 Individual Bets:")
    print(f"  {'Description':<35} {'Odds':<10} {'True%':<10} {'Edge':<10}")
    print(f"  {'-'*70}")

    for bet in parlay['bets']:
        edge = ParlayOptimizer.calculate_edge(bet)
        print(f"  {bet.description:<35} {bet.odds:>+8.0f}  "
              f"{bet.true_prob*100:>7.2f}%  {edge*100:>+7.2f}%")

    print(f"\n📈 Quality Metrics:")
    print(f"  Average Edge per Leg: {parlay['avg_edge']*100:+.2f}%")
    print(f"  Minimum Edge: {parlay['min_edge']*100:+.2f}%")
    print(f"  Max Correlation: {parlay['max_correlation']:.2f}")
    print(f"  Avg Correlation: {parlay['avg_correlation']:.2f}")

    if parlay['has_correlation_issue']:
        print(f"\n⚠️  WARNING: High correlation detected (>{0.5})")
        print(f"  Consider removing correlated legs")
    else:
        print(f"\n✓ Correlation acceptable")

    print(f"\n{'='*80}")


def main():
    parser = argparse.ArgumentParser(
        description='Intelligent Parlay Optimizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find optimal 2-4 leg parlays
  %(prog)s optimize \
    --bet "Chiefs -3" -110 0.55 game1 spread \
    --bet "Lakers ML" -150 0.68 game2 moneyline \
    --bet "Over 48.5" -110 0.52 game3 total \
    --bet "Celtics +5" +105 0.50 game4 spread

  # Stricter correlation limit
  %(prog)s optimize \
    --bet "Team A ML" -110 0.54 g1 moneyline \
    --bet "Team A -3" -110 0.52 g1 spread \
    --bet "Team B ML" +150 0.45 g2 moneyline \
    --max-correlation 0.2

  # Focus on 3-leg parlays only
  %(prog)s optimize \
    --bet "Bet 1" -110 0.55 g1 spread \
    --bet "Bet 2" +120 0.48 g2 moneyline \
    --bet "Bet 3" -105 0.53 g3 total \
    --bet "Bet 4" -110 0.54 g4 spread \
    --min-legs 3 --max-legs 3

Bet Format: DESCRIPTION ODDS TRUE_PROB GAME_ID BET_TYPE
  - TRUE_PROB: Your estimated win probability (0-1)
  - GAME_ID: Unique identifier for the game (for correlation detection)
  - BET_TYPE: moneyline, spread, total, prop, etc.
        """
    )

    subparsers = parser.add_subparsers(dest='command')

    optimize_parser = subparsers.add_parser('optimize', help='Find optimal parlays')
    optimize_parser.add_argument('--bet', nargs=5, action='append',
                                metavar=('DESC', 'ODDS', 'PROB', 'GAME', 'TYPE'),
                                help='Add bet: description odds true_prob game_id bet_type')
    optimize_parser.add_argument('--min-legs', type=int, default=2,
                                help='Minimum legs (default: 2)')
    optimize_parser.add_argument('--max-legs', type=int, default=4,
                                help='Maximum legs (default: 4)')
    optimize_parser.add_argument('--min-edge', type=float, default=0.02,
                                help='Minimum edge per leg (default: 0.02)')
    optimize_parser.add_argument('--max-correlation', type=float, default=0.3,
                                help='Maximum correlation (default: 0.3)')
    optimize_parser.add_argument('--top-n', type=int, default=5,
                                help='Number of top parlays to show (default: 5)')

    args = parser.parse_args()

    if args.command == 'optimize':
        if not args.bet or len(args.bet) < args.min_legs:
            print(f"Error: Need at least {args.min_legs} bets")
            return

        # Parse bets
        bets = []
        for i, bet_data in enumerate(args.bet):
            desc, odds, prob, game, bet_type = bet_data
            bets.append(Bet(
                id=f"bet{i}",
                description=desc,
                odds=float(odds),
                true_prob=float(prob),
                game_id=game,
                bet_type=bet_type
            ))

        # Find optimal parlays
        optimal_parlays = ParlayOptimizer.find_optimal_parlays(
            bets,
            min_legs=args.min_legs,
            max_legs=args.max_legs,
            min_edge_per_leg=args.min_edge,
            max_correlation=args.max_correlation,
            top_n=args.top_n
        )

        if not optimal_parlays:
            print("\n❌ No qualifying parlays found with specified criteria")
            print("\nTry adjusting:")
            print("  - Lower --min-edge")
            print("  - Increase --max-correlation")
            print("  - Reduce --min-legs")
            return

        print(f"\n🏆 Found {len(optimal_parlays)} optimal parlay(s):\n")

        for i, parlay in enumerate(optimal_parlays, 1):
            print_parlay_analysis(parlay, rank=i)

        # Summary
        best = optimal_parlays[0]
        print(f"\n💡 RECOMMENDATION:")
        print(f"  Best Parlay: {best['num_legs']}-leg parlay")
        print(f"  Expected Value: ${best['parlay_ev']:+.2f} per $100")
        print(f"  Edge: {best['parlay_edge']*100:+.2f}%")
        print(f"  Parlay Odds: {best['parlay_odds']:+.0f}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
