"""
Backtesting Framework for Betting Strategies

Test betting strategies against historical data or simulated results.
"""

import csv
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Optional
import random


class BetResult:
    """Represents a single bet result"""
    def __init__(self, date: datetime, odds: float, stake: float, won: bool):
        self.date = date
        self.odds = odds
        self.stake = stake
        self.won = won
        self.profit = self._calculate_profit()

    def _calculate_profit(self) -> float:
        """Calculate profit/loss for this bet"""
        if self.won:
            if self.odds > 0:
                return self.stake * (self.odds / 100)
            else:
                return self.stake * (100 / abs(self.odds))
        else:
            return -self.stake


class BacktestResult:
    """Results from a backtest run"""
    def __init__(self, strategy_name: str, starting_bankroll: float):
        self.strategy_name = strategy_name
        self.starting_bankroll = starting_bankroll
        self.bets: List[BetResult] = []
        self.bankroll_history: List[float] = [starting_bankroll]
        self.current_bankroll = starting_bankroll

    def add_bet(self, bet: BetResult):
        """Add a bet result and update bankroll"""
        self.bets.append(bet)
        self.current_bankroll += bet.profit
        self.bankroll_history.append(self.current_bankroll)

    def get_stats(self) -> Dict:
        """Calculate comprehensive statistics"""
        if not self.bets:
            return {}

        total_bets = len(self.bets)
        wins = sum(1 for bet in self.bets if bet.won)
        losses = total_bets - wins
        win_rate = (wins / total_bets) * 100 if total_bets > 0 else 0

        total_staked = sum(bet.stake for bet in self.bets)
        total_profit = self.current_bankroll - self.starting_bankroll
        roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

        # Calculate max drawdown
        peak = self.starting_bankroll
        max_dd = 0
        for value in self.bankroll_history:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd

        # Winning/losing streaks
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        for bet in self.bets:
            if bet.won:
                if current_streak >= 0:
                    current_streak += 1
                else:
                    current_streak = 1
                max_win_streak = max(max_win_streak, current_streak)
            else:
                if current_streak <= 0:
                    current_streak -= 1
                else:
                    current_streak = -1
                max_loss_streak = max(max_loss_streak, abs(current_streak))

        # Average win/loss
        winning_bets = [bet.profit for bet in self.bets if bet.won]
        losing_bets = [abs(bet.profit) for bet in self.bets if not bet.won]

        avg_win = sum(winning_bets) / len(winning_bets) if winning_bets else 0
        avg_loss = sum(losing_bets) / len(losing_bets) if losing_bets else 0

        # Profit factor
        gross_profit = sum(winning_bets) if winning_bets else 0
        gross_loss = sum(losing_bets) if losing_bets else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((100 - win_rate) / 100 * avg_loss)

        # Sharpe ratio (simplified)
        returns = []
        for i in range(1, len(self.bankroll_history)):
            ret = (self.bankroll_history[i] - self.bankroll_history[i-1]) / self.bankroll_history[i-1]
            returns.append(ret)

        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = variance ** 0.5
            sharpe = (avg_return / std_dev) if std_dev > 0 else 0
        else:
            sharpe = 0

        return {
            'strategy': self.strategy_name,
            'starting_bankroll': self.starting_bankroll,
            'ending_bankroll': self.current_bankroll,
            'total_profit': total_profit,
            'roi': roi,
            'total_bets': total_bets,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'max_drawdown': max_dd * 100,
            'max_win_streak': max_win_streak,
            'max_loss_streak': max_loss_streak,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'sharpe_ratio': sharpe,
            'final_peak': max(self.bankroll_history),
            'final_low': min(self.bankroll_history)
        }

    def print_summary(self):
        """Print formatted summary"""
        stats = self.get_stats()
        if not stats:
            print("No bets in backtest")
            return

        print(f"\n{'='*60}")
        print(f"Backtest Results: {stats['strategy']}")
        print(f"{'='*60}")
        print(f"\nBankroll:")
        print(f"  Starting: ${stats['starting_bankroll']:.2f}")
        print(f"  Ending:   ${stats['ending_bankroll']:.2f}")
        print(f"  Profit:   ${stats['total_profit']:+.2f}")
        print(f"  Peak:     ${stats['final_peak']:.2f}")
        print(f"  Low:      ${stats['final_low']:.2f}")

        print(f"\nPerformance:")
        print(f"  Total Bets:    {stats['total_bets']}")
        print(f"  Record:        {stats['wins']}-{stats['losses']}")
        print(f"  Win Rate:      {stats['win_rate']:.2f}%")
        print(f"  ROI:           {stats['roi']:+.2f}%")
        print(f"  Profit Factor: {stats['profit_factor']:.2f}")
        print(f"  Expectancy:    ${stats['expectancy']:+.2f}")

        print(f"\nRisk Metrics:")
        print(f"  Max Drawdown:     {stats['max_drawdown']:.2f}%")
        print(f"  Sharpe Ratio:     {stats['sharpe_ratio']:.2f}")
        print(f"  Max Win Streak:   {stats['max_win_streak']}")
        print(f"  Max Loss Streak:  {stats['max_loss_streak']}")

        print(f"\nBet Sizes:")
        print(f"  Total Staked: ${stats['total_staked']:.2f}")
        print(f"  Avg Win:      ${stats['avg_win']:.2f}")
        print(f"  Avg Loss:     ${stats['avg_loss']:.2f}")


