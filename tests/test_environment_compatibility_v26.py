from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deployment.bundle import ShadowModelBundle
from deployment.contracts import feature_contract_hash
from deployment.environment import (
    CRITICAL_PICKLE_ENV_KEYS,
    capture_model_environment,
    compare_model_environments,
)


ROOT = Path(__file__).resolve().parents[1]


class TestEnvironmentCompatibilityV26(unittest.TestCase):
    def test_current_hybrid_model_io_environment_matches(self) -> None:
        current = capture_model_environment()
        report = compare_model_environments(current, current)
        self.assertEqual(report.status, "HYBRID_MODEL_IO_COMPATIBLE")
        self.assertTrue(report.compatible)
        self.assertEqual(report.mismatches, {})

    def test_pickle_stack_version_mismatch_rejects(self) -> None:
        expected = capture_model_environment()
        runtime = dict(expected)
        runtime["scikit_learn"] = "0.0.0-test-mismatch"
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "REJECT_PICKLE_STACK_MISMATCH")
        self.assertFalse(report.compatible)
        self.assertIn("scikit_learn", report.mismatches)

    def test_xgboost_patch_difference_is_allowed_for_native_model_io(self) -> None:
        expected = capture_model_environment()
        runtime = dict(expected)
        expected["xgboost"] = "3.4.1"
        runtime["xgboost"] = "3.4.0"
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "HYBRID_MODEL_IO_COMPATIBLE")
        self.assertTrue(report.compatible)
        self.assertTrue(report.xgboost_native_compatible)

    def test_xgboost_minor_difference_rejects(self) -> None:
        expected = capture_model_environment()
        runtime = dict(expected)
        expected["xgboost"] = "3.4.1"
        runtime["xgboost"] = "3.5.0"
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "REJECT_XGBOOST_NATIVE_VERSION_MISMATCH")
        self.assertFalse(report.compatible)
        self.assertIn("xgboost", report.mismatches)

    def test_missing_training_environment_rejects(self) -> None:
        runtime = capture_model_environment()
        expected = {key: runtime[key] for key in CRITICAL_PICKLE_ENV_KEYS}
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "REJECT_MISSING_TRAINING_ENVIRONMENT")
        self.assertIn("xgboost", report.mismatches)

    def test_bundle_rejects_pickle_mismatch_before_joblib_load(self) -> None:
        expected = capture_model_environment()
        expected["scikit_learn"] = "0.0.0-test-mismatch"
        manifest = {
            "feature_contract_hash": feature_contract_hash(),
            "training_environment": expected,
            "models": {
                "dummy": {
                    "serialization": "joblib_pipeline",
                    "artifact": "does-not-need-to-exist.joblib",
                    "sha256": "0" * 64,
                }
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch("deployment.bundle.joblib.load") as mocked_load:
                with self.assertRaisesRegex(RuntimeError, "compatibility gate failed"):
                    ShadowModelBundle.load(root)
                mocked_load.assert_not_called()

    def test_bundle_accepts_compatible_environment_before_empty_model_set(self) -> None:
        manifest = {
            "feature_contract_hash": feature_contract_hash(),
            "training_environment": capture_model_environment(),
            "models": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            bundle = ShadowModelBundle.load(root)
            self.assertEqual(
                bundle.environment_compatibility.status,
                "HYBRID_MODEL_IO_COMPATIBLE",
            )

    def test_training_and_runtime_pin_pickle_stack_but_allow_xgb_patch_split(self) -> None:
        training = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        runtime = (ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
        expected_common = [
            "numpy==2.5.2",
            "pandas==3.0.5",
            "scipy==1.18.0",
            "scikit-learn==1.9.0",
            "joblib==1.5.3",
        ]
        for requirement in expected_common:
            self.assertIn(requirement, training)
            self.assertIn(requirement, runtime)
        self.assertIn("xgboost==3.4.1", training)
        self.assertIn("xgboost-cpu==3.4.0", runtime)

    def test_builder_uses_native_xgboost_model_io(self) -> None:
        source = (ROOT / "build_deployment_bundle_v21.py").read_text(encoding="utf-8")
        self.assertIn("sklearn_preprocessor_plus_xgboost_ubj", source)
        self.assertIn("save_model", source)
        self.assertIn("serialization_parity_summary.json", source)

    def test_frozen_parity_fixture_has_public_features_only(self) -> None:
        fixture = json.loads(
            (ROOT / "tests/fixtures/v26_locked_parity_reference.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(fixture["records"]), 25)
        self.assertEqual(len(fixture["scores"]), 25)
        self.assertTrue(fixture["provenance"]["records_are_public_rating_features_only"])
        forbidden = set(fixture["provenance"]["excluded_identifiers_and_outcomes"])
        for record in fixture["records"]:
            self.assertTrue(forbidden.isdisjoint(record))


if __name__ == "__main__":
    unittest.main()
