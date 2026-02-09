"""
Multi-market ratings model plugin.
"""

from lib.multi_market_ratings import MultiMarketRatingsModel

from sportsbetlang.models.base import ModelSpec


def create_model(**kwargs) -> MultiMarketRatingsModel:
    """Create a new MultiMarketRatingsModel instance."""
    return MultiMarketRatingsModel(**kwargs)


def get_model_spec() -> ModelSpec:
    return ModelSpec(
        name="multi_market_ratings",
        description="Baseline offense/defense ratings for spread + totals across sports.",
        loader=lambda: MultiMarketRatingsModel,
    )


__all__ = [
    "MultiMarketRatingsModel",
    "create_model",
    "get_model_spec",
]