class Backtester:
    """Run backtests on betting strategies"""

    def __init__(self, starting_bankroll: float):
        self.starting_bankroll = starting_bankroll

    def run_historical_backtest(
        self,
        strategy_name: str,
        bet_sizing_func: Callable,
        historical_data: List[Dict],
        kelly_prob_func: Optional[Callable] = None
    ) -> BacktestResult:
        """
        Run backtest on historical data

        Args:
            strategy_name: Name of the strategy
            bet_sizing_func: Function(bankroll, odds) -> stake
            historical_data: List of dicts with 'date', 'odds', 'result' (True/False)
            kelly_prob_func: Optional function to estimate win probability

        Returns:
            BacktestResult object
        """
        result = BacktestResult(strategy_name, self.starting_bankroll)
        current_bankroll = self.starting_bankroll

        for data in historical_data:
            if current_bankroll <= 0:
                break

            odds = data['odds']
            won = data['result']
            date = data.get('date', datetime.now())

            # Calculate bet size using strategy
            stake = bet_sizing_func(current_bankroll, odds)

            # Don't bet more than bankroll
            stake = min(stake, current_bankroll)

            if stake <= 0:
                continue

            # Create bet result
            bet = BetResult(date, odds, stake, won)
            result.add_bet(bet)

            # Update bankroll
            current_bankroll = result.current_bankroll

        return result

    def run_monte_carlo_backtest(
        self,
        strategy_name: str,
        bet_sizing_func: Callable,
        num_bets: int,
        win_probability: float,
        odds_range: tuple = (-110, -110),
        num_simulations: int = 1000
    ) -> List[BacktestResult]:
        """
        Run Monte Carlo simulation of a strategy

        Args:
            strategy_name: Name of strategy
            bet_sizing_func: Function(bankroll, odds) -> stake
            num_bets: Number of bets per simulation
            win_probability: Win probability for each bet
            odds_range: (min_odds, max_odds) range
            num_simulations: Number of simulations to run

        Returns:
            List of BacktestResult objects
        """
        results = []

        for sim in range(num_simulations):
            result = BacktestResult(f"{strategy_name}_sim_{sim}", self.starting_bankroll)
            current_bankroll = self.starting_bankroll

            for bet_num in range(num_bets):
                if current_bankroll <= 0:
                    break

                # Random odds in range
                if odds_range[0] == odds_range[1]:
                    odds = odds_range[0]
                else:
                    odds = random.randint(odds_range[0], odds_range[1])

                # Calculate stake
                stake = bet_sizing_func(current_bankroll, odds)
                stake = min(stake, current_bankroll)

                if stake <= 0:
                    continue

                # Simulate result
                won = random.random() < win_probability

                # Create bet
                bet = BetResult(datetime.now(), odds, stake, won)
                result.add_bet(bet)
                current_bankroll = result.current_bankroll

            results.append(result)

        return results

    def compare_strategies(
        self,
        strategies: Dict[str, Callable],
        historical_data: List[Dict]
    ) -> Dict[str, BacktestResult]:
        """
        Compare multiple strategies on same data

        Args:
            strategies: Dict of {strategy_name: bet_sizing_func}
            historical_data: Historical bet data

        Returns:
            Dict of {strategy_name: BacktestResult}
        """
        results = {}

        for name, sizing_func in strategies.items():
            result = self.run_historical_backtest(name, sizing_func, historical_data)
            results[name] = result

        return results


