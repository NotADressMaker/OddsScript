"""
Closing Line Value (CLV) Tracker

Track whether you're beating the closing line - one of the best indicators
of long-term betting success.
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Optional


class CLVTracker:
    """
    Track Closing Line Value for bets

    CLV measures how much value you captured by comparing your bet odds
    to the closing line. Positive CLV indicates you got better odds than
    the market's final assessment.
    """

    def __init__(self, filename: str = 'clv_data.csv'):
        """
        Initialize CLV tracker

        Args:
            filename: CSV file to store CLV data
        """
        self.filename = filename
        self.bets: List[Dict] = []
        self.load_data()

    def load_data(self):
        """Load CLV data from file"""
        try:
            with open(self.filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['bet_odds'] = float(row['bet_odds'])
                    row['closing_odds'] = float(row['closing_odds'])
                    row['clv_percent'] = float(row['clv_percent']) if row['clv_percent'] else None
                    row['result'] = row.get('result', 'pending')
                    self.bets.append(row)
        except FileNotFoundError:
            pass

    def save_data(self):
        """Save CLV data to file"""
        if not self.bets:
            return

        fieldnames = ['date', 'game', 'selection', 'bet_odds', 'closing_odds',
                     'clv_percent', 'result', 'notes']

        with open(self.filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.bets)

    def calculate_clv(self, bet_odds: float, closing_odds: float) -> float:
        """
        Calculate CLV percentage

        Positive CLV = you got better odds than closing
        Negative CLV = you got worse odds than closing

        Args:
            bet_odds: Odds when you placed bet
            closing_odds: Closing line odds

        Returns:
            CLV as percentage
        """
        # Convert to implied probabilities
        if bet_odds > 0:
            bet_prob = 100 / (bet_odds + 100)
        else:
            bet_prob = abs(bet_odds) / (abs(bet_odds) + 100)

        if closing_odds > 0:
            closing_prob = 100 / (closing_odds + 100)
        else:
            closing_prob = abs(closing_odds) / (abs(closing_odds) + 100)

        # CLV = (closing_prob - bet_prob) / bet_prob * 100
        # If closing prob is higher, you got better odds (positive CLV)
        clv = ((closing_prob - bet_prob) / bet_prob) * 100

        return clv

    def add_bet(
        self,
        game: str,
        selection: str,
        bet_odds: float,
        closing_odds: Optional[float] = None,
        notes: str = ''
    ):
        """
        Add a bet to track CLV

        Args:
            game: Game description
            selection: What you bet on
            bet_odds: Odds when you placed bet
            closing_odds: Closing line odds (can add later)
            notes: Optional notes
        """
        clv_percent = None
        if closing_odds is not None:
            clv_percent = self.calculate_clv(bet_odds, closing_odds)

        bet = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'game': game,
            'selection': selection,
            'bet_odds': bet_odds,
            'closing_odds': closing_odds if closing_odds is not None else '',
            'clv_percent': clv_percent if clv_percent is not None else '',
            'result': 'pending',
            'notes': notes
        }

        self.bets.append(bet)
        self.save_data()

        if clv_percent is not None:
            print(f"✓ Bet added: {selection} @ {bet_odds:+.0f} | CLV: {clv_percent:+.2f}%")
        else:
            print(f"✓ Bet added: {selection} @ {bet_odds:+.0f} (closing line pending)")

    def update_closing_line(self, bet_index: int, closing_odds: float):
        """
        Update bet with closing line

        Args:
            bet_index: Index of bet to update
            closing_odds: Closing line odds
        """
        if bet_index < 0 or bet_index >= len(self.bets):
            print("Invalid bet index")
            return

        bet = self.bets[bet_index]
        bet['closing_odds'] = closing_odds
        bet['clv_percent'] = self.calculate_clv(bet['bet_odds'], closing_odds)

        self.save_data()
        print(f"✓ Updated closing line: CLV = {bet['clv_percent']:+.2f}%")

    def settle_bet(self, bet_index: int, result: str):
        """
        Settle a bet

        Args:
            bet_index: Index of bet
            result: 'won', 'lost', or 'push'
        """
        if bet_index < 0 or bet_index >= len(self.bets):
            print("Invalid bet index")
            return

        self.bets[bet_index]['result'] = result
        self.save_data()
        print(f"✓ Bet settled: {result.upper()}")

    def get_stats(self) -> Dict:
        """Calculate CLV statistics"""
        # Filter bets with CLV data
        bets_with_clv = [bet for bet in self.bets if bet['clv_percent'] != '']

        if not bets_with_clv:
            return {}

        clv_values = [float(bet['clv_percent']) for bet in bets_with_clv]

        # Overall CLV stats
        avg_clv = sum(clv_values) / len(clv_values)
        positive_clv_count = sum(1 for clv in clv_values if clv > 0)
        positive_clv_rate = (positive_clv_count / len(clv_values)) * 100

        # Median CLV
        sorted_clv = sorted(clv_values)
        n = len(sorted_clv)
        median_clv = sorted_clv[n//2] if n % 2 == 1 else (sorted_clv[n//2-1] + sorted_clv[n//2]) / 2

        # Best and worst
        best_clv = max(clv_values)
        worst_clv = min(clv_values)

        # Results correlation
        settled_bets = [bet for bet in bets_with_clv if bet['result'] != 'pending']

        if settled_bets:
            won_bets = [bet for bet in settled_bets if bet['result'] == 'won']
            lost_bets = [bet for bet in settled_bets if bet['result'] == 'lost']

            avg_clv_wins = sum(float(bet['clv_percent']) for bet in won_bets) / len(won_bets) if won_bets else 0
            avg_clv_losses = sum(float(bet['clv_percent']) for bet in lost_bets) / len(lost_bets) if lost_bets else 0

            win_rate = (len(won_bets) / len(settled_bets)) * 100

            # CLV by result
            positive_clv_bets = [bet for bet in settled_bets if float(bet['clv_percent']) > 0]
            negative_clv_bets = [bet for bet in settled_bets if float(bet['clv_percent']) <= 0]

            positive_clv_wins = sum(1 for bet in positive_clv_bets if bet['result'] == 'won')
            positive_clv_win_rate = (positive_clv_wins / len(positive_clv_bets) * 100) if positive_clv_bets else 0

            negative_clv_wins = sum(1 for bet in negative_clv_bets if bet['result'] == 'won')
            negative_clv_win_rate = (negative_clv_wins / len(negative_clv_bets) * 100) if negative_clv_bets else 0
        else:
            avg_clv_wins = 0
            avg_clv_losses = 0
            win_rate = 0
            positive_clv_win_rate = 0
            negative_clv_win_rate = 0

        return {
            'total_bets': len(bets_with_clv),
            'avg_clv': avg_clv,
            'median_clv': median_clv,
            'positive_clv_rate': positive_clv_rate,
            'best_clv': best_clv,
            'worst_clv': worst_clv,
            'settled_bets': len(settled_bets),
            'win_rate': win_rate,
            'avg_clv_wins': avg_clv_wins,
            'avg_clv_losses': avg_clv_losses,
            'positive_clv_win_rate': positive_clv_win_rate,
            'negative_clv_win_rate': negative_clv_win_rate
        }

    def print_stats(self):
        """Print formatted CLV statistics"""
        stats = self.get_stats()

        if not stats:
            print("No CLV data available")
            return

        print(f"\n{'='*60}")
        print(f"Closing Line Value (CLV) Analysis")
        print(f"{'='*60}")

        print(f"\nOverall CLV:")
        print(f"  Total Bets Tracked: {stats['total_bets']}")
        print(f"  Average CLV: {stats['avg_clv']:+.2f}%")
        print(f"  Median CLV: {stats['median_clv']:+.2f}%")
        print(f"  Positive CLV Rate: {stats['positive_clv_rate']:.1f}%")
        print(f"  Best CLV: {stats['best_clv']:+.2f}%")
        print(f"  Worst CLV: {stats['worst_clv']:+.2f}%")

        if stats['settled_bets'] > 0:
            print(f"\nResults (Settled Bets: {stats['settled_bets']}):")
            print(f"  Overall Win Rate: {stats['win_rate']:.1f}%")
            print(f"  Avg CLV on Wins: {stats['avg_clv_wins']:+.2f}%")
            print(f"  Avg CLV on Losses: {stats['avg_clv_losses']:+.2f}%")
            print(f"\n  Win Rate with +CLV: {stats['positive_clv_win_rate']:.1f}%")
            print(f"  Win Rate with -CLV: {stats['negative_clv_win_rate']:.1f}%")

        # Interpretation
        print(f"\n{'='*60}")
        print(f"Interpretation:")
        if stats['avg_clv'] > 2:
            print(f"  ✓ EXCELLENT - Consistently beating closing line")
            print(f"    You're getting significant value on your bets")
        elif stats['avg_clv'] > 0:
            print(f"  ✓ GOOD - Positive CLV on average")
            print(f"    You're beating the closing line more often than not")
        elif stats['avg_clv'] > -2:
            print(f"  ~ NEUTRAL - Close to market efficiency")
            print(f"    You're roughly in line with closing odds")
        else:
            print(f"  ✗ POOR - Negative CLV on average")
            print(f"    Consider waiting for better lines or improving timing")

        print(f"\nNote: Positive CLV is strongly correlated with long-term")
        print(f"      profitability, even if short-term results vary.")

    def list_recent(self, limit: int = 10):
        """List recent bets with CLV"""
        bets_with_clv = [bet for bet in self.bets if bet['clv_percent'] != ''][-limit:]

        if not bets_with_clv:
            print("No bets with CLV data")
            return

        print(f"\nRecent Bets (Last {len(bets_with_clv)}):")
        print(f"{'Date':<20} {'Selection':<25} {'Bet':<8} {'Close':<8} {'CLV':<10} {'Result'}")
        print("="*90)

        for bet in bets_with_clv:
            clv_str = f"{float(bet['clv_percent']):+.2f}%"
            result_str = bet['result'] if bet['result'] != 'pending' else '-'

            print(f"{bet['date']:<20} {bet['selection']:<25} "
                  f"{bet['bet_odds']:>+7.0f} {float(bet['closing_odds']):>+7.0f} "
                  f"{clv_str:<10} {result_str}")


def main():
    """CLI interface for CLV tracker"""
    import argparse

    parser = argparse.ArgumentParser(description='Closing Line Value Tracker')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add bet
    add_parser = subparsers.add_parser('add', help='Add a bet')
    add_parser.add_argument('game', help='Game description')
    add_parser.add_argument('selection', help='Your selection')
    add_parser.add_argument('bet_odds', type=float, help='Odds when you bet')
    add_parser.add_argument('-c', '--closing', type=float, help='Closing line odds')
    add_parser.add_argument('-n', '--notes', default='', help='Notes')

    # Update closing line
    update_parser = subparsers.add_parser('close', help='Update closing line')
    update_parser.add_argument('index', type=int, help='Bet index')
    update_parser.add_argument('odds', type=float, help='Closing line odds')

    # Settle bet
    settle_parser = subparsers.add_parser('settle', help='Settle a bet')
    settle_parser.add_argument('index', type=int, help='Bet index')
    settle_parser.add_argument('result', choices=['won', 'lost', 'push'], help='Result')

    # Stats
    subparsers.add_parser('stats', help='Show CLV statistics')

    # Recent
    recent_parser = subparsers.add_parser('recent', help='Show recent bets')
    recent_parser.add_argument('-n', '--num', type=int, default=10, help='Number of bets')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = CLVTracker()

    if args.command == 'add':
        tracker.add_bet(args.game, args.selection, args.bet_odds,
                       args.closing, args.notes)
    elif args.command == 'close':
        tracker.update_closing_line(args.index, args.odds)
    elif args.command == 'settle':
        tracker.settle_bet(args.index, args.result)
    elif args.command == 'stats':
        tracker.print_stats()
    elif args.command == 'recent':
        tracker.list_recent(args.num)


if __name__ == '__main__':
    main()
