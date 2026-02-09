from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sportsbetlang.analytics.registry import ModelRegistry


@dataclass
class DummyModel:
    value: int


def test_config_hash_stable(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path)
    config_a = {"b": 1, "a": 2}
    config_b = {"a": 2, "b": 1}
    assert registry._hash_config(config_a) == registry._hash_config(config_b)


def test_save_load_round_trip(tmp_path: Path) -> None:
    registry = ModelRegistry(tmp_path)
    model = DummyModel(value=42)
    registry.save(
        model,
        metrics={"accuracy": 0.9},
        config={"alpha": 1.0},
        dataset_version="v1",
        name="dummy",
    )
    loaded = registry.load("dummy")
    assert isinstance(loaded, DummyModel)
    assert loaded.value == 42
