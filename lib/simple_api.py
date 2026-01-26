#!/usr/bin/env python3
"""
Simplified API for SportsBetLang

Easy-to-use interfaces for common betting operations.
"""

from typing import Dict, List, Optional, Callable, Tuple
from lib.advanced_stats import AdvancedStats
from lib.nhl_analytics import NHLAdvancedAnalytics, ShotQuality
from lib.ml_models import RandomForest, DecisionTree, FeatureEngineering


class SBL:
    """
    SportsBetLang - Simplified API

    Quick access to common betting calculations with one-liners.
    """

    # ========================================
    # Kelly Criterion & Bet Sizing
    # ========================================

    @staticmethod
    def kelly(win_prob: float, odds: float) -> float:
        """
        Calculate Kelly Criterion bet size

        Args:
            win_prob: Win probability (0-1)
            odds: Decimal odds

        Returns:
            Optimal fraction of bankroll

        Example:
            >>> SBL.kelly(0.55, 2.0)
            0.10  # Bet 10% of bankroll
        """
        return AdvancedStats.kelly_optimal_size(win_prob, odds)

    @staticmethod
    def half_kelly(win_prob: float, odds: float) -> float:
        """Half-Kelly (conservative)"""
        return AdvancedStats.kelly_optimal_size(win_prob, odds) * 0.5

    @staticmethod
    def quarter_kelly(win_prob: float, odds: float) -> float:
        """Quarter-Kelly (very conservative)"""
        return AdvancedStats.kelly_optimal_size(win_prob, odds) * 0.25

    # ========================================
    # Expected Value
    # ========================================

    @staticmethod
    def ev(win_prob: float, odds: float, bet_amount: float) -> float:
        """
        Calculate expected value

        Args:
            win_prob: Win probability
            odds: Decimal odds
            bet_amount: Bet amount

        Returns:
            Expected value in dollars

        Example:
            >>> SBL.ev(0.55, 2.0, 100)
            10.0  # Expected profit of $10
        """
        return bet_amount * ((win_prob * (odds - 1)) - (1 - win_prob))

    @staticmethod
    def ev_percent(win_prob: float, odds: float) -> float:
        """EV as percentage"""
        return ((win_prob * (odds - 1)) - (1 - win_prob)) * 100

    # ========================================
    # Odds Conversions
    # ========================================

    @staticmethod
    def american_to_decimal(american_odds: float) -> float:
        """
        Convert American odds to decimal

        Example:
            >>> SBL.american_to_decimal(-110)
            1.909
            >>> SBL.american_to_decimal(150)
            2.5
        """
        if american_odds > 0:
            return (american_odds / 100) + 1
        return (100 / abs(american_odds)) + 1

    @staticmethod
    def decimal_to_american(decimal_odds: float) -> float:
        """Convert decimal to American odds"""
        if decimal_odds >= 2.0:
            return (decimal_odds - 1) * 100
        return -100 / (decimal_odds - 1)

    @staticmethod
    def fractional_to_decimal(numerator: float, denominator: float) -> float:
        """
        Convert fractional odds to decimal

        Example:
            >>> SBL.fractional_to_decimal(3, 1)  # 3/1
            4.0
        """
        return (numerator / denominator) + 1

    @staticmethod
    def implied_prob(decimal_odds: float) -> float:
        """
        Calculate implied probability from odds

        Example:
            >>> SBL.implied_prob(2.0)
            0.5  # 50%
        """
        return 1 / decimal_odds

    @staticmethod
    def remove_vig(odds1: float, odds2: float) -> Tuple[float, float]:
        """
        Remove vig to get true probabilities

        Returns:
            (prob1, prob2) without vig

        Example:
            >>> SBL.remove_vig(1.91, 1.91)
            (0.5, 0.5)  # True 50/50
        """
        implied1 = 1 / odds1
        implied2 = 1 / odds2
        total = implied1 + implied2
        return (implied1 / total, implied2 / total)

    # ========================================
    # Edge & Value
    # ========================================

    @staticmethod
    def edge(win_prob: float, odds: float) -> float:
        """
        Calculate edge percentage

        Example:
            >>> SBL.edge(0.55, 2.0)
            5.0  # 5% edge
        """
        return (win_prob - (1 / odds)) * 100

    @staticmethod
    def clv(bet_odds: float, closing_odds: float) -> float:
        """
        Calculate Closing Line Value

        Example:
            >>> SBL.clv(2.1, 1.95)
            7.69  # Beat closing line by 7.69%
        """
        return ((bet_odds - closing_odds) / closing_odds) * 100

    # ========================================
    # Bayesian Inference
    # ========================================

    @staticmethod
    def bayes(wins: int, losses: int) -> Dict:
        """
        Bayesian win probability

        Example:
            >>> result = SBL.bayes(12, 5)
            >>> result['mean_probability']
            0.722
        """
        return AdvancedStats.bayesian_win_probability(wins, losses)

    # ========================================
    # Monte Carlo
    # ========================================

    @staticmethod
    def simulate(func: Callable, n: int = 10000) -> Dict:
        """
        Run Monte Carlo simulation

        Example:
            >>> def sim():
            ...     return sum(1 for _ in range(16) if random.random() < 0.6)
            >>> result = SBL.simulate(sim)
            >>> result['mean']
            9.6
        """
        return AdvancedStats.monte_carlo_simulation(func, n)

    # ========================================
    # Quick Decisions
    # ========================================

    @staticmethod
    def should_bet(win_prob: float, odds: float, min_edge: float = 5.0) -> bool:
        """
        Quick bet/no-bet decision

        Example:
            >>> SBL.should_bet(0.55, 2.0, min_edge=5)
            True
        """
        edge_pct = (win_prob - (1 / odds)) * 100
        return edge_pct >= min_edge

    @staticmethod
    def roi(total_wagered: float, total_won: float) -> float:
        """
        Calculate ROI percentage

        Example:
            >>> SBL.roi(1000, 1100)
            10.0  # 10% ROI
        """
        return ((total_won - total_wagered) / total_wagered) * 100

    @staticmethod
    def breakeven_percentage(odds: float) -> float:
        """
        Win % needed to break even

        Example:
            >>> SBL.breakeven_percentage(2.0)
            50.0
        """
        return (1 / odds) * 100

    # ========================================
    # Parlays
    # ========================================

    @staticmethod
    def parlay_odds(odds_list: List[float]) -> float:
        """
        Calculate parlay odds

        Example:
            >>> SBL.parlay_odds([2.0, 1.5, 1.8])
            5.4
        """
        result = 1.0
        for odds in odds_list:
            result *= odds
        return result

    @staticmethod
    def parlay_probability(probs: List[float]) -> float:
        """
        Calculate parlay win probability

        Example:
            >>> SBL.parlay_probability([0.5, 0.6, 0.7])
            0.21  # 21%
        """
        result = 1.0
        for prob in probs:
            result *= prob
        return result

    # ========================================
    # Bankroll Management
    # ========================================

    @staticmethod
    def bet_amount(bankroll: float, kelly_fraction: float,
                   conservatism: float = 0.5) -> float:
        """
        Calculate bet amount

        Args:
            bankroll: Current bankroll
            kelly_fraction: Kelly fraction
            conservatism: 0.5 for half-Kelly, 0.25 for quarter-Kelly

        Example:
            >>> SBL.bet_amount(1000, 0.10, conservatism=0.5)
            50.0  # Bet $50
        """
        return bankroll * kelly_fraction * conservatism

    @staticmethod
    def units_to_dollars(units: float, unit_size: float) -> float:
        """Convert betting units to dollars"""
        return units * unit_size

    @staticmethod
    def dollars_to_units(dollars: float, unit_size: float) -> float:
        """Convert dollars to betting units"""
        return dollars / unit_size


