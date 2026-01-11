#!/usr/bin/env python3
"""
Bankroll Simulator with Visualization

Simulate betting strategies and visualize bankroll progression.
"""

import argparse
import random
from typing import List, Callable


def american_to_decimal(odds: float) -> float:
    """Convert American to decimal odds"""
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


def calculate_payout(stake: float, odds: float, won: bool) -> float:
    """Calculate payout for a bet"""
    if won:
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))
    else:
        return -stake


class BankrollSimulator:
    """Simulate bankroll progression"""

    def __init__(
        self,
        starting_bankroll: float,
        strategy: str,
        win_rate: float,
        odds: float,
        num_bets: int
    ):
        self.starting_bankroll = starting_bankroll
        self.strategy = strategy
        self.win_rate = win_rate
        self.odds = odds
        self.num_bets = num_bets

        self.bankroll_history = [starting_bankroll]
        self.results = []

    def get_bet_size(self, current_bankroll: float) -> float:
        """Calculate bet size based on strategy"""
        if self.strategy == 'flat':
            return self.starting_bankroll * 0.02  # 2% of starting

        elif self.strategy == 'percentage':
            return current_bankroll * 0.02  # 2% of current

        elif self.strategy == 'kelly':
            # Kelly criterion
            if self.odds > 0:
                implied_prob = 100 / (self.odds + 100)
            else:
                implied_prob = abs(self.odds) / (abs(self.odds) + 100)

            decimal_odds = american_to_decimal(self.odds)
            b = decimal_odds - 1
            p = self.win_rate
            q = 1 - p

            kelly = (b * p - q) / b
            kelly = max(0, kelly) * 0.25  # Quarter Kelly

            return current_bankroll * kelly

        elif self.strategy == 'martingale':
            # This is stored in the object state
            if not hasattr(self, 'last_bet'):
                self.last_bet = self.starting_bankroll * 0.02
            return self.last_bet

        else:
            return self.starting_bankroll * 0.02

    def run_simulation(self):
        """Run the simulation"""
        current_bankroll = self.starting_bankroll
        consecutive_losses = 0

        for i in range(self.num_bets):
            if current_bankroll <= 0:
                # Busted
                self.bankroll_history.append(0)
                self.results.append(False)
                continue

            # Get bet size
            bet_size = self.get_bet_size(current_bankroll)
            bet_size = min(bet_size, current_bankroll)

            # Simulate outcome
            won = random.random() < self.win_rate

            # Calculate profit/loss
            profit = calculate_payout(bet_size, self.odds, won)

            # Update bankroll
            current_bankroll += profit
            current_bankroll = max(0, current_bankroll)

            # Store results
            self.bankroll_history.append(current_bankroll)
            self.results.append(won)

            # Update martingale state
            if self.strategy == 'martingale':
                if won:
                    self.last_bet = self.starting_bankroll * 0.02
                    consecutive_losses = 0
                else:
                    consecutive_losses += 1
                    self.last_bet = min(
                        self.last_bet * 2,
                        current_bankroll
                    )

    def get_stats(self) -> dict:
        """Calculate simulation statistics"""
        wins = sum(1 for r in self.results if r)
        losses = len(self.results) - wins

        peak = max(self.bankroll_history)
        low = min(self.bankroll_history)

        # Calculate max drawdown
        max_dd = 0
        peak_val = self.starting_bankroll
        for value in self.bankroll_history:
            if value > peak_val:
                peak_val = value
            dd = (peak_val - value) / peak_val if peak_val > 0 else 0
            if dd > max_dd:
                max_dd = dd

        final = self.bankroll_history[-1]
        profit = final - self.starting_bankroll
        roi = (profit / self.starting_bankroll) * 100

        return {
            'starting': self.starting_bankroll,
            'final': final,
            'profit': profit,
            'roi': roi,
            'wins': wins,
            'losses': losses,
            'win_rate': (wins / len(self.results) * 100) if self.results else 0,
            'peak': peak,
            'low': low,
            'max_drawdown': max_dd * 100,
            'busted': final <= 0
        }

    def visualize_ascii(self, width: int = 70, height: int = 20):
        """Create ASCII visualization of bankroll progression"""
        if not self.bankroll_history:
            return

        stats = self.get_stats()

        print(f"\n{'='*width}")
        print(f"Bankroll Simulation: {self.strategy.title()} Strategy")
        print(f"{'='*width}")

        # Create chart
        values = self.bankroll_history
        min_val = min(values)
        max_val = max(values)

        # Normalize to chart height
        if max_val == min_val:
            normalized = [height // 2] * len(values)
        else:
            normalized = [
                int((v - min_val) / (max_val - min_val) * (height - 1))
                for v in values
            ]

        # Create grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]

        # Plot line
        step = max(1, len(values) // width)
        for i in range(0, len(values) - step, step):
            x = i // step
            if x >= width:
                break
            y = height - 1 - normalized[i]

            # Draw line to next point
            if x < width - 1 and i + step < len(values):
                next_y = height - 1 - normalized[i + step]

                # Simple line drawing
                if next_y < y:
                    for dy in range(next_y, y + 1):
                        if 0 <= dy < height:
                            grid[dy][x] = '/'
                elif next_y > y:
                    for dy in range(y, next_y + 1):
                        if 0 <= dy < height:
                            grid[dy][x] = '\\'
                else:
                    if 0 <= y < height:
                        grid[y][x] = '─'
            else:
                if 0 <= y < height:
                    grid[y][x] = '*'

        # Add start line (horizontal line at starting bankroll)
        start_y = height - 1 - int((self.starting_bankroll - min_val) /
                                   (max_val - min_val) * (height - 1))
        if 0 <= start_y < height:
            for x in range(width):
                if grid[start_y][x] == ' ':
                    grid[start_y][x] = '·'

        # Print grid with labels
        print(f"\n${max_val:>10.2f} ┤")
        for row in grid:
            print("           │" + ''.join(row))
        print(f"${min_val:>10.2f} ┤")
        print("           └" + "─" * width)
        print(f"           Start{' ' * (width - 28)}End ({self.num_bets} bets)")

        # Print statistics
        print(f"\n{'Statistics:'}")
        print(f"  Starting Bankroll: ${stats['starting']:.2f}")
        print(f"  Final Bankroll:    ${stats['final']:.2f}")
        print(f"  Profit/Loss:       ${stats['profit']:+.2f}")
        print(f"  ROI:               {stats['roi']:+.2f}%")
        print(f"\n  Record:            {stats['wins']}-{stats['losses']}")
        print(f"  Win Rate:          {stats['win_rate']:.2f}%")
        print(f"\n  Peak:              ${stats['peak']:.2f}")
        print(f"  Low:               ${stats['low']:.2f}")
        print(f"  Max Drawdown:      {stats['max_drawdown']:.2f}%")

        if stats['busted']:
            print(f"\n  ⚠️  BUSTED!")
        elif stats['profit'] > 0:
            print(f"\n  ✓ Profitable")
        else:
            print(f"\n  ✗ Unprofitable")


def run_multiple_simulations(
    starting_bankroll: float,
    strategy: str,
    win_rate: float,
    odds: float,
    num_bets: int,
    num_sims: int = 100
):
    """Run multiple simulations and show aggregate results"""
    results = []

    for _ in range(num_sims):
        sim = BankrollSimulator(starting_bankroll, strategy, win_rate, odds, num_bets)
        sim.run_simulation()
        stats = sim.get_stats()
        results.append(stats)

    # Aggregate statistics
    avg_final = sum(r['final'] for r in results) / len(results)
    avg_profit = sum(r['profit'] for r in results) / len(results)
    avg_roi = sum(r['roi'] for r in results) / len(results)

    profitable_count = sum(1 for r in results if r['profit'] > 0)
    busted_count = sum(1 for r in results if r['busted'])

    avg_peak = sum(r['peak'] for r in results) / len(results)
    avg_drawdown = sum(r['max_drawdown'] for r in results) / len(results)

    print(f"\n{'='*70}")
    print(f"Monte Carlo Simulation Results ({num_sims} simulations)")
    print(f"Strategy: {strategy.title()} | Win Rate: {win_rate*100:.1f}% | Odds: {odds:+.0f}")
    print(f"{'='*70}")

    print(f"\nAggregate Results:")
    print(f"  Average Final Bankroll: ${avg_final:.2f}")
    print(f"  Average Profit:         ${avg_profit:+.2f}")
    print(f"  Average ROI:            {avg_roi:+.2f}%")

    print(f"\nOutcome Distribution:")
    print(f"  Profitable:  {profitable_count}/{num_sims} ({profitable_count/num_sims*100:.1f}%)")
    print(f"  Busted:      {busted_count}/{num_sims} ({busted_count/num_sims*100:.1f}%)")

    print(f"\nRisk Metrics:")
    print(f"  Average Peak:       ${avg_peak:.2f}")
    print(f"  Average Max DD:     {avg_drawdown:.2f}%")

    # Distribution
    print(f"\nFinal Bankroll Distribution:")
    ranges = [
        (0, 0, "Busted"),
        (1, starting_bankroll * 0.5, "Down >50%"),
        (starting_bankroll * 0.5, starting_bankroll * 0.9, "Down 10-50%"),
        (starting_bankroll * 0.9, starting_bankroll * 1.1, "±10%"),
        (starting_bankroll * 1.1, starting_bankroll * 2, "Up 10-100%"),
        (starting_bankroll * 2, float('inf'), "Doubled+")
    ]

    for low, high, label in ranges:
        count = sum(1 for r in results if low <= r['final'] < high)
        pct = count / num_sims * 100
        bar = '█' * int(pct / 2)
        print(f"  {label:12s}: {bar:30s} {pct:5.1f}% ({count})")


def main():
    parser = argparse.ArgumentParser(
        description='Bankroll Simulator with Visualization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Strategies:
  flat       - Flat betting (2% of starting bankroll)
  percentage - Percentage betting (2% of current bankroll)
  kelly      - Kelly criterion (1/4 Kelly)
  martingale - Martingale (double after loss)

Examples:
  # Single simulation
  %(prog)s -b 1000 -s percentage -w 0.54 -o -110 -n 100

  # Multiple simulations
  %(prog)s -b 1000 -s kelly -w 0.55 -o -110 -n 100 --sims 100
        """
    )

    parser.add_argument('-b', '--bankroll', type=float, required=True,
                       help='Starting bankroll')
    parser.add_argument('-s', '--strategy', required=True,
                       choices=['flat', 'percentage', 'kelly', 'martingale'],
                       help='Betting strategy')
    parser.add_argument('-w', '--winrate', type=float, required=True,
                       help='Win rate (0-1, e.g., 0.54)')
    parser.add_argument('-o', '--odds', type=float, required=True,
                       help='Average odds (American)')
    parser.add_argument('-n', '--numbets', type=int, default=100,
                       help='Number of bets per simulation')
    parser.add_argument('--sims', type=int, default=1,
                       help='Number of simulations to run')
    parser.add_argument('--visualize', action='store_true',
                       help='Show visualization (single sim only)')

    args = parser.parse_args()

    if args.sims == 1:
        # Single simulation
        sim = BankrollSimulator(
            args.bankroll,
            args.strategy,
            args.winrate,
            args.odds,
            args.numbets
        )
        sim.run_simulation()

        if args.visualize or True:  # Always visualize for single sim
            sim.visualize_ascii()
    else:
        # Multiple simulations
        run_multiple_simulations(
            args.bankroll,
            args.strategy,
            args.winrate,
            args.odds,
            args.numbets,
            args.sims
        )


if __name__ == '__main__':
    main()
