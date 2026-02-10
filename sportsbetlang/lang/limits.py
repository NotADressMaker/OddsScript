"""Runtime safety limits for the SportsBetLang interpreter."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Optional


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

SAFE_LIMITS = RuntimeLimits(
    max_steps=200_000,
    max_recursion_depth=200,
    max_loop_iterations=200_000,
)

EXPERT_LIMITS = RuntimeLimits(
    max_steps=2_000_000,
    max_recursion_depth=2_000,
    max_tokens=250_000,
    max_ast_nodes=1_000_000,
    max_string_length=500_000,
    max_list_length=250_000,
    max_loop_iterations=2_000_000,
)


def parse_limits_pragma(source: str) -> Dict[str, int]:
    """Parse a first-line '#limits key=value ...' pragma."""

    for raw_line in source.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        if not stripped.startswith("#"):
            return {}
        if not stripped.lower().startswith("#limits"):
            return {}
        payload = stripped[len("#limits") :].strip()
        if not payload:
            return {}
        overrides: Dict[str, int] = {}
        for part in payload.split():
            if "=" not in part:
                continue
            key, raw_value = part.split("=", 1)
            try:
                overrides[key.strip().lower()] = int(raw_value.strip().replace("_", ""))
            except ValueError:
                continue
        return overrides
    return {}


def resolve_runtime_limits(
    source: str,
    *,
    base_limits: RuntimeLimits,
    max_steps: Optional[int] = None,
    max_loop: Optional[int] = None,
    max_recursion: Optional[int] = None,
) -> RuntimeLimits:
    """Resolve limits from mode defaults, source pragma, and CLI overrides."""

    limits = base_limits
    pragma = parse_limits_pragma(source)
    if pragma:
        limits = replace(
            limits,
            max_steps=pragma.get("max_steps", limits.max_steps),
            max_loop_iterations=pragma.get("max_loop", limits.max_loop_iterations),
            max_recursion_depth=pragma.get("max_recursion", limits.max_recursion_depth),
        )
    return replace(
        limits,
        max_steps=max_steps if max_steps is not None else limits.max_steps,
        max_loop_iterations=max_loop if max_loop is not None else limits.max_loop_iterations,
        max_recursion_depth=max_recursion if max_recursion is not None else limits.max_recursion_depth,
    )
