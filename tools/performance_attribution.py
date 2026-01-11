#!/usr/bin/env python3
"""
Performance Attribution Analyzer

Analyze betting performance across multiple dimensions to identify edge sources.
"""

import argparse
import csv
import json
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Optional
import math


class Bet:
    """Represents a single bet"""

    def __init__(self, data: Dict):
        self.date = datetime.strptime(data['date'], '%Y-%m-%d')
        self.sport = data['sport']
        self.bet_type = data['bet_type']  # moneyline, spread, total, prop, etc.
        self.odds = float(data['odds'])
        self.stake = float(data['stake'])
        self.result = data['result']  # win, loss, push
        self.book = data.get('book', 'unknown')
        self.clv = float(data.get('clv', 0))  # Closing line value
        self.description = data.get('description', '')

        # Calculate profit
        if self.result == 'win':
            if self.odds > 0:
                self.profit = self.stake * (self.odds / 100)
            else:
                self.profit = self.stake * (100 / abs(self.odds))
        elif self.result == 'loss':
            self.profit = -self.stake
        else:  # push
            self.profit = 0

        # ROI for this bet
        self.roi = (self.profit / self.stake * 100) if self.stake > 0 else 0

        # Calculate odds category
        if abs(self.odds) <= 110:
            self.odds_category = 'short'  # -110 to +110
        elif abs(self.odds) <= 200:
            self.odds_category = 'medium'  # -200 to +200
        else:
            self.odds_category = 'long'  # Longer than +200/-200


