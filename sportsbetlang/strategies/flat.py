"""
Flat betting strategies.

Simple, consistent stake sizing regardless of edge or odds.
"""

from typing import Dict, Any
from sportsbetlang.strategies.base import (
    BettingStrategy,
    BetRecommendation,
    BetAction,
    register_strategy
)
from sportsbetlang.common.validators import validate_bankroll, validate_odds


@register_strategy
class FlatBettingStrategy(BettingStrategy):
    """Flat betting - same stake every bet"""

    @property
    def name(self) -> str:
        return "flat"

    @property
    def description(self) -> str:
        return "Flat betting with fixed stake amount (simple and safe)"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'stake_amount': 100.0,   # Fixed dollar amount
            'min_edge': 0.01         # Minimum edge to bet
        }

    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        stake_amount: float = 100.0,
        min_edge: float = 0.01,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate flat stake

        Args:
            bankroll: Current bankroll (informational only)
            odds: American odds (informational only)
            edge: Your edge
            stake_amount: Fixed stake amount
            min_edge: Minimum edge to bet

        Returns:
            BetRecommendation
        """
        validate_bankroll(bankroll)
        validate_odds(odds)

        # Check minimum edge
        if edge < min_edge:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Edge {edge*100:.2f}% below minimum {min_edge*100:.2f}%",
                action=BetAction.NO_BET,
                metadata={'edge': edge}
            )

        # Check if stake exceeds bankroll
        if stake_amount > bankroll:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Stake ${stake_amount:.2f} exceeds bankroll ${bankroll:.2f}",
                action=BetAction.NO_BET,
                metadata={'stake_amount': stake_amount, 'bankroll': bankroll}
            )

        # Calculate confidence based on edge
        confidence = min(1.0, edge / 0.10)  # 10% edge = 100% confidence

        return BetRecommendation(
            should_bet=True,
            stake=stake_amount,
            confidence=confidence,
            reasoning=f"Flat ${stake_amount:.2f} with {edge*100:+.2f}% edge",
            action=BetAction.BET,
            metadata={
                'edge': edge,
                'stake_amount': stake_amount,
                'pct_of_bankroll': (stake_amount / bankroll) * 100
            }
        )


@register_strategy
class PercentageBettingStrategy(BettingStrategy):
    """Percentage betting - fixed % of bankroll"""

    @property
    def name(self) -> str:
        return "percentage"

    @property
    def description(self) -> str:
        return "Bet a fixed percentage of bankroll (scales with bankroll)"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'stake_pct': 0.02,       # 2% of bankroll
            'min_edge': 0.01         # Minimum edge to bet
        }

    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        stake_pct: float = 0.02,
        min_edge: float = 0.01,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate percentage-based stake

        Args:
            bankroll: Current bankroll
            odds: American odds (informational)
            edge: Your edge
            stake_pct: Percentage of bankroll to stake
            min_edge: Minimum edge to bet

        Returns:
            BetRecommendation
        """
        validate_bankroll(bankroll)
        validate_odds(odds)

        if not 0 < stake_pct <= 1:
            raise ValueError(f"stake_pct must be 0-1, got {stake_pct}")

        # Check minimum edge
        if edge < min_edge:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Edge {edge*100:.2f}% below minimum {min_edge*100:.2f}%",
                action=BetAction.NO_BET,
                metadata={'edge': edge}
            )

        # Calculate stake
        stake = bankroll * stake_pct

        # Confidence based on edge
        confidence = min(1.0, edge / 0.10)

        return BetRecommendation(
            should_bet=True,
            stake=stake,
            confidence=confidence,
            reasoning=f"{stake_pct*100:.1f}% of bankroll = ${stake:.2f} with {edge*100:+.2f}% edge",
            action=BetAction.BET,
            metadata={
                'edge': edge,
                'stake_pct': stake_pct,
                'bankroll': bankroll
            }
        )


@register_strategy
class UnitBettingStrategy(BettingStrategy):
    """Unit-based betting - bet in units"""

    @property
    def name(self) -> str:
        return "unit"

    @property
    def description(self) -> str:
        return "Bet in units (1 unit = 1% of starting bankroll)"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'starting_bankroll': 1000.0,  # Starting bankroll
            'units': 1.0,                  # Units to bet
            'min_edge': 0.01               # Minimum edge
        }

    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        starting_bankroll: float = 1000.0,
        units: float = 1.0,
        min_edge: float = 0.01,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate unit-based stake

        Args:
            bankroll: Current bankroll
            odds: American odds
            edge: Your edge
            starting_bankroll: Original starting bankroll
            units: Number of units to bet
            min_edge: Minimum edge

        Returns:
            BetRecommendation
        """
        validate_bankroll(bankroll)
        validate_odds(odds)

        # Check minimum edge
        if edge < min_edge:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Edge {edge*100:.2f}% below minimum {min_edge*100:.2f}%",
                action=BetAction.NO_BET,
                metadata={'edge': edge}
            )

        # 1 unit = 1% of starting bankroll
        unit_size = starting_bankroll * 0.01
        stake = units * unit_size

        # Check if stake exceeds current bankroll
        if stake > bankroll:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"{units} units (${stake:.2f}) exceeds bankroll ${bankroll:.2f}",
                action=BetAction.NO_BET,
                metadata={'stake': stake, 'bankroll': bankroll}
            )

        # Confidence based on edge
        confidence = min(1.0, edge / 0.10)

        return BetRecommendation(
            should_bet=True,
            stake=stake,
            confidence=confidence,
            reasoning=f"{units} unit(s) = ${stake:.2f} with {edge*100:+.2f}% edge",
            action=BetAction.BET,
            metadata={
                'edge': edge,
                'units': units,
                'unit_size': unit_size,
                'starting_bankroll': starting_bankroll
            }
        )


# Export strategies
__all__ = [
    'FlatBettingStrategy',
    'PercentageBettingStrategy',
    'UnitBettingStrategy',
]
