"""
Kelly Criterion betting strategy.

Mathematically optimal strategy for maximizing long-term bankroll growth.
"""

from typing import Dict, Any
from sportsbetlang.strategies.base import (
    BettingStrategy,
    BetRecommendation,
    BetAction,
    register_strategy
)
from sportsbetlang.common.kelly import calculate_kelly as calc_kelly
from sportsbetlang.common.validators import (
    validate_bankroll,
    validate_odds,
    validate_kelly_fraction
)


@register_strategy
class KellyStrategy(BettingStrategy):
    """Kelly Criterion optimal bet sizing strategy"""

    @property
    def name(self) -> str:
        return "kelly"

    @property
    def description(self) -> str:
        return "Kelly Criterion for optimal bet sizing (maximizes log bankroll growth)"

    @property
    def version(self) -> str:
        return "2.0.0"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'kelly_fraction': 0.25,  # Quarter Kelly (recommended)
            'min_edge': 0.01,        # Minimum 1% edge to bet
            'max_stake_pct': 0.10    # Never bet more than 10% of bankroll
        }

    def validate_parameters(self, **kwargs):
        """Validate Kelly parameters"""
        if 'kelly_fraction' in kwargs:
            validate_kelly_fraction(kwargs['kelly_fraction'])

        if 'min_edge' in kwargs:
            min_edge = kwargs['min_edge']
            if not 0 <= min_edge <= 1:
                raise ValueError(f"min_edge must be 0-1, got {min_edge}")

        if 'max_stake_pct' in kwargs:
            max_stake = kwargs['max_stake_pct']
            if not 0 < max_stake <= 1:
                raise ValueError(f"max_stake_pct must be 0-1, got {max_stake}")

    def calculate_stake(
        self,
        bankroll: float,
        odds: float,
        edge: float,
        kelly_fraction: float = 0.25,
        min_edge: float = 0.01,
        max_stake_pct: float = 0.10,
        **kwargs
    ) -> BetRecommendation:
        """
        Calculate Kelly stake

        Args:
            bankroll: Current bankroll
            odds: American odds
            edge: Your edge over the market (as decimal)
            kelly_fraction: Fraction of full Kelly to use (default: 0.25)
            min_edge: Minimum edge required to bet (default: 0.01)
            max_stake_pct: Maximum % of bankroll to stake (default: 0.10)

        Returns:
            BetRecommendation
        """
        # Validate inputs
        validate_bankroll(bankroll)
        validate_odds(odds)
        self.validate_parameters(
            kelly_fraction=kelly_fraction,
            min_edge=min_edge,
            max_stake_pct=max_stake_pct
        )

        # Check minimum edge requirement
        if edge < min_edge:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Edge {edge*100:.2f}% below minimum {min_edge*100:.2f}%",
                action=BetAction.NO_BET,
                metadata={'edge': edge, 'min_edge': min_edge}
            )

        # Calculate Kelly from edge
        # Edge = true_prob - market_prob
        # Need to convert edge back to true probability
        from sportsbetlang.common.odds import implied_probability
        market_prob = float(implied_probability(odds))
        true_prob = market_prob + edge

        # Ensure probability is valid
        if true_prob <= 0 or true_prob >= 1:
            return BetRecommendation(
                should_bet=False,
                stake=0.0,
                confidence=0.0,
                reasoning=f"Invalid true probability {true_prob:.3f} (must be 0-1)",
                action=BetAction.NO_BET,
                metadata={'true_prob': true_prob}
            )

        # Calculate Kelly
        result = calc_kelly(
            odds=odds,
            true_prob=true_prob,
            kelly_fraction=kelly_fraction,
            bankroll=bankroll
        )

        stake = result['stake']
        kelly_pct = result['fractional_kelly']

        # Apply maximum stake limit
        max_stake = bankroll * max_stake_pct
        if stake > max_stake:
            stake = max_stake
            kelly_pct = max_stake_pct
            capped = True
        else:
            capped = False

        # Determine if we should bet
        should_bet = stake >= 1.0  # Minimum $1 bet

        # Calculate confidence based on edge and Kelly percentage
        # Higher edge and reasonable Kelly = higher confidence
        confidence = min(1.0, (edge / 0.10) * 0.5 + (kelly_pct / 0.05) * 0.5)

        # Build reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Edge: {edge*100:+.2f}%")
        reasoning_parts.append(f"Kelly: {kelly_pct*100:.2f}% of bankroll")

        if capped:
            reasoning_parts.append(f"(capped at {max_stake_pct*100:.0f}%)")

        reasoning_parts.append(f"EV: ${result['expected_profit']:.2f}")

        reasoning = ", ".join(reasoning_parts)

        return BetRecommendation(
            should_bet=should_bet,
            stake=stake if should_bet else 0.0,
            confidence=confidence,
            reasoning=reasoning,
            action=BetAction.BET if should_bet else BetAction.NO_BET,
            metadata={
                'edge': edge,
                'kelly_pct': kelly_pct,
                'kelly_fraction': kelly_fraction,
                'ev': result['ev'],
                'expected_profit': result['expected_profit'],
                'capped': capped,
                'true_prob': true_prob,
                'market_prob': market_prob
            }
        )


@register_strategy
class FullKellyStrategy(KellyStrategy):
    """Full Kelly (aggressive, high variance)"""

    @property
    def name(self) -> str:
        return "full-kelly"

    @property
    def description(self) -> str:
        return "Full Kelly Criterion (aggressive, maximizes growth but high variance)"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'kelly_fraction': 1.0,   # Full Kelly
            'min_edge': 0.02,        # Higher minimum edge for safety
            'max_stake_pct': 0.20    # Higher max for aggressive strategy
        }


@register_strategy
class ConservativeKellyStrategy(KellyStrategy):
    """Conservative Kelly (1/8 Kelly)"""

    @property
    def name(self) -> str:
        return "conservative-kelly"

    @property
    def description(self) -> str:
        return "Conservative Kelly (1/8 Kelly for minimal variance)"

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            'kelly_fraction': 0.125,  # 1/8 Kelly
            'min_edge': 0.005,        # Lower minimum edge
            'max_stake_pct': 0.05     # Conservative max
        }


# Export strategies
__all__ = [
    'KellyStrategy',
    'FullKellyStrategy',
    'ConservativeKellyStrategy',
]
