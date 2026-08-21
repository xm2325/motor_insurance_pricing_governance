from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from deployment.contracts import CATEGORICAL_FEATURES, FEATURES, feature_contract_hash
from deployment.environment import (
    EnvironmentCompatibility,
    require_model_environment_compatibility,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class ShadowModelBundle:
    root: Path
    manifest: dict[str, Any]
    models: dict[str, Any]
    environment_compatibility: EnvironmentCompatibility

    @classmethod
    def load(cls, root: str | Path) -> "ShadowModelBundle":
        root = Path(root)
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing deployment manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("feature_contract_hash") != feature_contract_hash():
            raise RuntimeError("Deployment feature contract hash does not match service code")

        # The persisted objects are sklearn Pipelines saved through joblib/pickle. Check
        # the model stack before any artifact is deserialised so a version mismatch fails
        # closed rather than merely emitting a warning after the object has been loaded.
        expected_environment = manifest.get("training_environment")
        if not isinstance(expected_environment, dict):
            raise RuntimeError(
                "Deployment manifest is missing training_environment; refuse joblib deserialization"
            )
        environment_compatibility = require_model_environment_compatibility(
            expected_environment
        )

        models: dict[str, Any] = {}
        for model_name, metadata in manifest["models"].items():
            artifact_path = root / metadata["artifact"]
            actual_hash = sha256_file(artifact_path)
            if actual_hash != metadata["sha256"]:
                raise RuntimeError(
                    f"Artifact hash mismatch for {model_name}: {actual_hash} != {metadata['sha256']}"
                )
            models[model_name] = joblib.load(artifact_path)
        return cls(
            root=root,
            manifest=manifest,
            models=models,
            environment_compatibility=environment_compatibility,
        )

    def _warnings_for_record(self, record: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        known = self.manifest.get("categorical_levels", {})
        for field in CATEGORICAL_FEATURES:
            value = record.get(field)
            if value is None:
                continue
            if str(value) not in known.get(field, []):
                warnings.append(f"unseen_category:{field}={value}")
        return warnings

    def score_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not records:
            return []
        frame = pd.DataFrame(records, columns=FEATURES)
        raw_predictions = {
            name: np.clip(model.predict(frame), 1e-12, None)
            for name, model in self.models.items()
        }
        scaled = {
            name: raw_predictions[name] * float(self.manifest["models"][name]["locked_scale"])
            for name in raw_predictions
        }

        rows: list[dict[str, Any]] = []
        for idx, record in enumerate(records):
            reference_frequency = float(scaled["poisson_glm_frequency"][idx])
            challenger_frequency = float(scaled["xgb_poisson_frequency"][idx])
            reference_pure_premium = float(scaled["tweedie_glm_pure_premium"][idx])
            challenger_pure_premium = float(scaled["xgb_tweedie_pure_premium"][idx])
            rows.append(
                {
                    "model_version": self.manifest["model_version"],
                    "governance_status": self.manifest["governance_status"],
                    "reference_frequency": reference_frequency,
                    "challenger_frequency": challenger_frequency,
                    "reference_pure_premium": reference_pure_premium,
                    "challenger_pure_premium": challenger_pure_premium,
                    "frequency_log_ratio": float(np.log(challenger_frequency / reference_frequency)),
                    "pure_premium_log_ratio": float(np.log(challenger_pure_premium / reference_pure_premium)),
                    "warnings": self._warnings_for_record(record),
                }
            )
        return rows
