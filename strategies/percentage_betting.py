"""
Percentage Betting Strategy

Always bet a fixed percentage of the current bankroll.
Automatically adjusts bet size as bankroll grows or shrinks.
"""


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
