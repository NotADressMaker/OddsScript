"""
Model plugins for SportsBetLang.

This package provides a registry-based plugin system for predictive models.
"""

from sportsbetlang.models.registry import (
    register,
    register_module,
    available,
    get,
    load,
    bulk_register,
)

_BUILTIN_MODULES = [
    "sportsbetlang.models.elo_totals",
    "sportsbetlang.models.multi_market_ratings",
]

bulk_register(_BUILTIN_MODULES)


def available_models():
    return available()


def get_model_spec(name: str):
    return get(name)


def load_model(name: str, **kwargs):
    model_loader = load(name)
    if isinstance(model_loader, type):
        return model_loader(**kwargs)
    if callable(model_loader):
        return model_loader(**kwargs)
    return model_loader


__all__ = [
    "available_models",
    "get_model_spec",
    "load_model",
    "register",
    "register_module",
]
