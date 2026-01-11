#!/usr/bin/env python3
"""
Portfolio Optimizer for Sports Betting

Optimize bet allocation across multiple games using mathematical optimization.
Based on Modern Portfolio Theory adapted for sports betting.
"""

import argparse
from typing import List, Tuple, Dict
import math


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal"""
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


def implied_probability(odds: float) -> float:
    """Calculate implied probability"""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


class PortfolioOptimizer:
    """
    Optimize bet allocation across multiple opportunities

    Uses Kelly Criterion adjusted for portfolio optimization
    """

    def __init__(self, bankroll: float, max_allocation: float = 0.10):
        """
        Initialize optimizer

        Args:
            bankroll: Total bankroll
            max_allocation: Maximum % of bankroll per bet (default 10%)
        """
        self.bankroll = bankroll
        self.max_allocation = max_allocation
        self.opportunities: List[Dict] = []

    def add_opportunity(
        self,
        name: str,
        true_prob: float,
        odds: float,
        correlation: float = 0.0
    ):
        """
        Add a betting opportunity

        Args:
            name: Name/description of bet
            true_prob: Your estimated win probability (0-1)
            odds: Market odds (American)
            correlation: Correlation with other bets (-1 to 1)
        """
        market_prob = implied_probability(odds)
        edge = true_prob - market_prob

        # Calculate Kelly percentage
        decimal_odds = american_to_decimal(odds)
        b = decimal_odds - 1
        p = true_prob
        q = 1 - p

        kelly = (b * p - q) / b
        kelly = max(0, kelly)  # No negative Kelly

        # Calculate expected value
        ev = p * (b * 1) - q * 1  # Per unit

        opportunity = {
            'name': name,
            'true_prob': true_prob,
            'odds': odds,
            'market_prob': market_prob,
            'edge': edge,
            'kelly': kelly,
            'ev': ev,
            'correlation': correlation,
            'decimal_odds': decimal_odds
        }

        self.opportunities.append(opportunity)

    def calculate_covariance(self, opp1: Dict, opp2: Dict) -> float:
        """Calculate covariance between two bets"""
        # Simplified covariance calculation
        # In reality, this would need more sophisticated modeling

        # Variance for each bet
        p1 = opp1['true_prob']
        p2 = opp2['true_prob']

        b1 = opp1['decimal_odds'] - 1
        b2 = opp2['decimal_odds'] - 1

        var1 = p1 * (b1 ** 2) + (1 - p1) * (1 ** 2) - (opp1['ev'] ** 2)
        var2 = p2 * (b2 ** 2) + (1 - p2) * (1 ** 2) - (opp2['ev'] ** 2)

        # Covariance = correlation * sqrt(var1) * sqrt(var2)
        correlation = opp1.get('correlation', 0)
        cov = correlation * math.sqrt(var1) * math.sqrt(var2)

        return cov

    def optimize_equal_edge(self) -> Dict:
        """
        Simple optimization: allocate equally among positive EV bets

        Returns:
            Dictionary with allocation recommendations
        """
        # Filter to positive EV bets only
        positive_ev = [opp for opp in self.opportunities if opp['ev'] > 0]

        if not positive_ev:
            return {
                'method': 'equal_edge',
                'allocations': [],
                'total_allocated': 0,
                'expected_return': 0
            }

        # Equal allocation
        allocation_per_bet = self.bankroll / len(positive_ev)

        # Cap at max allocation
        max_bet = self.bankroll * self.max_allocation
        allocation_per_bet = min(allocation_per_bet, max_bet)

        allocations = []
        total_allocated = 0
        expected_return = 0

        for opp in positive_ev:
            allocation = allocation_per_bet
            total_allocated += allocation
            expected_return += allocation * opp['ev']

            allocations.append({
                'name': opp['name'],
                'allocation': allocation,
                'percent': (allocation / self.bankroll) * 100,
                'odds': opp['odds'],
                'edge': opp['edge'],
                'expected_profit': allocation * opp['ev']
            })

        return {
            'method': 'equal_edge',
            'allocations': allocations,
            'total_allocated': total_allocated,
            'total_percent': (total_allocated / self.bankroll) * 100,
            'expected_return': expected_return,
            'expected_roi': (expected_return / total_allocated * 100) if total_allocated > 0 else 0
        }

    def optimize_kelly(self) -> Dict:
        """
        Kelly Criterion optimization for each bet independently

        Returns:
            Dictionary with Kelly allocations
        """
        allocations = []
        total_allocated = 0
        expected_return = 0

        for opp in self.opportunities:
            if opp['kelly'] > 0:
                # Use fractional Kelly for safety (1/4 Kelly)
                allocation = self.bankroll * opp['kelly'] * 0.25

                # Cap at max allocation
                max_bet = self.bankroll * self.max_allocation
                allocation = min(allocation, max_bet)

                total_allocated += allocation
                expected_return += allocation * opp['ev']

                allocations.append({
                    'name': opp['name'],
                    'allocation': allocation,
                    'percent': (allocation / self.bankroll) * 100,
                    'kelly_percent': opp['kelly'] * 100,
                    'fractional_kelly': 0.25,
                    'odds': opp['odds'],
                    'edge': opp['edge'],
                    'expected_profit': allocation * opp['ev']
                })

        # Sort by allocation
        allocations.sort(key=lambda x: x['allocation'], reverse=True)

        return {
            'method': 'kelly_criterion',
            'allocations': allocations,
            'total_allocated': total_allocated,
            'total_percent': (total_allocated / self.bankroll) * 100,
            'expected_return': expected_return,
            'expected_roi': (expected_return / total_allocated * 100) if total_allocated > 0 else 0
        }

    def optimize_ev_weighted(self) -> Dict:
        """
        EV-weighted allocation: allocate proportionally to expected value

        Returns:
            Dictionary with EV-weighted allocations
        """
        # Calculate total positive EV
        total_ev = sum(max(0, opp['ev']) for opp in self.opportunities)

        if total_ev <= 0:
            return {
                'method': 'ev_weighted',
                'allocations': [],
                'total_allocated': 0,
                'expected_return': 0
            }

        allocations = []
        total_allocated = 0
        expected_return = 0

        # Determine total budget (use 50% of bankroll for diversification)
        total_budget = self.bankroll * 0.5

        for opp in self.opportunities:
            if opp['ev'] > 0:
                # Allocate proportionally to EV
                weight = opp['ev'] / total_ev
                allocation = total_budget * weight

                # Cap at max allocation
                max_bet = self.bankroll * self.max_allocation
                allocation = min(allocation, max_bet)

                total_allocated += allocation
                expected_return += allocation * opp['ev']

                allocations.append({
                    'name': opp['name'],
                    'allocation': allocation,
                    'percent': (allocation / self.bankroll) * 100,
                    'ev_weight': weight * 100,
                    'odds': opp['odds'],
                    'edge': opp['edge'],
                    'expected_profit': allocation * opp['ev']
                })

        # Sort by allocation
        allocations.sort(key=lambda x: x['allocation'], reverse=True)

        return {
            'method': 'ev_weighted',
            'allocations': allocations,
            'total_allocated': total_allocated,
            'total_percent': (total_allocated / self.bankroll) * 100,
            'expected_return': expected_return,
            'expected_roi': (expected_return / total_allocated * 100) if total_allocated > 0 else 0
        }

    def optimize_sharpe(self) -> Dict:
        """
        Optimize for Sharpe ratio (risk-adjusted returns)

        Returns:
            Dictionary with Sharpe-optimized allocations
        """
        allocations = []
        total_allocated = 0
        expected_return = 0

        # Calculate Sharpe ratio for each opportunity
        sharpe_scores = []

        for opp in self.opportunities:
            if opp['ev'] > 0:
                # Calculate variance
                p = opp['true_prob']
                b = opp['decimal_odds'] - 1
                variance = p * (b ** 2) + (1 - p) * (1 ** 2) - (opp['ev'] ** 2)
                std_dev = math.sqrt(variance)

                # Sharpe ratio = EV / std_dev
                sharpe = opp['ev'] / std_dev if std_dev > 0 else 0

                sharpe_scores.append({
                    'opp': opp,
                    'sharpe': sharpe,
                    'std_dev': std_dev
                })

        # Sort by Sharpe ratio
        sharpe_scores.sort(key=lambda x: x['sharpe'], reverse=True)

        # Total Sharpe for weighting
        total_sharpe = sum(s['sharpe'] for s in sharpe_scores)

        if total_sharpe <= 0:
            return {
                'method': 'sharpe_optimized',
                'allocations': [],
                'total_allocated': 0,
                'expected_return': 0
            }

        # Allocate based on Sharpe ratio
        total_budget = self.bankroll * 0.5

        for item in sharpe_scores:
            opp = item['opp']
            weight = item['sharpe'] / total_sharpe
            allocation = total_budget * weight

            # Cap at max allocation
            max_bet = self.bankroll * self.max_allocation
            allocation = min(allocation, max_bet)

            total_allocated += allocation
            expected_return += allocation * opp['ev']

            allocations.append({
                'name': opp['name'],
                'allocation': allocation,
                'percent': (allocation / self.bankroll) * 100,
                'sharpe_ratio': item['sharpe'],
                'odds': opp['odds'],
                'edge': opp['edge'],
                'expected_profit': allocation * opp['ev']
            })

        return {
            'method': 'sharpe_optimized',
            'allocations': allocations,
            'total_allocated': total_allocated,
            'total_percent': (total_allocated / self.bankroll) * 100,
            'expected_return': expected_return,
            'expected_roi': (expected_return / total_allocated * 100) if total_allocated > 0 else 0
        }

    def compare_all_methods(self):
        """Compare all optimization methods"""
        methods = {
            'Kelly Criterion': self.optimize_kelly(),
            'EV Weighted': self.optimize_ev_weighted(),
            'Sharpe Optimized': self.optimize_sharpe(),
            'Equal Allocation': self.optimize_equal_edge()
        }

        print(f"\n{'='*80}")
        print(f"Portfolio Optimization Comparison")
        print(f"Bankroll: ${self.bankroll:.2f} | Opportunities: {len(self.opportunities)}")
        print(f"{'='*80}")

        # Print summary comparison
        print(f"\n{'Method':<20} {'Total Allocated':<18} {'Expected Return':<18} {'ROI':<10}")
        print(f"{'-'*80}")

        for name, result in methods.items():
            print(f"{name:<20} ${result['total_allocated']:<17.2f} "
                  f"${result['expected_return']:<17.2f} {result['expected_roi']:<9.2f}%")

        # Print detailed allocation for best method (highest expected return)
        best_method = max(methods.items(), key=lambda x: x[1]['expected_return'])

        print(f"\n{'='*80}")
        print(f"Recommended: {best_method[0]}")
        print(f"{'='*80}")

        result = best_method[1]

        if result['allocations']:
            print(f"\n{'Bet':<25} {'Allocation':<15} {'Percent':<10} {'Edge':<10} {'Exp Profit'}")
            print(f"{'-'*80}")

            for alloc in result['allocations']:
                print(f"{alloc['name']:<25} ${alloc['allocation']:<14.2f} "
                      f"{alloc['percent']:<9.2f}% {alloc['edge']*100:<9.2f}% "
                      f"${alloc['expected_profit']:+.2f}")

            print(f"\n{'Total':<25} ${result['total_allocated']:<14.2f} "
                  f"{result['total_percent']:<9.2f}%")
            print(f"\nExpected Return: ${result['expected_return']:+.2f}")
            print(f"Expected ROI: {result['expected_roi']:+.2f}%")
        else:
            print("\nNo positive EV opportunities found!")


def main():
    parser = argparse.ArgumentParser(
        description='Portfolio Optimizer for Sports Betting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s -b 5000 \\
    -o "Lakers -5" 0.58 -110 \\
    -o "Chiefs -3" 0.55 -120 \\
    -o "Over 220" 0.52 -110 \\
    --max-allocation 0.10

This will optimize bet allocation across 3 opportunities with a $5000 bankroll,
limiting each bet to 10%% of the bankroll.
        """
    )

    parser.add_argument('-b', '--bankroll', type=float, required=True,
                       help='Total bankroll')
    parser.add_argument('-o', '--opportunity', action='append', nargs=3,
                       metavar=('NAME', 'PROB', 'ODDS'),
                       help='Add opportunity: name, true_prob (0-1), odds')
    parser.add_argument('--max-allocation', type=float, default=0.10,
                       help='Max allocation per bet (default: 0.10 = 10%%)')
    parser.add_argument('-m', '--method',
                       choices=['kelly', 'ev', 'sharpe', 'equal', 'all'],
                       default='all',
                       help='Optimization method (default: all)')

    args = parser.parse_args()

    if not args.opportunity:
        print("Error: Add at least one opportunity with -o")
        return

    # Create optimizer
    optimizer = PortfolioOptimizer(args.bankroll, args.max_allocation)

    # Add opportunities
    for name, prob, odds in args.opportunity:
        optimizer.add_opportunity(name, float(prob), float(odds))

    # Run optimization
    if args.method == 'all':
        optimizer.compare_all_methods()
    elif args.method == 'kelly':
        result = optimizer.optimize_kelly()
        print_result(result, args.bankroll)
    elif args.method == 'ev':
        result = optimizer.optimize_ev_weighted()
        print_result(result, args.bankroll)
    elif args.method == 'sharpe':
        result = optimizer.optimize_sharpe()
        print_result(result, args.bankroll)
    elif args.method == 'equal':
        result = optimizer.optimize_equal_edge()
        print_result(result, args.bankroll)


def print_result(result: Dict, bankroll: float):
    """Print single optimization result"""
    print(f"\n{'='*70}")
    print(f"Optimization Method: {result['method'].replace('_', ' ').title()}")
    print(f"{'='*70}")

    if result['allocations']:
        print(f"\n{'Bet':<25} {'Allocation':<15} {'Percent':<10} {'Exp Profit'}")
        print(f"{'-'*70}")

        for alloc in result['allocations']:
            print(f"{alloc['name']:<25} ${alloc['allocation']:<14.2f} "
                  f"{alloc['percent']:<9.2f}% ${alloc['expected_profit']:+.2f}")

        print(f"\n{'Total':<25} ${result['total_allocated']:<14.2f} "
              f"{result['total_percent']:<9.2f}%")
        print(f"\nExpected Return: ${result['expected_return']:+.2f}")
        print(f"Expected ROI: {result['expected_roi']:+.2f}%")
    else:
        print("\nNo positive EV opportunities!")


if __name__ == '__main__':
    main()
