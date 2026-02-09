"""Model registry utilities for reproducible analytics artifacts."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata
from pathlib import Path
from typing import Any, Optional

try:
    import joblib
except ImportError:  # pragma: no cover - optional dependency
    joblib = None

import pickle


@dataclass(frozen=True)
class ModelMetadata:
    """Metadata describing a saved model artifact."""

    created_at: str
    config_hash: str
    dataset_version: str
    metrics: dict[str, Any]
    config: dict[str, Any]
    python_version: str
    packages: dict[str, str]


class ModelRegistry:
    """Persist and load model artifacts with metadata."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _hash_config(self, config: dict[str, Any]) -> str:
        payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _versions(self) -> dict[str, str]:
        packages = {}
        for name in ["numpy", "pandas", "scikit-learn", "joblib"]:
            try:
                packages[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                continue
        return packages

    def _model_dir(self, name: str, version: str) -> Path:
        return self.root_dir / name / version

    def _write_metadata(self, path: Path, metadata_obj: ModelMetadata) -> None:
        path.write_text(json.dumps(metadata_obj.__dict__, indent=2), encoding="utf-8")

    def _write_report(self, model_dir: Path, metadata_obj: ModelMetadata) -> None:
        report_path = model_dir / "report.json"
        report = {
            "created_at": metadata_obj.created_at,
            "config_hash": metadata_obj.config_hash,
            "dataset_version": metadata_obj.dataset_version,
            "metrics": metadata_obj.metrics,
            "config": metadata_obj.config,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def save(
        self,
        model: Any,
        *,
        metrics: dict[str, Any],
        config: dict[str, Any],
        dataset_version: str,
        name: str,
    ) -> Path:
        """Persist a model artifact and metadata to the registry."""

        created_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        version = datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")
        model_dir = self._model_dir(name, version)
        model_dir.mkdir(parents=True, exist_ok=True)

        config_hash = self._hash_config(config)
        metadata_obj = ModelMetadata(
            created_at=created_at,
            config_hash=config_hash,
            dataset_version=dataset_version,
            metrics=metrics,
            config=config,
            python_version=sys.version.split(" ")[0],
            packages=self._versions(),
        )
        metadata_path = model_dir / "metadata.json"
        self._write_metadata(metadata_path, metadata_obj)
        self._write_report(model_dir, metadata_obj)

        if joblib is not None:
            artifact_path = model_dir / "model.joblib"
            joblib.dump(model, artifact_path)
        else:
            artifact_path = model_dir / "model.pkl"
            with artifact_path.open("wb") as handle:
                pickle.dump(model, handle)

        return model_dir

    def load(self, name: str, version: Optional[str] = None) -> Any:
        """Load a model artifact by name and optional version."""

        model_root = self.root_dir / name
        if not model_root.exists():
            raise FileNotFoundError(f"Model '{name}' not found")
        versions = sorted(p.name for p in model_root.iterdir() if p.is_dir())
        if not versions:
            raise FileNotFoundError(f"Model '{name}' has no versions")
        selected = version or versions[-1]
        model_dir = model_root / selected
        artifact = model_dir / "model.joblib"
        if not artifact.exists():
            artifact = model_dir / "model.pkl"
        if not artifact.exists():
            raise FileNotFoundError(f"Model artifact not found for '{name}'")
        if joblib is not None and artifact.suffix == ".joblib":
            return joblib.load(artifact)
        with artifact.open("rb") as handle:
            return pickle.load(handle)

    def list_models(self) -> list[dict[str, Any]]:
        """Return the registry inventory."""

        inventory: list[dict[str, Any]] = []
        for model_dir in sorted(self.root_dir.iterdir()):
            if not model_dir.is_dir():
                continue
            versions = sorted(p.name for p in model_dir.iterdir() if p.is_dir())
            inventory.append(
                {
                    "name": model_dir.name,
                    "versions": versions,
                    "latest": versions[-1] if versions else None,
                }
            )
        return inventory
