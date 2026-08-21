from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TestEnvironmentStaticV26(unittest.TestCase):
    def test_training_and_runtime_pin_same_model_stack(self) -> None:
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
        self.assertIn("xgboost==3.4.0", training)
        self.assertIn("xgboost-cpu==3.4.0", runtime)

    def test_bundle_checks_environment_before_joblib_load_in_source(self) -> None:
        source = (ROOT / "deployment/bundle.py").read_text(encoding="utf-8")
        gate = source.index("require_model_environment_compatibility")
        load = source.index("joblib.load(artifact_path)")
        self.assertLess(gate, load)
        self.assertIn("missing training_environment", source)

    def test_manifest_builder_records_environment_and_serialization_policy(self) -> None:
        source = (ROOT / "build_deployment_bundle_v21.py").read_text(encoding="utf-8")
        self.assertIn('"training_environment": training_environment', source)
        self.assertIn('"bundle_contract_version": "0.26"', source)
        self.assertIn('"environment_check_before_deserialization": True', source)
        self.assertIn('"format": "joblib_pickle_sklearn_pipeline"', source)

    def test_frozen_reference_provenance_is_locked(self) -> None:
        fixture = json.loads(
            (ROOT / "tests/fixtures/v26_locked_parity_reference.json").read_text(encoding="utf-8")
        )
        provenance = fixture["provenance"]
        self.assertEqual(provenance["source_workflow_run_id"], 32505692555)
        self.assertEqual(provenance["source_artifact_id"], 9455210467)
        self.assertEqual(
            provenance["source_artifact_digest"],
            "sha256:04a7fefcd4a8aaf1f48ef1a9d082a5338bb860b2dcd3c62599e623b464b771e8",
        )
        self.assertEqual(
            provenance["source_parity_reference_sha256"],
            "2a3e24aed7db97bfe3cf601dd5ac6c14f1044820da9a7bed20b5e5b68510ce01",
        )
        self.assertEqual(len(fixture["records"]), 25)
        self.assertEqual(len(fixture["scores"]), 25)


if __name__ == "__main__":
    unittest.main()
