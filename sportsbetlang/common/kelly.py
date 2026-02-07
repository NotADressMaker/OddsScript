"""
Kelly Criterion calculations - single implementation for all tools.

The Kelly Criterion is the mathematically optimal bet sizing formula for
maximizing long-term bankroll growth.
"""

from typing import Optional, Dict, List
from decimal import Decimal
import math


class KellyCriterion:
    """Kelly criterion for optimal bet sizing"""

    @staticmethod
    def calculate(
        odds: float,
        true_prob: float,
        kelly_fraction: float = 1.0,
        bankroll: Optional[float] = None,
        max_stake_pct: Optional[float] = None,
        allow_full_kelly: Optional[bool] = None,
        sample_size: Optional[int] = None,
        confidence_calibrated: Optional[bool] = None,
        min_sample_size_warning: Optional[int] = None,
        require_confidence_calibration: Optional[bool] = None
    ) -> Dict:
        """
        Calculate Kelly stake

        Args:
            odds: American odds
            true_prob: Your true probability estimate (0-1)
            kelly_fraction: Fraction of full Kelly to bet (default 1.0, recommend 0.25)
            bankroll: Optional bankroll for absolute stake calculation

        Returns:
            Dictionary with:
                - kelly_pct: Full Kelly percentage
                - fractional_kelly: Adjusted Kelly percentage
                - kelly_fraction: The fraction used
                - ev: Expected value
                - edge: Your edge over the market
                - recommended: 'BET' or 'NO BET'
                - stake: Absolute stake (if bankroll provided)

        Examples:
            >>> KellyCriterion.calculate(odds=-110, true_prob=0.55, kelly_fraction=0.25, bankroll=1000)
            {'kelly_pct': 0.047..., 'fractional_kelly': 0.011..., 'stake': 11.9...}
        """
        from sportsbetlang.common.odds import american_to_decimal
        from sportsbetlang.config import get_config

        config = get_config()
        warnings: List[str] = []

        if allow_full_kelly is None:
            allow_full_kelly = config.allow_full_kelly
        if max_stake_pct is None:
            max_stake_pct = config.max_kelly_pct
        if min_sample_size_warning is None:
            min_sample_size_warning = config.min_sample_size_warning
        if require_confidence_calibration is None:
            require_confidence_calibration = config.require_confidence_calibration

        if kelly_fraction >= 1.0 and not allow_full_kelly:
            warnings.append(
                "Full Kelly sizing is disabled by default. "
                f"Using fractional Kelly ({config.kelly_fraction:.2f}) instead."
            )
            kelly_fraction = config.kelly_fraction

        if sample_size is not None and sample_size < min_sample_size_warning:
            warnings.append(
                f"Sample size ({sample_size}) is below the recommended minimum "
                f"({min_sample_size_warning}). Treat sizing as exploratory."
            )

        if require_confidence_calibration and confidence_calibrated is False:
            warnings.append(
                "Model confidence is uncalibrated. Use smaller stakes or calibrate first."
            )

        # Convert to decimal odds
        decimal_odds = american_to_decimal(odds)
        b = decimal_odds - 1  # Net odds (profit per unit staked)

        # Kelly formula: (bp - q) / b
        # where p = win probability, q = loss probability
        p = true_prob
        q = 1 - p

        # Full Kelly percentage
        kelly_pct = (b * p - q) / b

        # Apply fractional Kelly (safety margin)
        fractional_kelly = kelly_pct * kelly_fraction

        # Ensure non-negative (no bet if negative Kelly)
        fractional_kelly = max(0, fractional_kelly)

        # Cap maximum stake percentage
        if max_stake_pct is not None and fractional_kelly > max_stake_pct:
            warnings.append(
                f"Stake capped at {max_stake_pct:.2%} of bankroll (max_stake_pct)."
            )
            fractional_kelly = max_stake_pct

        # Calculate expected value (per unit staked)
        ev = p * b - q

        # Calculate edge
        from sportsbetlang.common.odds import implied_probability
        market_prob = implied_probability(odds)
        edge = p - market_prob

        # Build result
        result = {
            'kelly_pct': kelly_pct,
            'fractional_kelly': fractional_kelly,
            'kelly_fraction': kelly_fraction,
            'ev': ev,
            'edge': edge,
            'true_prob': true_prob,
            'market_prob': market_prob,
            'recommended': 'BET' if fractional_kelly > 0.001 else 'NO BET',  # Min 0.1% of bankroll
            'warnings': warnings
        }

        # Calculate absolute stake if bankroll provided
        if bankroll is not None:
            result['stake'] = fractional_kelly * bankroll
            result['expected_profit'] = result['stake'] * ev

        return result

    @staticmethod
    def calculate_variance(
        odds: float,
        true_prob: float,
        kelly_fraction: float = 0.25,
        n_bets: int = 100
    ) -> Dict:
        """
        Calculate Kelly variance and risk metrics

        Args:
            odds: American odds
            true_prob: True probability
            kelly_fraction: Kelly fraction
            n_bets: Number of bets to simulate

        Returns:
            Variance statistics
        """
        from sportsbetlang.common.odds import american_to_decimal

        decimal_odds = american_to_decimal(odds)
        b = decimal_odds - 1

        p = true_prob
        q = 1 - p

        # Kelly percentage
        kelly_pct = (b * p - q) / b
        f = kelly_pct * kelly_fraction  # Fraction of bankroll

        # Variance of a single bet
        # Var(X) = E[X^2] - E[X]^2
        win_return = b * f  # Return if win
        loss_return = -f    # Return if loss

        ev = p * win_return + q * loss_return
        ev_squared = p * (win_return ** 2) + q * (loss_return ** 2)
        variance = ev_squared - (ev ** 2)
        std_dev = math.sqrt(variance)

        # For n independent bets
        total_variance = variance * n_bets
        total_std_dev = math.sqrt(total_variance)

        # Expected growth
        expected_growth = (1 + ev) ** n_bets

        return {
            'single_bet_variance': variance,
            'single_bet_std_dev': std_dev,
            'n_bets': n_bets,
            'total_variance': total_variance,
            'total_std_dev': total_std_dev,
            'expected_value': ev,
            'expected_growth': expected_growth,
            'expected_growth_pct': (expected_growth - 1) * 100
        }

    @staticmethod
    def multi_outcome(
        outcomes: List[Dict],
        bankroll: float = 1000,
        kelly_fraction: float = 0.25
    ) -> Dict:
        """
        Multi-outcome Kelly (for horse racing, golf, 3-way markets, etc.)

        Uses the generalized Kelly formula for multiple simultaneous bets.

        Args:
            outcomes: List of dicts with 'odds' and 'prob' keys
            bankroll: Total bankroll
            kelly_fraction: Fraction of Kelly to use

        Returns:
            Optimal stakes for each outcome

        Examples:
            >>> outcomes = [
            ...     {'name': 'Horse A', 'odds': 300, 'prob': 0.30},
            ...     {'name': 'Horse B', 'odds': 400, 'prob': 0.25},
            ...     {'name': 'Horse C', 'odds': 500, 'prob': 0.20}
            ... ]
            >>> KellyCriterion.multi_outcome(outcomes, bankroll=1000)
        """
        from sportsbetlang.common.odds import american_to_decimal

        n = len(outcomes)

        # Build probability matrix
        # For multi-outcome Kelly, we need to solve:
        # f_i = (p_i * b_i - sum(f_j)) / b_i for each outcome

        # Convert odds to decimal
        for outcome in outcomes:
            outcome['decimal'] = american_to_decimal(outcome['odds'])
            outcome['b'] = outcome['decimal'] - 1  # Net odds

        # Iterative solution (simplified)
        stakes = []
        total_prob = sum(o['prob'] for o in outcomes)

        for outcome in outcomes:
            p = outcome['prob']
            b = outcome['b']
            q = 1 - p

            # Single outcome Kelly
            kelly = (b * p - q) / b
            fractional = kelly * kelly_fraction

            # Adjust for multi-outcome (normalize by total probability)
            if total_prob > 1:
                fractional = fractional * (1 / total_prob)

            stakes.append({
                'name': outcome.get('name', 'Outcome'),
                'odds': outcome['odds'],
                'prob': p,
                'kelly_pct': kelly,
                'fractional_kelly': max(0, fractional),
                'stake': max(0, fractional * bankroll)
            })

        total_stake = sum(s['stake'] for s in stakes)

        return {
            'outcomes': stakes,
            'total_stake': total_stake,
            'bankroll': bankroll,
            'pct_of_bankroll': (total_stake / bankroll) * 100
        }

    @staticmethod
    def simultaneous_bets(
        bets: List[Dict],
        bankroll: float,
        kelly_fraction: float = 0.25
    ) -> Dict:
        """
        Calculate optimal stakes for multiple simultaneous independent bets

        When you have multiple bets at the same time, you need to allocate
        bankroll optimally across all of them.

        Args:
            bets: List of dicts with 'odds' and 'prob' keys
            bankroll: Total available bankroll
            kelly_fraction: Kelly fraction

        Returns:
            Optimal allocation across all bets
        """
        # Calculate individual Kelly for each
        individual_kellys = []

        for bet in bets:
            kelly_result = KellyCriterion.calculate(
                odds=bet['odds'],
                true_prob=bet['prob'],
                kelly_fraction=kelly_fraction
            )
            individual_kellys.append({
                'description': bet.get('description', 'Bet'),
                'odds': bet['odds'],
                'fractional_kelly': kelly_result['fractional_kelly'],
                'edge': kelly_result['edge'],
                'ev': kelly_result['ev']
            })

        # Sum of all Kelly percentages
        total_kelly_pct = sum(k['fractional_kelly'] for k in individual_kellys)

        # If total exceeds 100%, normalize (scale down)
        if total_kelly_pct > 1.0:
            scale_factor = 1.0 / total_kelly_pct
            for kelly in individual_kellys:
                kelly['scaled_kelly'] = kelly['fractional_kelly'] * scale_factor
                kelly['stake'] = kelly['scaled_kelly'] * bankroll
        else:
            for kelly in individual_kellys:
                kelly['scaled_kelly'] = kelly['fractional_kelly']
                kelly['stake'] = kelly['scaled_kelly'] * bankroll

        total_stake = sum(k['stake'] for k in individual_kellys)
        weighted_ev = sum(k['stake'] * k['ev'] for k in individual_kellys) / total_stake if total_stake > 0 else 0

        return {
            'bets': individual_kellys,
            'total_stake': total_stake,
            'bankroll': bankroll,
            'pct_allocated': (total_stake / bankroll) * 100,
            'weighted_ev': weighted_ev,
            'normalized': total_kelly_pct > 1.0
        }

    @staticmethod
    def risk_of_ruin(
        win_rate: float,
        avg_odds: float,
        kelly_fraction: float = 0.25,
        min_bankroll_pct: float = 0.10
    ) -> float:
        """
        Calculate risk of ruin (probability of losing X% of bankroll)

        Args:
            win_rate: Historical win rate (0-1)
            avg_odds: Average odds (American)
            kelly_fraction: Kelly fraction used
            min_bankroll_pct: Minimum bankroll % before "ruin" (default 10%)

        Returns:
            Probability of ruin (0-1)
        """
        from sportsbetlang.common.odds import american_to_decimal

        decimal_odds = american_to_decimal(avg_odds)
        b = decimal_odds - 1

        p = win_rate
        q = 1 - p

        # Calculate Kelly
        kelly_pct = (b * p - q) / b
        f = kelly_pct * kelly_fraction

        # Risk of ruin formula (approximation)
        # RoR = ((1-p)/p * (1+b))^(C/(f*W))
        # where C = desired bankroll %, W = winning payout

        if p <= 0 or p >= 1:
            return 1.0 if p <= 0.5 else 0.0

        ratio = ((1 - p) / p) * (1 + b)

        # Exponent based on bankroll preservation goal
        exponent = math.log(min_bankroll_pct) / (f * b)

        ror = ratio ** exponent

        return min(1.0, max(0.0, ror))


# Convenience function
def calculate_kelly(
    odds: float,
    true_prob: float,
    kelly_fraction: float = 0.25,
    bankroll: Optional[float] = None,
    max_stake_pct: Optional[float] = None,
    allow_full_kelly: Optional[bool] = None,
    sample_size: Optional[int] = None,
    confidence_calibrated: Optional[bool] = None,
    min_sample_size_warning: Optional[int] = None,
    require_confidence_calibration: Optional[bool] = None
) -> Dict:
    """Calculate Kelly stake (convenience function)"""
    return KellyCriterion.calculate(
        odds=odds,
        true_prob=true_prob,
        kelly_fraction=kelly_fraction,
        bankroll=bankroll,
        max_stake_pct=max_stake_pct,
        allow_full_kelly=allow_full_kelly,
        sample_size=sample_size,
        confidence_calibrated=confidence_calibrated,
        min_sample_size_warning=min_sample_size_warning,
        require_confidence_calibration=require_confidence_calibration
    )
