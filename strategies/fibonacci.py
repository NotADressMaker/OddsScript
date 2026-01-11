"""
Fibonacci Betting Strategy

Uses the Fibonacci sequence to determine bet sizing.
After a loss, move forward in the sequence. After a win, move back two steps.
"""


class FibonacciStrategy:
    """
    Fibonacci betting strategy implementation
    """

    def __init__(self, base_unit: float, bankroll: float, max_sequence_position: int = 15):
        """
        Initialize Fibonacci strategy

        Args:
            base_unit: Base betting unit
            bankroll: Total bankroll available
            max_sequence_position: Maximum position in Fibonacci sequence to prevent unlimited growth
        """
        self.base_unit = base_unit
        self.bankroll = bankroll
        self.max_sequence_position = max_sequence_position

        # Generate Fibonacci sequence
        self.sequence = self._generate_sequence(max_sequence_position)
        self.current_position = 0

        self.total_wagered = 0
        self.total_won = 0

    def _generate_sequence(self, length: int) -> list:
        """Generate Fibonacci sequence"""
        if length == 0:
            return []
        elif length == 1:
            return [1]

        sequence = [1, 1]
        for i in range(2, length):
            sequence.append(sequence[i - 1] + sequence[i - 2])

        return sequence

    def get_current_bet(self) -> float:
        """Get current bet size based on position in sequence"""
        multiplier = self.sequence[self.current_position]
        return self.base_unit * multiplier

    def next_bet(self, won_last: bool) -> float:
        """Calculate next bet size based on last result"""
        if won_last:
            # Move back two positions after win
            self.current_position = max(0, self.current_position - 2)
        else:
            # Move forward one position after loss
            self.current_position = min(
                len(self.sequence) - 1,
                self.current_position + 1
            )

        return self.get_current_bet()

    def can_place_bet(self) -> bool:
        """Check if we have enough bankroll for current bet"""
        return self.get_current_bet() <= self.bankroll

    def record_result(self, won: bool, payout: float = None):
        """Record bet result and update bankroll"""
        bet_size = self.get_current_bet()
        self.total_wagered += bet_size

        if won:
            if payout is None:
                payout = bet_size
            self.bankroll += payout
            self.total_won += payout
        else:
            self.bankroll -= bet_size

    def reset(self):
        """Reset to beginning of sequence"""
        self.current_position = 0

    def get_stats(self) -> dict:
        """Get strategy statistics"""
        return {
            'bankroll': self.bankroll,
            'total_wagered': self.total_wagered,
            'total_won': self.total_won,
            'net_profit': self.total_won - self.total_wagered,
            'current_position': self.current_position,
            'current_multiplier': self.sequence[self.current_position],
            'current_bet': self.get_current_bet()
        }


def simulate_fibonacci(
    base_unit: float,
    bankroll: float,
    num_bets: int,
    win_probability: float = 0.5,
    max_sequence_position: int = 15
) -> dict:
    """
    Simulate Fibonacci strategy

    Args:
        base_unit: Base betting unit
        bankroll: Initial bankroll
        num_bets: Number of bets to simulate
        win_probability: Probability of winning each bet
        max_sequence_position: Maximum position in sequence

    Returns:
        Dictionary with simulation results
    """
    import random

    strategy = FibonacciStrategy(base_unit, bankroll, max_sequence_position)
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

        bet_size = strategy.get_current_bet()
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
        'busted': busted,
        'max_position_reached': strategy.current_position
    }


if __name__ == '__main__':
    print("Fibonacci Strategy Simulation")
    print("=" * 50)

    result = simulate_fibonacci(
        base_unit=10,
        bankroll=1000,
        num_bets=100,
        win_probability=0.48
    )

    print(f"Initial Bankroll: ${result['initial_bankroll']:.2f}")
    print(f"Final Bankroll: ${result['final_bankroll']:.2f}")
    print(f"Profit/Loss: ${result['profit']:.2f}")
    print(f"ROI: {result['roi']:.2f}%")
    print(f"Bets Placed: {result['bets_placed']}")
    print(f"Wins: {result['wins']}")
    print(f"Losses: {result['losses']}")
    print(f"Win Rate: {result['win_rate']:.2f}%")
    print(f"Max Position Reached: {result['max_position_reached']}")
    print(f"Busted: {result['busted']}")
