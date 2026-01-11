"""
Flat Betting Strategy

The safest and most recommended strategy for long-term success.
Bet the same amount (usually 1-5% of bankroll) on each bet.
"""


class FlatBetting:
    """
    Flat betting strategy - bet same amount each time
    """

    def __init__(self, bet_size: float, bankroll: float, adjust_for_bankroll: bool = False):
        """
        Initialize flat betting strategy

        Args:
            bet_size: Fixed bet size (or percentage if adjust_for_bankroll=True)
            bankroll: Total bankroll available
            adjust_for_bankroll: If True, bet_size is percentage of current bankroll
        """
        self.initial_bet_size = bet_size
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.adjust_for_bankroll = adjust_for_bankroll

        self.total_wagered = 0
        self.total_won = 0
        self.bets_placed = 0
        self.wins = 0
        self.losses = 0

    def get_current_bet(self) -> float:
        """Get current bet size"""
        if self.adjust_for_bankroll:
            # Bet fixed percentage of current bankroll
            return self.bankroll * self.initial_bet_size
        else:
            # Bet fixed amount
            return self.initial_bet_size

    def can_place_bet(self) -> bool:
        """Check if we have enough bankroll for current bet"""
        return self.get_current_bet() <= self.bankroll

    def record_result(self, won: bool, odds: float = -110):
        """
        Record bet result and update bankroll

        Args:
            won: Whether the bet won
            odds: American odds for the bet
        """
        bet_size = self.get_current_bet()
        self.total_wagered += bet_size
        self.bets_placed += 1

        if won:
            self.wins += 1
            # Calculate payout based on American odds
            if odds > 0:
                payout = bet_size * (odds / 100)
            else:
                payout = bet_size * (100 / abs(odds))

            self.bankroll += payout
            self.total_won += payout
        else:
            self.losses += 1
            self.bankroll -= bet_size

    def get_stats(self) -> dict:
        """Get strategy statistics"""
        win_rate = (self.wins / self.bets_placed * 100) if self.bets_placed > 0 else 0
        roi = ((self.bankroll - self.initial_bankroll) / self.total_wagered * 100) if self.total_wagered > 0 else 0

        return {
            'bankroll': self.bankroll,
            'initial_bankroll': self.initial_bankroll,
            'profit': self.bankroll - self.initial_bankroll,
            'roi': roi,
            'total_wagered': self.total_wagered,
            'total_won': self.total_won,
            'bets_placed': self.bets_placed,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'current_bet_size': self.get_current_bet()
        }


class PercentageBetting:
    """
    Percentage betting - always bet a fixed percentage of current bankroll
    Automatically adjusts bet size as bankroll grows or shrinks
    """

    def __init__(self, percentage: float, bankroll: float, min_bet: float = 1.0):
        """
        Initialize percentage betting strategy

        Args:
            percentage: Percentage of bankroll to bet (e.g., 0.02 for 2%)
            bankroll: Total bankroll available
            min_bet: Minimum bet size (to avoid betting tiny amounts)
        """
        self.percentage = percentage
        self.bankroll = bankroll
        self.initial_bankroll = bankroll
        self.min_bet = min_bet

        self.total_wagered = 0
        self.bets_placed = 0
        self.wins = 0
        self.losses = 0

    def get_current_bet(self) -> float:
        """Get current bet size (percentage of current bankroll)"""
        bet = self.bankroll * self.percentage
        return max(bet, self.min_bet)

    def can_place_bet(self) -> bool:
        """Check if we have enough bankroll for current bet"""
        return self.get_current_bet() <= self.bankroll

    def record_result(self, won: bool, odds: float = -110):
        """Record bet result and update bankroll"""
        bet_size = self.get_current_bet()
        self.total_wagered += bet_size
        self.bets_placed += 1

        if won:
            self.wins += 1
            if odds > 0:
                payout = bet_size * (odds / 100)
            else:
                payout = bet_size * (100 / abs(odds))
            self.bankroll += payout
        else:
            self.losses += 1
            self.bankroll -= bet_size

    def get_stats(self) -> dict:
        """Get strategy statistics"""
        win_rate = (self.wins / self.bets_placed * 100) if self.bets_placed > 0 else 0
        roi = ((self.bankroll - self.initial_bankroll) / self.initial_bankroll * 100)

        return {
            'bankroll': self.bankroll,
            'initial_bankroll': self.initial_bankroll,
            'profit': self.bankroll - self.initial_bankroll,
            'roi': roi,
            'total_wagered': self.total_wagered,
            'bets_placed': self.bets_placed,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'current_bet_size': self.get_current_bet(),
            'percentage': self.percentage * 100
        }


def compare_strategies(
    starting_bankroll: float,
    num_bets: int,
    win_probability: float = 0.52,
    odds: float = -110
) -> dict:
    """
    Compare flat betting vs percentage betting

    Args:
        starting_bankroll: Initial bankroll
        num_bets: Number of bets to simulate
        win_probability: Probability of winning each bet
        odds: American odds for each bet

    Returns:
        Dictionary comparing both strategies
    """
    import random

    # Flat betting: 2% of starting bankroll
    flat = FlatBetting(starting_bankroll * 0.02, starting_bankroll, adjust_for_bankroll=False)

    # Percentage betting: 2% of current bankroll
    percentage = PercentageBetting(0.02, starting_bankroll)

    for _ in range(num_bets):
        won = random.random() < win_probability

        if flat.can_place_bet():
            flat.record_result(won, odds)

        if percentage.can_place_bet():
            percentage.record_result(won, odds)

    return {
        'flat_betting': flat.get_stats(),
        'percentage_betting': percentage.get_stats()
    }


if __name__ == '__main__':
    print("Flat Betting vs Percentage Betting")
    print("=" * 50)

    results = compare_strategies(
        starting_bankroll=1000,
        num_bets=100,
        win_probability=0.54,  # Slight edge
        odds=-110
    )

    print("\nFlat Betting (2% of starting bankroll):")
    flat_stats = results['flat_betting']
    print(f"  Final Bankroll: ${flat_stats['bankroll']:.2f}")
    print(f"  Profit: ${flat_stats['profit']:.2f}")
    print(f"  ROI: {flat_stats['roi']:.2f}%")
    print(f"  Win Rate: {flat_stats['win_rate']:.2f}%")

    print("\nPercentage Betting (2% of current bankroll):")
    pct_stats = results['percentage_betting']
    print(f"  Final Bankroll: ${pct_stats['bankroll']:.2f}")
    print(f"  Profit: ${pct_stats['profit']:.2f}")
    print(f"  ROI: {pct_stats['roi']:.2f}%")
    print(f"  Win Rate: {pct_stats['win_rate']:.2f}%")