class Bet:
    """
    Fluent API for bet analysis

    Allows chaining for readable bet analysis.

    Example:
        >>> bet = Bet(100).at_odds(2.1).with_probability(0.58)
        >>> bet.edge()
        10.38
        >>> bet.kelly_size()
        99.09
    """

    def __init__(self, amount: float = 100):
        """Initialize with bet amount"""
        self.amount = amount
        self.win_prob = None
        self.odds = None
        self._bankroll = 1000
        self._name = "Bet"

    def named(self, name: str):
        """Give the bet a name"""
        self._name = name
        return self

    def at_odds(self, odds: float):
        """
        Set odds (decimal)

        Example:
            >>> Bet(100).at_odds(2.1)
        """
        self.odds = odds
        return self

    def at_american(self, american_odds: float):
        """
        Set odds (American format)

        Example:
            >>> Bet(100).at_american(-110)
        """
        self.odds = SBL.american_to_decimal(american_odds)
        return self

    def with_probability(self, prob: float):
        """
        Set win probability

        Example:
            >>> Bet(100).at_odds(2.1).with_probability(0.58)
        """
        self.win_prob = prob
        return self

    def from_bankroll(self, bankroll: float):
        """
        Set bankroll size

        Example:
            >>> Bet(100).from_bankroll(5000)
        """
        self._bankroll = bankroll
        return self

    def edge(self) -> float:
        """Calculate edge percentage"""
        self._validate()
        return SBL.edge(self.win_prob, self.odds)

    def ev(self) -> float:
        """Calculate expected value"""
        self._validate()
        return SBL.ev(self.win_prob, self.odds, self.amount)

    def ev_percent(self) -> float:
        """Calculate EV as percentage"""
        self._validate()
        return SBL.ev_percent(self.win_prob, self.odds)

    def kelly_fraction(self) -> float:
        """Calculate Kelly fraction"""
        self._validate()
        return SBL.kelly(self.win_prob, self.odds)

    def kelly_size(self, conservatism: float = 0.5) -> float:
        """
        Calculate Kelly bet size

        Args:
            conservatism: 0.5 for half-Kelly (recommended)
        """
        self._validate()
        kelly = SBL.kelly(self.win_prob, self.odds)
        return self._bankroll * kelly * conservatism

    def should_bet(self, min_edge: float = 5.0) -> bool:
        """Check if bet meets minimum edge threshold"""
        self._validate()
        return self.edge() >= min_edge

    def summary(self) -> Dict:
        """
        Get complete analysis

        Returns:
            Dictionary with all metrics
        """
        self._validate()

        kelly = SBL.kelly(self.win_prob, self.odds)
        edge = self.edge()

        return {
            'name': self._name,
            'bet_amount': self.amount,
            'odds': self.odds,
            'win_probability': self.win_prob,
            'implied_probability': 1 / self.odds,
            'edge_pct': edge,
            'ev_dollars': self.ev(),
            'ev_pct': self.ev_percent(),
            'kelly_fraction': kelly,
            'kelly_bet_half': self.kelly_size(0.5),
            'kelly_bet_quarter': self.kelly_size(0.25),
            'recommendation': self._recommendation(edge)
        }

    def print_summary(self):
        """Print formatted summary"""
        summary = self.summary()

        print(f"\n{'='*60}")
        print(f"BET ANALYSIS: {summary['name']}")
        print(f"{'='*60}")
        print(f"Bet Amount:        ${summary['bet_amount']:.2f}")
        print(f"Odds:              {summary['odds']:.2f}")
        print(f"Your Probability:  {summary['win_probability']*100:.1f}%")
        print(f"Implied Prob:      {summary['implied_probability']*100:.1f}%")
        print(f"\nEDGE:              {summary['edge_pct']:.2f}%")
        print(f"Expected Value:    ${summary['ev_dollars']:.2f} ({summary['ev_pct']:.2f}%)")
        print(f"\nKelly Fraction:    {summary['kelly_fraction']*100:.2f}%")
        print(f"Half-Kelly Bet:    ${summary['kelly_bet_half']:.2f}")
        print(f"Quarter-Kelly Bet: ${summary['kelly_bet_quarter']:.2f}")
        print(f"\nRECOMMENDATION:    {summary['recommendation']}")
        print(f"{'='*60}\n")

        return self

    def _validate(self):
        """Validate that required fields are set"""
        if self.win_prob is None:
            raise ValueError("Win probability not set. Use .with_probability()")
        if self.odds is None:
            raise ValueError("Odds not set. Use .at_odds() or .at_american()")
        if not 0 < self.win_prob < 1:
            raise ValueError(f"Win probability must be between 0 and 1, got {self.win_prob}")
        if self.odds <= 1:
            raise ValueError(f"Odds must be > 1, got {self.odds}")

    @staticmethod
    def _recommendation(edge: float) -> str:
        """Get bet recommendation based on edge"""
        if edge < 0:
            return "PASS - Negative edge"
        elif edge < 2:
            return "PASS - Edge too small"
        elif edge < 5:
            return "SMALL BET - Marginal edge"
        elif edge < 10:
            return "BET - Good edge"
        else:
            return "STRONG BET - Excellent edge"


