from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deployment.bundle import ShadowModelBundle
from deployment.contracts import feature_contract_hash
from deployment.environment import (
    CRITICAL_MODEL_ENV_KEYS,
    capture_model_environment,
    compare_model_environments,
)


ROOT = Path(__file__).resolve().parents[1]


class TestEnvironmentCompatibilityV26(unittest.TestCase):
    def test_exact_model_stack_matches(self) -> None:
        current = capture_model_environment()
        report = compare_model_environments(current, current)
        self.assertEqual(report.status, "EXACT_MODEL_STACK_MATCH")
        self.assertTrue(report.compatible)
        self.assertEqual(report.mismatches, {})

    def test_critical_version_mismatch_rejects(self) -> None:
        expected = capture_model_environment()
        runtime = dict(expected)
        runtime["scikit_learn"] = "0.0.0-test-mismatch"
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "REJECT_MODEL_STACK_MISMATCH")
        self.assertFalse(report.compatible)
        self.assertIn("scikit_learn", report.mismatches)

    def test_missing_training_environment_rejects(self) -> None:
        runtime = capture_model_environment()
        expected = {key: runtime[key] for key in CRITICAL_MODEL_ENV_KEYS if key != "xgboost"}
        report = compare_model_environments(expected, runtime)
        self.assertEqual(report.status, "REJECT_MISSING_TRAINING_ENVIRONMENT")
        self.assertIn("xgboost", report.mismatches)

    def test_bundle_rejects_mismatch_before_joblib_load(self) -> None:
        expected = capture_model_environment()
        expected["xgboost"] = "0.0.0-test-mismatch"
        manifest = {
            "feature_contract_hash": feature_contract_hash(),
            "training_environment": expected,
            "models": {
                "dummy": {
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

    def test_bundle_accepts_exact_environment_before_empty_model_set(self) -> None:
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
                "EXACT_MODEL_STACK_MATCH",
            )

    def test_training_and_runtime_requirements_pin_same_model_stack(self) -> None:
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
        self.assertIn("xgboost==3.4.0", training)
        self.assertIn("xgboost-cpu==3.4.0", runtime)

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
