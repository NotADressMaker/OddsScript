"""
Martingale Betting Strategy

WARNING: This is a high-risk strategy. Use for educational purposes only.
The Martingale strategy doubles your bet after each loss to recover losses.
"""


class MartingaleStrategy:
    """
    Martingale betting strategy implementation
    Doubles bet size after each loss
    """

    def __init__(self, base_bet: float, max_bet: float, bankroll: float):
        """
        Initialize Martingale strategy

        Args:
            base_bet: Starting bet size
            max_bet: Maximum allowed bet (table limit or personal limit)
            bankroll: Total bankroll available
        """
        self.base_bet = base_bet
        self.max_bet = max_bet
        self.bankroll = bankroll
        self.current_bet = base_bet
        self.consecutive_losses = 0
        self.total_wagered = 0
        self.total_won = 0

    def next_bet(self, won_last: bool) -> float:
        """Calculate next bet size based on last result"""
        if won_last:
            # Reset to base bet after win
            self.consecutive_losses = 0
            self.current_bet = self.base_bet
        else:
            # Double bet after loss
            self.consecutive_losses += 1
            self.current_bet = min(self.current_bet * 2, self.max_bet, self.bankroll)

        return self.current_bet

    def can_place_bet(self) -> bool:
        """Check if we have enough bankroll for current bet"""
        return self.current_bet <= self.bankroll

    def record_result(self, won: bool, payout: float = None):
        """Record bet result and update bankroll"""
        self.total_wagered += self.current_bet

        if won:
            if payout is None:
                payout = self.current_bet  # 1:1 payout
            self.bankroll += payout
            self.total_won += payout
        else:
            self.bankroll -= self.current_bet

    def get_stats(self) -> dict:
        """Get strategy statistics"""
        return {
            'bankroll': self.bankroll,
            'total_wagered': self.total_wagered,
            'total_won': self.total_won,
            'net_profit': self.total_won - self.total_wagered,
            'consecutive_losses': self.consecutive_losses,
            'current_bet': self.current_bet
        }

    def max_losing_streak(self) -> int:
        """Calculate maximum number of losses before exceeding limits"""
        bet = self.base_bet
        losses = 0

        while bet <= self.max_bet and bet <= self.bankroll:
            losses += 1
            bet *= 2

        return losses - 1


class ReverseMartingale:
    """
    Reverse Martingale (Paroli) strategy
    Doubles bet after each WIN instead of loss
    """

    def __init__(self, base_bet: float, max_progression: int, bankroll: float):
        """
        Initialize Reverse Martingale strategy

        Args:
            base_bet: Starting bet size
            max_progression: Maximum number of times to double (e.g., 3 = bet, double, double)
            bankroll: Total bankroll available
        """
        self.base_bet = base_bet
        self.max_progression = max_progression
        self.bankroll = bankroll
        self.current_bet = base_bet
        self.consecutive_wins = 0

    def next_bet(self, won_last: bool) -> float:
        """Calculate next bet size based on last result"""
        if won_last and self.consecutive_wins < self.max_progression:
            # Double bet after win (up to max progression)
            self.consecutive_wins += 1
            self.current_bet = min(self.current_bet * 2, self.bankroll)
        else:
            # Reset to base bet after loss or reaching max progression
            self.consecutive_wins = 0
            self.current_bet = self.base_bet

        return self.current_bet

    def can_place_bet(self) -> bool:
        """Check if we have enough bankroll for current bet"""
        return self.current_bet <= self.bankroll


def simulate_martingale(
    base_bet: float,
    bankroll: float,
    max_bet: float,
    num_bets: int,
    win_probability: float = 0.5
) -> dict:
    """
    Simulate Martingale strategy

    Args:
        base_bet: Starting bet size
        bankroll: Initial bankroll
        max_bet: Maximum bet allowed
        num_bets: Number of bets to simulate
        win_probability: Probability of winning each bet

    Returns:
        Dictionary with simulation results
    """
    import random

    strategy = MartingaleStrategy(base_bet, max_bet, bankroll)
    initial_bankroll = bankroll
    max_bankroll = bankroll
    min_bankroll = bankroll
    bets_placed = 0
    wins = 0
    losses = 0
    busted = False

    for i in range(num_bets):
        if not strategy.can_place_bet():
            busted = True
            break

        bet_size = strategy.current_bet
        won = random.random() < win_probability

        if won:
            wins += 1
            strategy.record_result(True, bet_size)
        else:
            losses += 1
            strategy.record_result(False)

        bets_placed += 1
        max_bankroll = max(max_bankroll, strategy.bankroll)
        min_bankroll = min(min_bankroll, strategy.bankroll)

        strategy.next_bet(won)

    return {
        'initial_bankroll': initial_bankroll,
        'final_bankroll': strategy.bankroll,
        'profit': strategy.bankroll - initial_bankroll,
        'roi': ((strategy.bankroll - initial_bankroll) / initial_bankroll) * 100,
        'bets_placed': bets_placed,
        'wins': wins,
        'losses': losses,
        'win_rate': (wins / bets_placed * 100) if bets_placed > 0 else 0,
        'max_bankroll': max_bankroll,
        'min_bankroll': min_bankroll,
        'busted': busted
    }


if __name__ == '__main__':
    # Example usage
    print("Martingale Strategy Simulation")
    print("=" * 50)

    result = simulate_martingale(
        base_bet=10,
        bankroll=1000,
        max_bet=500,
        num_bets=100,
        win_probability=0.48  # Slightly less than 50% to simulate house edge
    )

    print(f"Initial Bankroll: ${result['initial_bankroll']:.2f}")
    print(f"Final Bankroll: ${result['final_bankroll']:.2f}")
    print(f"Profit/Loss: ${result['profit']:.2f}")
    print(f"ROI: {result['roi']:.2f}%")
    print(f"Bets Placed: {result['bets_placed']}")
    print(f"Wins: {result['wins']}")
    print(f"Losses: {result['losses']}")
    print(f"Win Rate: {result['win_rate']:.2f}%")
    print(f"Busted: {result['busted']}")