class Compare:
    """
    Compare multiple betting opportunities

    Example:
        >>> comp = Compare()
        >>> comp.add("Bet A", prob=0.58, odds=2.1)
        >>> comp.add("Bet B", prob=0.52, odds=2.3)
        >>> comp.best()
        "Bet A"
    """

    def __init__(self, bankroll: float = 1000):
        self.bankroll = bankroll
        self.bets = []

    def add(self, name: str, prob: float, odds: float):
        """Add a bet to compare"""
        bet = Bet().named(name).at_odds(odds).with_probability(prob).from_bankroll(self.bankroll)
        self.bets.append(bet)
        return self

    def best(self, metric: str = 'edge') -> str:
        """
        Find best bet by metric

        Args:
            metric: 'edge', 'ev', or 'kelly'
        """
        if not self.bets:
            return None

        if metric == 'edge':
            best_bet = max(self.bets, key=lambda b: b.edge())
        elif metric == 'ev':
            best_bet = max(self.bets, key=lambda b: b.ev())
        elif metric == 'kelly':
            best_bet = max(self.bets, key=lambda b: b.kelly_size())
        else:
            raise ValueError(f"Unknown metric: {metric}")

        return best_bet._name

    def summary(self) -> List[Dict]:
        """Get summary of all bets"""
        return [bet.summary() for bet in self.bets]

    def print_comparison(self):
        """Print formatted comparison table"""
        print(f"\n{'='*80}")
        print(f"BETTING OPPORTUNITIES COMPARISON")
        print(f"{'='*80}")
        print(f"{'Bet':<15} {'Prob':<8} {'Odds':<8} {'Edge':<10} {'EV%':<10} {'Kelly':<12}")
        print(f"{'-'*80}")

        for bet in self.bets:
            summary = bet.summary()
            print(f"{summary['name']:<15} {summary['win_probability']*100:>5.1f}%  "
                  f"{summary['odds']:<8.2f} {summary['edge_pct']:>6.2f}%  "
                  f"{summary['ev_pct']:>6.2f}%  ${summary['kelly_bet_half']:>9.2f}")

        print(f"{'-'*80}")
        print(f"Best Edge:  {self.best('edge')}")
        print(f"Best EV:    {self.best('ev')}")
        print(f"{'='*80}\n")

        return self


# Convenient aliases
kelly = SBL.kelly
ev = SBL.ev
edge = SBL.edge
bayes = SBL.bayes
simulate = SBL.simulate
