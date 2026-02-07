"""
Betting math library for SportsBetLang.

This package provides a stable surface for odds math, EV calculations,
vig removal, Kelly sizing, and correlation utilities.
"""

from sportsbetlang.common import (
    OddsConverter,
    OddsFormat,
    american_to_decimal,
    decimal_to_american,
    implied_probability,
    remove_vig,
    calculate_vig,
    KellyCriterion,
    calculate_kelly,
    ValidationError,
)
from sportsbetlang.betting.correlation import (
    CorrelationAnalyzer,
    CorrelationType,
    BetType,
)
from sportsbetlang.betting.ev import (
    american_to_implied_prob,
    prob_to_american,
    payout_per_1_risk,
    expected_value_per_1_risk,
)

__all__ = [
    "OddsConverter",
    "OddsFormat",
    "american_to_decimal",
    "decimal_to_american",
    "implied_probability",
    "remove_vig",
    "calculate_vig",
    "KellyCriterion",
    "calculate_kelly",
    "ValidationError",
    "CorrelationAnalyzer",
    "CorrelationType",
    "BetType",
    "american_to_implied_prob",
    "prob_to_american",
    "payout_per_1_risk",
    "expected_value_per_1_risk",
]
