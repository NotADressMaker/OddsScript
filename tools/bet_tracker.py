#!/usr/bin/env python3
"""
Bet Performance Tracker

Track and analyze your betting performance over time.
Stores bets in a CSV file and provides analytics.
"""

import csv
import json
from datetime import datetime
from typing import List, Dict, Optional
import os


class BetTracker:
    """Track betting performance and generate analytics"""

    def __init__(self, filename: str = 'bets.csv'):
        """
        Initialize bet tracker

        Args:
            filename: CSV file to store bets
        """
        self.filename = filename
        self.bets: List[Dict] = []
        self.load_bets()

    def load_bets(self):
        """Load bets from CSV file"""
        if not os.path.exists(self.filename):
            return

        with open(self.filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric fields
                row['odds'] = float(row['odds'])
                row['stake'] = float(row['stake'])
                row['profit'] = float(row['profit']) if row['profit'] else None
                self.bets.append(row)

    def save_bets(self):
        """Save bets to CSV file"""
        if not self.bets:
            return

        fieldnames = ['date', 'sport', 'event', 'bet_type', 'selection',
                      'odds', 'stake', 'result', 'profit', 'notes']

        with open(self.filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.bets)

    def add_bet(self,
                sport: str,
                event: str,
                bet_type: str,
                selection: str,
                odds: float,
                stake: float,
                notes: str = ''):
        """
        Add a new bet

        Args:
            sport: Sport type (e.g., 'NFL', 'NBA', 'MLB')
            event: Event description (e.g., 'Lakers vs Celtics')
            bet_type: Type of bet (e.g., 'moneyline', 'spread', 'total')
            selection: What you bet on (e.g., 'Lakers -5.5')
            odds: American odds
            stake: Amount wagered
            notes: Optional notes
        """
        bet = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sport': sport,
            'event': event,
            'bet_type': bet_type,
            'selection': selection,
            'odds': odds,
            'stake': stake,
            'result': 'pending',
            'profit': None,
            'notes': notes
        }

        self.bets.append(bet)
        self.save_bets()
        print(f"✓ Bet added: {event} - {selection} @ {odds:+.0f}")

    def settle_bet(self, bet_index: int, result: str):
        """
        Settle a bet

        Args:
            bet_index: Index of bet to settle
            result: 'won', 'lost', or 'push'
        """
        if bet_index < 0 or bet_index >= len(self.bets):
            print("Invalid bet index")
            return

        bet = self.bets[bet_index]
        bet['result'] = result

        if result == 'won':
            if bet['odds'] > 0:
                profit = bet['stake'] * (bet['odds'] / 100)
            else:
                profit = bet['stake'] * (100 / abs(bet['odds']))
            bet['profit'] = profit
        elif result == 'lost':
            bet['profit'] = -bet['stake']
        else:  # push
            bet['profit'] = 0

        self.save_bets()
        print(f"✓ Bet settled: {result.upper()} - Profit: ${bet['profit']:+.2f}")

    def list_pending(self):
        """List all pending bets"""
        pending = [bet for bet in self.bets if bet['result'] == 'pending']

        if not pending:
            print("No pending bets")
            return

        print(f"\nPending Bets ({len(pending)})")
        print("=" * 80)

        for i, bet in enumerate(self.bets):
            if bet['result'] == 'pending':
                print(f"{i}: {bet['date']} | {bet['sport']} | {bet['event']}")
                print(f"   {bet['selection']} @ {bet['odds']:+.0f} | Stake: ${bet['stake']:.2f}")

    def get_stats(self, sport: Optional[str] = None, days: Optional[int] = None) -> Dict:
        """
        Get betting statistics

        Args:
            sport: Filter by sport (optional)
            days: Only include bets from last N days (optional)

        Returns:
            Dictionary with statistics
        """
        # Filter bets
        filtered_bets = [bet for bet in self.bets if bet['result'] != 'pending']

        if sport:
            filtered_bets = [bet for bet in filtered_bets if bet['sport'] == sport]

        if days:
            cutoff = datetime.now() - timedelta(days=days)
            filtered_bets = [
                bet for bet in filtered_bets
                if datetime.strptime(bet['date'], '%Y-%m-%d %H:%M:%S') >= cutoff
            ]

        if not filtered_bets:
            return {}

        # Calculate stats
        total_bets = len(filtered_bets)
        wins = sum(1 for bet in filtered_bets if bet['result'] == 'won')
        losses = sum(1 for bet in filtered_bets if bet['result'] == 'lost')
        pushes = sum(1 for bet in filtered_bets if bet['result'] == 'push')

        total_staked = sum(bet['stake'] for bet in filtered_bets)
        total_profit = sum(bet['profit'] or 0 for bet in filtered_bets)

        win_rate = (wins / total_bets * 100) if total_bets > 0 else 0
        roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

        # Calculate by bet type
        by_type = {}
        for bet in filtered_bets:
            bet_type = bet['bet_type']
            if bet_type not in by_type:
                by_type[bet_type] = {'bets': 0, 'wins': 0, 'profit': 0, 'staked': 0}

            by_type[bet_type]['bets'] += 1
            if bet['result'] == 'won':
                by_type[bet_type]['wins'] += 1
            by_type[bet_type]['profit'] += bet['profit'] or 0
            by_type[bet_type]['staked'] += bet['stake']

        # Calculate by sport
        by_sport = {}
        for bet in filtered_bets:
            sport_name = bet['sport']
            if sport_name not in by_sport:
                by_sport[sport_name] = {'bets': 0, 'wins': 0, 'profit': 0, 'staked': 0}

            by_sport[sport_name]['bets'] += 1
            if bet['result'] == 'won':
                by_sport[sport_name]['wins'] += 1
            by_sport[sport_name]['profit'] += bet['profit'] or 0
            by_sport[sport_name]['staked'] += bet['stake']

        return {
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'pushes': pushes,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_profit': total_profit,
            'roi': roi,
            'average_stake': total_staked / total_bets if total_bets > 0 else 0,
            'average_profit_per_bet': total_profit / total_bets if total_bets > 0 else 0,
            'by_type': by_type,
            'by_sport': by_sport
        }

    def print_stats(self, sport: Optional[str] = None, days: Optional[int] = None):
        """Print formatted statistics"""
        stats = self.get_stats(sport, days)

        if not stats:
            print("No settled bets to analyze")
            return

        title = "Betting Performance"
        if sport:
            title += f" - {sport}"
        if days:
            title += f" (Last {days} days)"

        print(f"\n{title}")
        print("=" * 60)

        print(f"\nOverall:")
        print(f"  Total Bets: {stats['total_bets']}")
        print(f"  Record: {stats['wins']}-{stats['losses']}-{stats['pushes']}")
        print(f"  Win Rate: {stats['win_rate']:.2f}%")
        print(f"  Total Staked: ${stats['total_staked']:.2f}")
        print(f"  Total Profit: ${stats['total_profit']:+.2f}")
        print(f"  ROI: {stats['roi']:+.2f}%")
        print(f"  Avg Stake: ${stats['average_stake']:.2f}")
        print(f"  Avg Profit/Bet: ${stats['average_profit_per_bet']:+.2f}")

        if stats['by_type']:
            print(f"\nBy Bet Type:")
            for bet_type, data in stats['by_type'].items():
                win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
                roi = (data['profit'] / data['staked'] * 100) if data['staked'] > 0 else 0
                print(f"  {bet_type}: {data['bets']} bets, {win_rate:.1f}% win rate, {roi:+.2f}% ROI")

        if stats['by_sport']:
            print(f"\nBy Sport:")
            for sport_name, data in stats['by_sport'].items():
                win_rate = (data['wins'] / data['bets'] * 100) if data['bets'] > 0 else 0
                roi = (data['profit'] / data['staked'] * 100) if data['staked'] > 0 else 0
                print(f"  {sport_name}: {data['bets']} bets, {win_rate:.1f}% win rate, {roi:+.2f}% ROI")

    def export_json(self, filename: str = 'bets_export.json'):
        """Export bets to JSON"""
        with open(filename, 'w') as f:
            json.dump(self.bets, f, indent=2)
        print(f"✓ Exported {len(self.bets)} bets to {filename}")


