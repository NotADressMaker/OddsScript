"""
Elo totals model plugin entrypoint.
"""

from sportsbetlang.models.elo_totals import (
    EloTotalsModel,
    create_model,
    get_model_spec,
)

__all__ = [
    "EloTotalsModel",
    "create_model",
    "get_model_spec",
]