def generate_sample_data(
    num_bets: int,
    win_rate: float,
    odds_range: tuple = (-110, -110)
) -> List[Dict]:
    """Generate sample historical data"""
    data = []
    start_date = datetime.now() - timedelta(days=num_bets)

    for i in range(num_bets):
        date = start_date + timedelta(days=i)
        if odds_range[0] == odds_range[1]:
            odds = odds_range[0]
        else:
            odds = random.randint(odds_range[0], odds_range[1])

        won = random.random() < win_rate

        data.append({
            'date': date,
            'odds': odds,
            'result': won
        })

    return data


# Example strategies for backtesting

def flat_bet_strategy(bankroll: float, odds: float, bet_size: float = 10) -> float:
    """Flat betting strategy"""
    return bet_size


def percentage_strategy(bankroll: float, odds: float, percentage: float = 0.02) -> float:
    """Percentage of bankroll strategy"""
    return bankroll * percentage


def kelly_strategy(bankroll: float, odds: float, win_prob: float = 0.55) -> float:
    """Kelly criterion strategy"""
    # Calculate implied probability
    if odds > 0:
        implied_prob = 100 / (odds + 100)
    else:
        implied_prob = abs(odds) / (abs(odds) + 100)

    # Calculate decimal odds
    if odds > 0:
        decimal_odds = (odds / 100) + 1
    else:
        decimal_odds = (100 / abs(odds)) + 1

    # Kelly formula
    b = decimal_odds - 1
    p = win_prob
    q = 1 - p
    kelly = (b * p - q) / b

    # Use fractional Kelly for safety
    kelly = max(0, kelly) * 0.25

    return bankroll * kelly


if __name__ == '__main__':
    print("Backtesting Framework Demo")
    print("="*60)

    # Generate sample data
    print("\nGenerating sample data (100 bets, 54% win rate)...")
    data = generate_sample_data(100, 0.54)

    # Create backtester
    backtester = Backtester(starting_bankroll=1000)

    # Test flat betting
    print("\n1. Flat Betting ($10 per bet)")
    flat_result = backtester.run_historical_backtest(
        "Flat $10",
        lambda br, odds: 10,
        data
    )
    flat_result.print_summary()

    # Test percentage betting
    print("\n2. Percentage Betting (2% of bankroll)")
    pct_result = backtester.run_historical_backtest(
        "2% Percentage",
        lambda br, odds: br * 0.02,
        data
    )
    pct_result.print_summary()

    # Test Kelly criterion
    print("\n3. Kelly Criterion (1/4 Kelly)")
    kelly_result = backtester.run_historical_backtest(
        "Quarter Kelly",
        lambda br, odds: kelly_strategy(br, odds),
        data
    )
    kelly_result.print_summary()

    # Compare strategies
    print("\n" + "="*60)
    print("Strategy Comparison")
    print("="*60)

    all_results = [flat_result, pct_result, kelly_result]
    all_results.sort(key=lambda r: r.get_stats()['roi'], reverse=True)

    print("\nRanked by ROI:")
    for i, result in enumerate(all_results, 1):
        stats = result.get_stats()
        print(f"{i}. {stats['strategy']:15s} - ROI: {stats['roi']:+7.2f}% | "
              f"Profit: ${stats['total_profit']:+8.2f} | "
              f"Max DD: {stats['max_drawdown']:5.2f}%")
