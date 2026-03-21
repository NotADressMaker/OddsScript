"""
Centralized odds conversion utilities.

This is the single source of truth for all odds conversions across SportsBetLang.
Used by all tools and libraries to eliminate code duplication.
"""

from typing import Union, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class OddsFormat(Enum):
    """Supported odds formats"""
    AMERICAN = "american"
    DECIMAL = "decimal"
    FRACTIONAL = "fractional"
    IMPLIED = "implied"


class OddsConverter:
    """High-precision odds conversion utilities"""

    @staticmethod
    def american_to_decimal(odds: float, precision: int = 4) -> Decimal:
        """
        Convert American odds to decimal odds

        Args:
            odds: American odds (e.g., -110, +150)
            precision: Decimal places (default: 4)

        Returns:
            Decimal odds

        Examples:
            >>> OddsConverter.american_to_decimal(-110)
            Decimal('1.9091')
            >>> OddsConverter.american_to_decimal(150)
            Decimal('2.5000')
        """
        if odds == 0:
            raise ValueError("American odds cannot be 0")

        if odds > 0:
            result = (odds / 100) + 1
        else:
            result = (100 / abs(odds)) + 1

        quantizer = Decimal('0.' + '0' * precision)
        return Decimal(str(result)).quantize(quantizer, rounding=ROUND_HALF_UP)

    @staticmethod
    def decimal_to_american(odds: float) -> float:
        """
        Convert decimal odds to American odds

        Args:
            odds: Decimal odds (e.g., 1.91, 2.50)

        Returns:
            American odds

        Examples:
            >>> OddsConverter.decimal_to_american(1.91)
            -109.89...
            >>> OddsConverter.decimal_to_american(2.50)
            150.0
        """
        if odds <= 1:
            raise ValueError("Decimal odds must be greater than 1.0")

        if odds >= 2.0:
            return (odds - 1) * 100
        else:
            return -100 / (odds - 1)

    @staticmethod
    def american_to_fractional(odds: float) -> str:
        """
        Convert American odds to fractional format

        Args:
            odds: American odds

        Returns:
            Fractional odds as string (e.g., "5/2", "1/2")

        Examples:
            >>> OddsConverter.american_to_fractional(150)
            '3/2'
            >>> OddsConverter.american_to_fractional(-110)
            '10/11'
        """
        decimal = float(OddsConverter.american_to_decimal(odds))

        # Convert decimal to fraction
        if decimal >= 2.0:
            # Underdog
            numerator = decimal - 1
        else:
            # Favorite
            numerator = 1 / (decimal - 1)

        # Use continued fractions to find best approximation
        return OddsConverter._decimal_to_fraction(numerator)

    @staticmethod
    def fractional_to_american(fractional: str) -> float:
        """
        Convert fractional odds to American

        Args:
            fractional: Fractional odds (e.g., "5/2", "1/2")

        Returns:
            American odds

        Examples:
            >>> OddsConverter.fractional_to_american("3/2")
            150.0
            >>> OddsConverter.fractional_to_american("10/11")
            -110.0
        """
        parts = fractional.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid fractional format: {fractional}")

        num, denom = float(parts[0]), float(parts[1])
        if denom == 0:
            raise ValueError("Fractional odds denominator cannot be 0")
        decimal = (num / denom) + 1

        return OddsConverter.decimal_to_american(decimal)

    @staticmethod
    def to_implied_probability(
        odds: float,
        format: OddsFormat = OddsFormat.AMERICAN,
        precision: int = 4
    ) -> Decimal:
        """
        Convert odds to implied probability

        Args:
            odds: Odds value
            format: Odds format
            precision: Decimal places

        Returns:
            Implied probability (0-1)

        Examples:
            >>> OddsConverter.to_implied_probability(-110)
            Decimal('0.5238')
            >>> OddsConverter.to_implied_probability(2.0, OddsFormat.DECIMAL)
            Decimal('0.5000')
        """
        if format == OddsFormat.AMERICAN:
            decimal = OddsConverter.american_to_decimal(odds)
        elif format == OddsFormat.DECIMAL:
            decimal = Decimal(str(odds))
        else:
            raise ValueError(f"Unsupported format: {format}")

        quantizer = Decimal('0.' + '0' * precision)
        return (Decimal('1') / decimal).quantize(quantizer, rounding=ROUND_HALF_UP)

    @staticmethod
    def remove_vig(
        prob1: float,
        prob2: float,
        method: str = 'proportional'
    ) -> Tuple[float, float]:
        """
        Remove vig (overround) from probabilities

        Args:
            prob1: Implied probability of outcome 1
            prob2: Implied probability of outcome 2
            method: Removal method - 'proportional', 'power', or 'additive'

        Returns:
            Tuple of (fair_prob1, fair_prob2)

        Examples:
            >>> OddsConverter.remove_vig(0.5238, 0.5238)
            (0.5, 0.5)
        """
        total = prob1 + prob2

        if method == 'proportional':
            # Most common method - proportionally distribute the vig
            return prob1 / total, prob2 / total

        elif method == 'power':
            # Shin method - assumes some insider trading
            # More sophisticated but requires optimization
            import math

            # Simplified power method
            z = total - 1  # Overround
            k = 1 - z / 2  # Adjustment factor

            fair1 = (prob1 ** k) / ((prob1 ** k) + (prob2 ** k))
            fair2 = 1 - fair1

            return fair1, fair2

        elif method == 'additive':
            # Simply subtract half the vig from each
            vig = total - 1
            return prob1 - vig/2, prob2 - vig/2

        else:
            raise ValueError(f"Unknown method: {method}")

    @staticmethod
    def remove_vig_multi(
        probs: list,
        method: str = 'proportional'
    ) -> list:
        """
        Remove vig from multiple outcomes (3-way markets, etc.)

        Args:
            probs: List of implied probabilities
            method: Removal method

        Returns:
            List of fair probabilities
        """
        total = sum(probs)

        if method == 'proportional':
            return [p / total for p in probs]
        elif method == 'additive':
            vig = total - 1
            adjustment = vig / len(probs)
            return [p - adjustment for p in probs]
        else:
            raise ValueError(f"Method {method} not supported for multi-outcome")

    @staticmethod
    def calculate_vig(prob1: float, prob2: float) -> float:
        """
        Calculate the vig (overround) percentage

        Args:
            prob1: Implied probability 1
            prob2: Implied probability 2

        Returns:
            Vig percentage (e.g., 4.76 for -110/-110)

        Examples:
            >>> OddsConverter.calculate_vig(0.5238, 0.5238)
            4.76
        """
        total = prob1 + prob2
        return (total - 1) * 100

    @staticmethod
    def _decimal_to_fraction(decimal: float, max_denominator: int = 100) -> str:
        """
        Convert decimal to fraction using continued fractions algorithm

        Args:
            decimal: Decimal number
            max_denominator: Maximum denominator allowed

        Returns:
            Fraction as string
        """
        # Handle whole numbers
        if decimal == int(decimal):
            return f"{int(decimal)}/1"

        # Continued fractions algorithm
        tolerance = 1.0e-6
        h1, h2 = 1, 0
        k1, k2 = 0, 1
        b = decimal

        while True:
            a = int(b)
            aux = h1
            h1 = a * h1 + h2
            h2 = aux
            aux = k1
            k1 = a * k1 + k2
            k2 = aux
            b = 1 / (b - a)

            if abs(decimal - h1/k1) < tolerance or k1 > max_denominator:
                break

        return f"{h1}/{k1}"


# Convenience functions for backward compatibility
def american_to_decimal(odds: float) -> float:
    """Convert American to decimal odds"""
    return float(OddsConverter.american_to_decimal(odds))


def decimal_to_american(odds: float) -> float:
    """Convert decimal to American odds"""
    return OddsConverter.decimal_to_american(odds)


def implied_probability(odds: float, format: str = 'american') -> float:
    """Calculate implied probability"""
    fmt = OddsFormat.AMERICAN if format == 'american' else OddsFormat.DECIMAL
    return float(OddsConverter.to_implied_probability(odds, fmt))


def remove_vig(prob1: float, prob2: float, method: str = 'proportional') -> Tuple[float, float]:
    """Remove vig from probabilities"""
    return OddsConverter.remove_vig(prob1, prob2, method)


def calculate_vig(prob1: float, prob2: float) -> float:
    """Calculate vig percentage"""
    return OddsConverter.calculate_vig(prob1, prob2)
