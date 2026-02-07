"""
Base types for model plugins.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class ModelSpec:
    """Metadata + loader for a model plugin."""

    name: str
    description: str
    loader: Callable[[], Any]

    def load(self) -> Any:
        return self.loader()
