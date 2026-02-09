"""Runtime safety limits for the SportsBetLang interpreter."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeLimits:
    """Container for configurable runtime limits."""

    max_steps: int = 200_000
    max_recursion_depth: int = 200
    max_tokens: int = 50_000
    max_ast_nodes: int = 200_000
    max_string_length: int = 200_000
    max_list_length: int = 50_000
    max_loop_iterations: int = 200_000


DEFAULT_LIMITS = RuntimeLimits()
