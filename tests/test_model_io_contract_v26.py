from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestModelIOContractV26(unittest.TestCase):
    def test_pickle_stack_is_exactly_pinned_across_training_and_runtime(self) -> None:
        training = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        runtime = (ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
        for requirement in (
            "numpy==2.5.2",
            "pandas==3.0.5",
            "scipy==1.18.0",
            "scikit-learn==1.9.0",
            "joblib==1.5.3",
        ):
            self.assertIn(requirement, training)
            self.assertIn(requirement, runtime)

    def test_xgboost_uses_training_full_and_runtime_cpu_native_io(self) -> None:
        training = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        runtime = (ROOT / "requirements-runtime.txt").read_text(encoding="utf-8")
        builder = (ROOT / "build_deployment_bundle_v21.py").read_text(encoding="utf-8")
        loader = (ROOT / "deployment/bundle.py").read_text(encoding="utf-8")
        self.assertIn("xgboost==3.4.1", training)
        self.assertIn("xgboost-cpu==3.4.0", runtime)
        self.assertIn("sklearn_preprocessor_plus_xgboost_ubj", builder)
        self.assertIn("save_model", builder)
        self.assertIn("serialization_parity_summary.json", builder)
        self.assertIn("sklearn_preprocessor_plus_xgboost_ubj", loader)
        self.assertIn("load_model", loader)

    def test_workflow_uses_hybrid_compatibility_not_exact_xgboost_patch(self) -> None:
        workflow = (ROOT / ".github/workflows/v26-environment.yml").read_text(encoding="utf-8")
        self.assertIn("HYBRID_MODEL_IO_COMPATIBLE", workflow)
        self.assertIn("same_major_minor_for_native_model_io", workflow)
        self.assertIn("SAME_FIT_SERIALIZATION_PARITY_PASS", workflow)
        self.assertNotIn("EXACT_MODEL_STACK_MATCH", workflow)

    def test_historical_fixture_remains_public_feature_only(self) -> None:
        fixture = json.loads(
            (ROOT / "tests/fixtures/v26_locked_parity_reference.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(fixture["records"]), 25)
        self.assertTrue(fixture["provenance"]["records_are_public_rating_features_only"])
        forbidden = set(fixture["provenance"]["excluded_identifiers_and_outcomes"])
        for record in fixture["records"]:
            self.assertTrue(forbidden.isdisjoint(record))


if __name__ == "__main__":
    unittest.main()
