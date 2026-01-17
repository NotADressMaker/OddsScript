"""
Shared utilities for SportsBetLang.

This module contains common functionality used across all tools and libraries:
- Odds conversions
- Kelly Criterion calculations
- Input validation
"""

from sportsbetlang.common.odds import (
    OddsConverter,
    OddsFormat,
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    remove_vig,
    calculate_vig
)

from sportsbetlang.common.kelly import (
    KellyCriterion,
    calculate_kelly
)

from sportsbetlang.common.validators import (
    Validators,
    ValidationError,
    validate_odds,
    validate_probability,
    validate_stake,
    validate_bankroll,
    validate_kelly_fraction
)

__all__ = [
    # Odds conversion
    'OddsConverter',
    'OddsFormat',
    'american_to_decimal',
    'decimal_to_american',
    'implied_probability',
    'remove_vig',
    'calculate_vig',

    # Kelly Criterion
    'KellyCriterion',
    'calculate_kelly',

    # Validation
    'Validators',
    'ValidationError',
    'validate_odds',
    'validate_probability',
    'validate_stake',
    'validate_bankroll',
    'validate_kelly_fraction',
]
