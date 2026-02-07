"""
Elo totals model plugin.
"""

from lib.elo_totals import EloTotalsModel

from sportsbetlang.models.base import ModelSpec


def create_model(**kwargs) -> EloTotalsModel:
    """Create a new EloTotalsModel instance."""
    return EloTotalsModel(**kwargs)


def get_model_spec() -> ModelSpec:
    return ModelSpec(
        name="elo_totals",
        description="Elo-based totals model with offense/defense ratings.",
        loader=lambda: EloTotalsModel,
    )


__all__ = [
    "EloTotalsModel",
    "create_model",
    "get_model_spec",
]
