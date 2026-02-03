"""Schema registry and minimal validation helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_DIR = Path(__file__).parent


def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_basic(schema: dict, payload: dict) -> tuple[bool, list[str]]:
    errors: list[str] = []
    required = schema.get("required", [])
    for key in required:
        if key not in payload:
            errors.append(f"Missing required field: {key}")
    properties = schema.get("properties", {})
    for key, value in payload.items():
        if key not in properties:
            continue
        expected = properties[key].get("type")
        if expected is None:
            continue
        if not _matches_type(expected, value):
            errors.append(f"Field {key} expected {expected} but got {type(value).__name__}")
    return (len(errors) == 0, errors)


def _matches_type(expected: Any, value: Any) -> bool:
    if isinstance(expected, list):
        return any(_matches_type(option, value) for option in expected)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "null":
        return value is None
    return True