def main():
    """CLI interface for bet tracker"""
    import argparse

    parser = argparse.ArgumentParser(description='Bet Performance Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add bet
    add_parser = subparsers.add_parser('add', help='Add a new bet')
    add_parser.add_argument('sport', help='Sport (e.g., NFL, NBA)')
    add_parser.add_argument('event', help='Event (e.g., "Lakers vs Celtics")')
    add_parser.add_argument('selection', help='Selection (e.g., "Lakers -5.5")')
    add_parser.add_argument('-t', '--type', default='moneyline', help='Bet type')
    add_parser.add_argument('-o', '--odds', type=float, required=True, help='American odds')
    add_parser.add_argument('-s', '--stake', type=float, required=True, help='Stake amount')
    add_parser.add_argument('-n', '--notes', default='', help='Notes')

    # Settle bet
    settle_parser = subparsers.add_parser('settle', help='Settle a bet')
    settle_parser.add_argument('index', type=int, help='Bet index')
    settle_parser.add_argument('result', choices=['won', 'lost', 'push'], help='Result')

    # List pending
    subparsers.add_parser('pending', help='List pending bets')

    # Stats
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.add_argument('-s', '--sport', help='Filter by sport')
    stats_parser.add_argument('-d', '--days', type=int, help='Last N days')

    # Export
    export_parser = subparsers.add_parser('export', help='Export to JSON')
    export_parser.add_argument('-f', '--file', default='bets_export.json', help='Output file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = BetTracker()

    if args.command == 'add':
        tracker.add_bet(
            args.sport,
            args.event,
            args.type,
            args.selection,
            args.odds,
            args.stake,
            args.notes
        )
    elif args.command == 'settle':
        tracker.settle_bet(args.index, args.result)
    elif args.command == 'pending':
        tracker.list_pending()
    elif args.command == 'stats':
        tracker.print_stats(args.sport, args.days)
    elif args.command == 'export':
        tracker.export_json(args.file)


if __name__ == '__main__':
    from datetime import timedelta
    main()
