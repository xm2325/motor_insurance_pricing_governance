from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from deployment.contracts import CATEGORICAL_FEATURES, FEATURES, feature_contract_hash
from deployment.environment import (
    EnvironmentCompatibility,
    require_model_environment_compatibility,
)
from deployment.provenance import BundleIntegrityReport, verify_bundle_lock


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass
class NativeXGBPipeline:
    """Inference wrapper: sklearn preprocessing + XGBoost native model IO."""

    preprocessor: Any
    model: XGBRegressor

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        transformed = self.preprocessor.transform(frame)
        return self.model.predict(transformed)


@dataclass
class ShadowModelBundle:
    root: Path
    manifest: dict[str, Any]
    models: dict[str, Any]
    environment_compatibility: EnvironmentCompatibility
    bundle_integrity: BundleIntegrityReport | None = None

    @classmethod
    def load(cls, root: str | Path) -> "ShadowModelBundle":
        root = Path(root)
        manifest_path = root / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Missing deployment manifest: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # v0.27 adds a content-addressed lock. Verify every locked file before any
        # joblib deserialisation or native-model load. Older contract bundles remain
        # readable so v0.21-v0.26 regression workflows can still exercise their own
        # historical contracts.
        bundle_integrity: BundleIntegrityReport | None = None
        if str(manifest.get("bundle_contract_version")) == "0.27":
            bundle_integrity = verify_bundle_lock(root)
            lock_document = json.loads((root / "bundle.lock.json").read_text(encoding="utf-8"))
            expected_pairs = {
                "bundle_contract_version": str(manifest.get("bundle_contract_version")),
                "model_version": manifest.get("model_version"),
                "governance_status": manifest.get("governance_status"),
                "feature_contract_hash": manifest.get("feature_contract_hash"),
            }
            for key, expected in expected_pairs.items():
                observed = lock_document.get(key)
                if observed != expected:
                    raise RuntimeError(
                        f"Bundle lock metadata mismatch for {key}: {observed!r} != {expected!r}"
                    )

        if manifest.get("feature_contract_hash") != feature_contract_hash():
            raise RuntimeError("Deployment feature contract hash does not match service code")

        # v0.26 deliberately keeps XGBoost out of pickle. Check the exact sklearn/joblib
        # stack and the native-XGBoost compatibility rule before any joblib object is loaded.
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
            serialization = metadata.get("serialization", "joblib_pipeline")

            if serialization == "joblib_pipeline":
                artifact_path = root / metadata["artifact"]
                actual_hash = sha256_file(artifact_path)
                if actual_hash != metadata["sha256"]:
                    raise RuntimeError(
                        f"Artifact hash mismatch for {model_name}: {actual_hash} != {metadata['sha256']}"
                    )
                models[model_name] = joblib.load(artifact_path)
                continue

            if serialization == "sklearn_preprocessor_plus_xgboost_ubj":
                prep_path = root / metadata["preprocessor_artifact"]
                native_path = root / metadata["native_model_artifact"]
                prep_hash = sha256_file(prep_path)
                native_hash = sha256_file(native_path)
                if prep_hash != metadata["preprocessor_sha256"]:
                    raise RuntimeError(
                        f"Preprocessor hash mismatch for {model_name}: "
                        f"{prep_hash} != {metadata['preprocessor_sha256']}"
                    )
                if native_hash != metadata["native_model_sha256"]:
                    raise RuntimeError(
                        f"Native model hash mismatch for {model_name}: "
                        f"{native_hash} != {metadata['native_model_sha256']}"
                    )
                preprocessor = joblib.load(prep_path)
                native_model = XGBRegressor()
                native_model.load_model(str(native_path))
                models[model_name] = NativeXGBPipeline(preprocessor, native_model)
                continue

            raise RuntimeError(
                f"Unsupported serialization mode for {model_name}: {serialization}"
            )

        return cls(
            root=root,
            manifest=manifest,
            models=models,
            environment_compatibility=environment_compatibility,
            bundle_integrity=bundle_integrity,
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
