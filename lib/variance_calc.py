"""
Variance Calculator for Sports Betting

Understand bankroll variance and calculate required bankroll for risk tolerance.
"""

import math
from typing import List, Tuple


class VarianceCalculator:
    """Calculate variance and risk of ruin for betting"""

    @staticmethod
    def calculate_variance(
        win_rate: float,
        avg_odds: float,
        bet_size: float
    ) -> float:
        """
        Calculate variance per bet

        Args:
            win_rate: Win rate as decimal (e.g., 0.54)
            avg_odds: Average odds (American)
            bet_size: Size of each bet

        Returns:
            Variance per bet
        """
        # Calculate payout multiplier
        if avg_odds > 0:
            win_mult = avg_odds / 100
        else:
            win_mult = 100 / abs(avg_odds)

        # Variance = p * (win)^2 + (1-p) * (loss)^2 - (expected_value)^2
        win_amount = bet_size * win_mult
        loss_amount = bet_size

        ev = (win_rate * win_amount) - ((1 - win_rate) * loss_amount)

        variance = (win_rate * (win_amount ** 2) +
                   (1 - win_rate) * (loss_amount ** 2) -
                   (ev ** 2))

        return variance

    @staticmethod
    def standard_deviation(
        win_rate: float,
        avg_odds: float,
        bet_size: float,
        num_bets: int
    ) -> float:
        """
        Calculate standard deviation over N bets

        Args:
            win_rate: Win rate as decimal
            avg_odds: Average odds
            bet_size: Bet size
            num_bets: Number of bets

        Returns:
            Standard deviation
        """
        variance = VarianceCalculator.calculate_variance(win_rate, avg_odds, bet_size)
        total_variance = variance * num_bets
        return math.sqrt(total_variance)

    @staticmethod
    def confidence_interval(
        win_rate: float,
        avg_odds: float,
        bet_size: float,
        num_bets: int,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval for profit after N bets

        Args:
            win_rate: Win rate as decimal
            avg_odds: Average odds
            bet_size: Bet size
            num_bets: Number of bets
            confidence: Confidence level (0.95 = 95%)

        Returns:
            (lower_bound, upper_bound) for profit
        """
        # Expected value
        if avg_odds > 0:
            win_mult = avg_odds / 100
        else:
            win_mult = 100 / abs(avg_odds)

        win_amount = bet_size * win_mult
        loss_amount = bet_size

        ev_per_bet = (win_rate * win_amount) - ((1 - win_rate) * loss_amount)
        expected_profit = ev_per_bet * num_bets

        # Standard deviation
        std_dev = VarianceCalculator.standard_deviation(
            win_rate, avg_odds, bet_size, num_bets
        )

        # Z-score for confidence level
        if confidence == 0.95:
            z = 1.96
        elif confidence == 0.99:
            z = 2.576
        elif confidence == 0.90:
            z = 1.645
        else:
            z = 1.96  # default

        margin = z * std_dev

        return (expected_profit - margin, expected_profit + margin)

    @staticmethod
    def risk_of_ruin(
        bankroll: float,
        edge: float,
        win_rate: float,
        bet_size: float
    ) -> float:
        """
        Calculate risk of ruin (probability of going broke)

        Simplified formula for equal bet sizes

        Args:
            bankroll: Starting bankroll
            edge: Edge as decimal (e.g., 0.02 for 2%)
            win_rate: Win rate as decimal
            bet_size: Bet size

        Returns:
            Risk of ruin as probability
        """
        # Number of bets until broke
        max_losses = bankroll / bet_size

        # Using simplified formula
        if edge <= 0:
            return 1.0  # Certain ruin with no edge

        # Calculate using exponential formula
        # RoR = ((1-p)/p)^(bankroll/unit) where p = win probability with edge
        loss_rate = 1 - win_rate

        if win_rate >= 1.0:
            return 0.0

        ratio = loss_rate / win_rate

        # Account for edge
        adjusted_ratio = ratio * (1 - edge)

        if adjusted_ratio >= 1:
            return 1.0

        ror = adjusted_ratio ** max_losses

        return min(1.0, ror)

    @staticmethod
    def required_bankroll(
        risk_tolerance: float,
        edge: float,
        win_rate: float,
        bet_size: float
    ) -> float:
        """
        Calculate required bankroll for risk tolerance

        Args:
            risk_tolerance: Acceptable risk of ruin (e.g., 0.01 for 1%)
            edge: Edge as decimal
            win_rate: Win rate as decimal
            bet_size: Bet size

        Returns:
            Required bankroll
        """
        if edge <= 0 or win_rate >= 1.0:
            return float('inf')

        loss_rate = 1 - win_rate
        ratio = (loss_rate / win_rate) * (1 - edge)

        if ratio >= 1:
            return float('inf')

        # Solve: risk_tolerance = ratio^(bankroll/bet_size)
        # bankroll = bet_size * log(risk_tolerance) / log(ratio)

        if risk_tolerance <= 0:
            return float('inf')

        units_needed = math.log(risk_tolerance) / math.log(ratio)
        return units_needed * bet_size

    @staticmethod
    def kelly_variance(
        true_prob: float,
        odds: float,
        bankroll: float,
        num_bets: int
    ) -> dict:
        """
        Calculate variance when using Kelly criterion

        Args:
            true_prob: True win probability
            odds: Odds (American)
            bankroll: Starting bankroll
            num_bets: Number of bets to simulate

        Returns:
            Variance statistics
        """
        # Calculate Kelly percentage
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1

        b = decimal_odds - 1
        p = true_prob
        q = 1 - p

        kelly = (b * p - q) / b
        kelly = max(0, kelly)

        # Calculate variance with Kelly sizing
        # Note: Kelly sizing changes each bet, so this is approximate
        current_bankroll = bankroll

        # Approximate by using average bet size
        avg_bet = bankroll * kelly * 0.5  # Rough approximation

        variance = VarianceCalculator.calculate_variance(
            true_prob, odds, avg_bet
        )

        std_dev = math.sqrt(variance * num_bets)

        # Expected growth rate with Kelly
        growth_rate = p * math.log(1 + b * kelly) + q * math.log(1 - kelly)
        expected_bankroll = bankroll * math.exp(growth_rate * num_bets)

        return {
            'kelly_percent': kelly * 100,
            'avg_bet_size': avg_bet,
            'variance_per_bet': variance,
            'std_dev': std_dev,
            'expected_bankroll': expected_bankroll,
            'growth_rate': growth_rate
        }


def analyze_variance(
    win_rate: float,
    avg_odds: float,
    bankroll: float,
    bet_size: float,
    num_bets: int
):
    """Print comprehensive variance analysis"""
    calc = VarianceCalculator()

    print(f"\n{'='*60}")
    print(f"Variance Analysis")
    print(f"{'='*60}")

    print(f"\nParameters:")
    print(f"  Win Rate: {win_rate*100:.2f}%")
    print(f"  Average Odds: {avg_odds:+.0f}")
    print(f"  Bankroll: ${bankroll:.2f}")
    print(f"  Bet Size: ${bet_size:.2f}")
    print(f"  Number of Bets: {num_bets}")

    # Calculate edge
    if avg_odds > 0:
        implied_prob = 100 / (avg_odds + 100)
    else:
        implied_prob = abs(avg_odds) / (abs(avg_odds) + 100)

    edge = win_rate - implied_prob

    print(f"\n  Implied Probability: {implied_prob*100:.2f}%")
    print(f"  Your Edge: {edge*100:+.2f}%")

    # Variance
    variance = calc.calculate_variance(win_rate, avg_odds, bet_size)
    std_dev = calc.standard_deviation(win_rate, avg_odds, bet_size, num_bets)

    print(f"\nVariance:")
    print(f"  Variance per bet: ${variance:.2f}")
    print(f"  Std Dev ({num_bets} bets): ${std_dev:.2f}")

    # Expected value
    if avg_odds > 0:
        win_amount = bet_size * (avg_odds / 100)
    else:
        win_amount = bet_size * (100 / abs(avg_odds))

    ev_per_bet = (win_rate * win_amount) - ((1 - win_rate) * bet_size)
    expected_profit = ev_per_bet * num_bets

    print(f"\nExpected Value:")
    print(f"  EV per bet: ${ev_per_bet:+.2f}")
    print(f"  Expected profit ({num_bets} bets): ${expected_profit:+.2f}")

    # Confidence intervals
    lower_95, upper_95 = calc.confidence_interval(
        win_rate, avg_odds, bet_size, num_bets, 0.95
    )
    lower_99, upper_99 = calc.confidence_interval(
        win_rate, avg_odds, bet_size, num_bets, 0.99
    )

    print(f"\nConfidence Intervals:")
    print(f"  95% CI: ${lower_95:+.2f} to ${upper_95:+.2f}")
    print(f"  99% CI: ${lower_99:+.2f} to ${upper_99:+.2f}")

    # Risk of ruin
    ror = calc.risk_of_ruin(bankroll, edge, win_rate, bet_size)

    print(f"\nRisk of Ruin:")
    print(f"  Probability: {ror*100:.4f}%")

    if ror < 0.01:
        print(f"  ✓ Very low risk")
    elif ror < 0.05:
        print(f"  ✓ Acceptable risk")
    elif ror < 0.10:
        print(f"  ~ Moderate risk")
    else:
        print(f"  ✗ High risk - reduce bet size!")

    # Required bankroll
    req_br_1pct = calc.required_bankroll(0.01, edge, win_rate, bet_size)
    req_br_5pct = calc.required_bankroll(0.05, edge, win_rate, bet_size)

    print(f"\nRequired Bankroll:")
    print(f"  For 1% RoR: ${req_br_1pct:.2f}")
    print(f"  For 5% RoR: ${req_br_5pct:.2f}")

    if bankroll < req_br_5pct:
        print(f"\n  ⚠️  Warning: Bankroll below recommended level")
        print(f"      Consider reducing bet size to ${bankroll * 0.02:.2f}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Variance Calculator')
    parser.add_argument('-w', '--winrate', type=float, required=True,
                       help='Win rate (0-1, e.g., 0.54)')
    parser.add_argument('-o', '--odds', type=float, required=True,
                       help='Average odds (American)')
    parser.add_argument('-b', '--bankroll', type=float, required=True,
                       help='Bankroll size')
    parser.add_argument('-s', '--stake', type=float, required=True,
                       help='Bet size')
    parser.add_argument('-n', '--numbets', type=int, default=100,
                       help='Number of bets (default: 100)')

    args = parser.parse_args()

    analyze_variance(
        args.winrate,
        args.odds,
        args.bankroll,
        args.stake,
        args.numbets
    )