class PerformanceAttributionAnalyzer:
    """Analyze performance across multiple dimensions"""

    def __init__(self, bets: List[Bet]):
        self.bets = bets
        self.total_bets = len(bets)
        self.total_stake = sum(b.stake for b in bets)
        self.total_profit = sum(b.profit for b in bets)
        self.overall_roi = (self.total_profit / self.total_stake * 100) if self.total_stake > 0 else 0

    def analyze_by_dimension(self, dimension: str) -> Dict:
        """
        Analyze performance by a specific dimension

        Args:
            dimension: One of 'sport', 'bet_type', 'book', 'odds_category', 'clv_sign'

        Returns:
            Dictionary with performance by category
        """
        categories = defaultdict(lambda: {
            'bets': [],
            'count': 0,
            'wins': 0,
            'losses': 0,
            'pushes': 0,
            'total_stake': 0,
            'total_profit': 0,
            'roi': 0,
            'win_rate': 0
        })

        for bet in self.bets:
            if dimension == 'sport':
                key = bet.sport
            elif dimension == 'bet_type':
                key = bet.bet_type
            elif dimension == 'book':
                key = bet.book
            elif dimension == 'odds_category':
                key = bet.odds_category
            elif dimension == 'clv_sign':
                key = 'positive_clv' if bet.clv > 0 else 'negative_clv'
            else:
                continue

            categories[key]['bets'].append(bet)
            categories[key]['count'] += 1
            categories[key]['total_stake'] += bet.stake
            categories[key]['total_profit'] += bet.profit

            if bet.result == 'win':
                categories[key]['wins'] += 1
            elif bet.result == 'loss':
                categories[key]['losses'] += 1
            else:
                categories[key]['pushes'] += 1

        # Calculate metrics
        for key in categories:
            cat = categories[key]
            decided_bets = cat['wins'] + cat['losses']
            cat['win_rate'] = (cat['wins'] / decided_bets * 100) if decided_bets > 0 else 0
            cat['roi'] = (cat['total_profit'] / cat['total_stake'] * 100) if cat['total_stake'] > 0 else 0

        return dict(categories)

    def calculate_sharpe_ratio(self, bets: List[Bet]) -> float:
        """Calculate Sharpe ratio for risk-adjusted returns"""
        if len(bets) < 2:
            return 0

        rois = [b.roi for b in bets]
        avg_roi = sum(rois) / len(rois)

        variance = sum((roi - avg_roi) ** 2 for roi in rois) / len(rois)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0

        # Annualized Sharpe ratio (assuming ~260 betting days per year)
        sharpe = (avg_roi / std_dev) * math.sqrt(260)
        return sharpe

    def top_performers(self, dimension: str, metric: str = 'roi', top_n: int = 5) -> List[Dict]:
        """
        Get top performers by dimension

        Args:
            dimension: Dimension to analyze
            metric: 'roi', 'profit', or 'win_rate'
            top_n: Number of top performers to return

        Returns:
            List of top performers
        """
        analysis = self.analyze_by_dimension(dimension)

        # Filter out categories with too few bets
        significant = {k: v for k, v in analysis.items() if v['count'] >= 5}

        # Sort by metric
        sorted_categories = sorted(
            significant.items(),
            key=lambda x: x[1][metric],
            reverse=True
        )

        return [
            {
                'category': cat,
                'count': data['count'],
                'roi': data['roi'],
                'profit': data['total_profit'],
                'win_rate': data['win_rate']
            }
            for cat, data in sorted_categories[:top_n]
        ]

    def bottom_performers(self, dimension: str, metric: str = 'roi', bottom_n: int = 5) -> List[Dict]:
        """Get bottom performers by dimension"""
        analysis = self.analyze_by_dimension(dimension)
        significant = {k: v for k, v in analysis.items() if v['count'] >= 5}

        sorted_categories = sorted(
            significant.items(),
            key=lambda x: x[1][metric]
        )

        return [
            {
                'category': cat,
                'count': data['count'],
                'roi': data['roi'],
                'profit': data['total_profit'],
                'win_rate': data['win_rate']
            }
            for cat, data in sorted_categories[:bottom_n]
        ]

    def generate_full_report(self) -> Dict:
        """Generate comprehensive performance attribution report"""
        report = {
            'overall': {
                'total_bets': self.total_bets,
                'total_stake': self.total_stake,
                'total_profit': self.total_profit,
                'roi': self.overall_roi,
                'sharpe_ratio': self.calculate_sharpe_ratio(self.bets)
            },
            'by_sport': self.analyze_by_dimension('sport'),
            'by_bet_type': self.analyze_by_dimension('bet_type'),
            'by_book': self.analyze_by_dimension('book'),
            'by_odds_category': self.analyze_by_dimension('odds_category'),
            'by_clv': self.analyze_by_dimension('clv_sign'),
            'top_performers': {
                'sports': self.top_performers('sport', 'roi', 3),
                'bet_types': self.top_performers('bet_type', 'roi', 3),
                'books': self.top_performers('book', 'roi', 3)
            },
            'bottom_performers': {
                'sports': self.bottom_performers('sport', 'roi', 3),
                'bet_types': self.bottom_performers('bet_type', 'roi', 3),
                'books': self.bottom_performers('book', 'roi', 3)
            }
        }

        return report

    def print_report(self):
        """Print formatted attribution report"""
        report = self.generate_full_report()

        print(f"\n{'='*80}")
        print(f"PERFORMANCE ATTRIBUTION REPORT")
        print(f"{'='*80}")

        # Overall performance
        print(f"\n📊 Overall Performance")
        print(f"  Total Bets:     {report['overall']['total_bets']:,}")
        print(f"  Total Staked:   ${report['overall']['total_stake']:,.2f}")
        print(f"  Total Profit:   ${report['overall']['total_profit']:+,.2f}")
        print(f"  ROI:            {report['overall']['roi']:+.2f}%")
        print(f"  Sharpe Ratio:   {report['overall']['sharpe_ratio']:.2f}")

        # By Sport
        print(f"\n⚽ Performance by Sport")
        print(f"  {'Sport':<15} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"  {'-'*70}")
        for sport, data in sorted(report['by_sport'].items(), key=lambda x: x[1]['roi'], reverse=True):
            indicator = "✓" if data['roi'] > 0 else "✗"
            print(f"  {sport:<15} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f} {indicator}")

        # By Bet Type
        print(f"\n📋 Performance by Bet Type")
        print(f"  {'Type':<15} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"  {'-'*70}")
        for bet_type, data in sorted(report['by_bet_type'].items(), key=lambda x: x[1]['roi'], reverse=True):
            indicator = "✓" if data['roi'] > 0 else "✗"
            print(f"  {bet_type:<15} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f} {indicator}")

        # By Odds Category
        print(f"\n💰 Performance by Odds Range")
        print(f"  {'Category':<15} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"  {'-'*70}")
        for odds_cat, data in sorted(report['by_odds_category'].items(), key=lambda x: x[1]['roi'], reverse=True):
            indicator = "✓" if data['roi'] > 0 else "✗"
            print(f"  {odds_cat:<15} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f} {indicator}")

        # By Book
        print(f"\n📚 Performance by Sportsbook")
        print(f"  {'Book':<15} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"  {'-'*70}")
        for book, data in sorted(report['by_book'].items(), key=lambda x: x[1]['roi'], reverse=True):
            indicator = "✓" if data['roi'] > 0 else "✗"
            print(f"  {book:<15} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f} {indicator}")

        # CLV Analysis
        print(f"\n📈 Closing Line Value (CLV) Analysis")
        print(f"  {'CLV':<15} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"  {'-'*70}")
        for clv_sign, data in report['by_clv'].items():
            indicator = "✓" if data['roi'] > 0 else "✗"
            print(f"  {clv_sign:<15} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f} {indicator}")

        # Top Performers
        print(f"\n🏆 Top Performers")
        print(f"\n  Best Sports (by ROI, min 5 bets):")
        for i, perf in enumerate(report['top_performers']['sports'], 1):
            print(f"    {i}. {perf['category']:12s} - ROI: {perf['roi']:+.2f}% ({perf['count']} bets)")

        print(f"\n  Best Bet Types (by ROI, min 5 bets):")
        for i, perf in enumerate(report['top_performers']['bet_types'], 1):
            print(f"    {i}. {perf['category']:12s} - ROI: {perf['roi']:+.2f}% ({perf['count']} bets)")

        print(f"\n  Best Books (by ROI, min 5 bets):")
        for i, perf in enumerate(report['top_performers']['books'], 1):
            print(f"    {i}. {perf['category']:12s} - ROI: {perf['roi']:+.2f}% ({perf['count']} bets)")

        # Bottom Performers
        print(f"\n⚠️  Areas for Improvement")
        print(f"\n  Worst Sports (by ROI, min 5 bets):")
        for i, perf in enumerate(report['bottom_performers']['sports'], 1):
            print(f"    {i}. {perf['category']:12s} - ROI: {perf['roi']:+.2f}% ({perf['count']} bets)")

        print(f"\n  Worst Bet Types (by ROI, min 5 bets):")
        for i, perf in enumerate(report['bottom_performers']['bet_types'], 1):
            print(f"    {i}. {perf['category']:12s} - ROI: {perf['roi']:+.2f}% ({perf['count']} bets)")

        # Recommendations
        print(f"\n💡 Recommendations")

        recommendations = []

        # Check CLV
        if 'positive_clv' in report['by_clv'] and 'negative_clv' in report['by_clv']:
            pos_roi = report['by_clv']['positive_clv']['roi']
            neg_roi = report['by_clv']['negative_clv']['roi']

            if pos_roi > neg_roi:
                recommendations.append(
                    f"✓ Focus on positive CLV bets (ROI: {pos_roi:+.2f}% vs {neg_roi:+.2f}%)"
                )

        # Check bet types
        best_type = report['top_performers']['bet_types'][0] if report['top_performers']['bet_types'] else None
        worst_type = report['bottom_performers']['bet_types'][0] if report['bottom_performers']['bet_types'] else None

        if best_type and worst_type:
            if worst_type['roi'] < -5:
                recommendations.append(
                    f"⚠️  Avoid {worst_type['category']} bets (ROI: {worst_type['roi']:+.2f}%)"
                )
            if best_type['roi'] > 5:
                recommendations.append(
                    f"✓ Increase {best_type['category']} bets (ROI: {best_type['roi']:+.2f}%)"
                )

        # Check sports
        best_sport = report['top_performers']['sports'][0] if report['top_performers']['sports'] else None
        worst_sport = report['bottom_performers']['sports'][0] if report['bottom_performers']['sports'] else None

        if best_sport and worst_sport:
            if worst_sport['roi'] < -5:
                recommendations.append(
                    f"⚠️  Reduce or avoid {worst_sport['category']} (ROI: {worst_sport['roi']:+.2f}%)"
                )

        # Check odds categories
        for odds_cat, data in report['by_odds_category'].items():
            if data['count'] >= 10 and data['roi'] > 10:
                recommendations.append(
                    f"✓ {odds_cat.title()} odds showing strong performance ({data['roi']:+.2f}%)"
                )

        if recommendations:
            for rec in recommendations:
                print(f"  {rec}")
        else:
            print(f"  No specific recommendations - continue tracking performance")

        print(f"\n{'='*80}")


def load_bets_from_csv(filename: str) -> List[Bet]:
    """Load bets from CSV file"""
    bets = []
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bets.append(Bet(row))
    return bets


def main():
    parser = argparse.ArgumentParser(
        description='Performance Attribution Analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze bets from CSV
  %(prog)s bets.csv

  # Export analysis to JSON
  %(prog)s bets.csv --export report.json

CSV Format (required columns):
  date,sport,bet_type,odds,stake,result,book,clv,description

  date:        YYYY-MM-DD
  sport:       nfl, nba, mlb, soccer, etc.
  bet_type:    moneyline, spread, total, prop
  odds:        American odds (-110, +150, etc.)
  stake:       Bet amount
  result:      win, loss, push
  book:        Sportsbook name
  clv:         Closing line value (optional, 0 if unknown)
  description: Bet description (optional)
        """
    )

    parser.add_argument('csv_file', help='CSV file with bet data')
    parser.add_argument('--export', help='Export report to JSON file')
    parser.add_argument('--dimension', choices=['sport', 'bet_type', 'book', 'odds_category', 'clv_sign'],
                       help='Show detailed breakdown by specific dimension')

    args = parser.parse_args()

    # Load bets
    try:
        bets = load_bets_from_csv(args.csv_file)
    except FileNotFoundError:
        print(f"Error: File '{args.csv_file}' not found")
        return
    except Exception as e:
        print(f"Error loading bets: {e}")
        return

    if not bets:
        print("No bets found in CSV file")
        return

    # Analyze
    analyzer = PerformanceAttributionAnalyzer(bets)

    if args.dimension:
        # Show detailed breakdown
        analysis = analyzer.analyze_by_dimension(args.dimension)
        print(f"\n{'='*70}")
        print(f"Performance by {args.dimension.replace('_', ' ').title()}")
        print(f"{'='*70}")
        print(f"\n{'Category':<20} {'Bets':<8} {'Win%':<8} {'ROI':<10} {'Profit':<12}")
        print(f"{'-'*70}")
        for category, data in sorted(analysis.items(), key=lambda x: x[1]['roi'], reverse=True):
            print(f"{category:<20} {data['count']:<8} {data['win_rate']:<7.1f}% "
                  f"{data['roi']:>+8.2f}% ${data['total_profit']:>+10.2f}")
    else:
        # Full report
        analyzer.print_report()

    # Export if requested
    if args.export:
        report = analyzer.generate_full_report()
        with open(args.export, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Report exported to {args.export}")


if __name__ == '__main__':
    main()
