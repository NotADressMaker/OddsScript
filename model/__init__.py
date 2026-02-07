"""
Model plugin namespace for SportsBetLang.

Importing model.<name> resolves to a SportsBetLang model plugin.
"""

from sportsbetlang.models import (
    available_models,
    get_model_spec,
    load_model,
    register,
    register_module,
)

__all__ = [
    "available_models",
    "get_model_spec",
    "load_model",
    "register",
    "register_module",
]
