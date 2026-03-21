import pytest

from sportsbetlang.common.odds import OddsConverter, american_to_decimal, decimal_to_american


def test_american_to_decimal_rejects_zero():
    with pytest.raises(ValueError, match="cannot be 0"):
        american_to_decimal(0)


def test_decimal_to_american_rejects_values_leq_one():
    for odds in (1.0, 0.95):
        with pytest.raises(ValueError, match="greater than 1.0"):
            decimal_to_american(odds)


def test_fractional_to_american_rejects_zero_denominator():
    with pytest.raises(ValueError, match="denominator cannot be 0"):
        OddsConverter.fractional_to_american("5/0")
