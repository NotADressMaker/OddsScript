"""
Model registry for SportsBetLang plugins.
"""

from __future__ import annotations

import importlib
from typing import Dict, Iterable, List

from sportsbetlang.models.base import ModelSpec


_REGISTRY: Dict[str, ModelSpec] = {}


def register(spec: ModelSpec) -> None:
    """Register a model specification."""
    if not spec.name:
        raise ValueError("ModelSpec.name cannot be empty")
    _REGISTRY[spec.name] = spec


def register_module(module_path: str) -> None:
    """Import a module and register its ModelSpec if present."""
    module = importlib.import_module(module_path)
    get_spec = getattr(module, "get_model_spec", None)
    if callable(get_spec):
        register(get_spec())


def available() -> List[str]:
    """Return available model names."""
    return sorted(_REGISTRY.keys())


def get(name: str) -> ModelSpec:
    """Fetch a ModelSpec by name."""
    if name not in _REGISTRY:
        raise KeyError(f"Model '{name}' is not registered")
    return _REGISTRY[name]


def load(name: str):
    """Load the model loader output for a model name."""
    return get(name).load()


def bulk_register(modules: Iterable[str]) -> None:
    """Register multiple modules in one call."""
    for module_path in modules:
        register_module(module_path)
