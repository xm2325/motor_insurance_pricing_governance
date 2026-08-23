from __future__ import annotations

import json
import unittest
from pathlib import Path

from validate_external_validation_prereg_v36 import (
    ExternalPreregistrationError,
    canonical_sha256,
    ensure_no_row_level_external_data_present,
    validate_prereg,
)


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "governance" / "external_validation_prereg_v36.json"
WORKFLOW = ROOT / ".github" / "workflows" / "v36-external-prereg.yml"


class ExternalValidationPreregV36Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_registered_protocol_validates(self) -> None:
        validate_prereg(self.payload)
        self.assertEqual(len(canonical_sha256(self.payload)), 64)

    def test_no_row_level_australian_data_are_present_in_prereg_version(self) -> None:
        ensure_no_row_level_external_data_present()

    def test_public_metadata_known_before_row_level_access_is_explicit(self) -> None:
        known = self.payload["source"]["known_from_public_documentation_before_row_level_access"]
        self.assertEqual(known["rows"], 67856)
        self.assertEqual(known["columns"], 9)
        self.assertEqual(known["policies_with_at_least_one_claim"], 4624)
        self.assertEqual(
            known["column_names"],
            ["Exposure", "VehValue", "VehAge", "VehBody", "Gender", "DrivAge", "ClaimOcc", "ClaimNb", "ClaimAmount"],
        )

    def test_claimocc_and_gender_are_excluded_from_primary_features(self) -> None:
        features = self.payload["features"]
        self.assertEqual(features["numeric"], ["VehValue"])
        self.assertEqual(features["categorical"], ["VehAge", "VehBody", "DrivAge"])
        self.assertIn("ClaimOcc", features["excluded_from_predictors"])
        self.assertIn("Gender", features["excluded_from_predictors"])

    def test_locked_split_has_no_outcome_stratification_or_retuning(self) -> None:
        split = self.payload["split"]
        self.assertIn("without outcome stratification", split["method"])
        self.assertEqual(split["seed"], 20260823)
        self.assertEqual(
            (split["train_fraction"], split["calibration_fraction"], split["locked_test_fraction"]),
            (0.60, 0.20, 0.20),
        )
        self.assertFalse(split["test_used_for_hyperparameter_selection"])
        self.assertFalse(split["calibration_used_for_hyperparameter_selection"])
        self.assertFalse(split["resplitting_after_outcome_inspection_allowed"])
        self.assertFalse(self.payload["models"]["hyperparameter_search_allowed"])
        self.assertFalse(self.payload["models"]["early_stopping_allowed"])

    def test_primary_and_secondary_gates_are_frozen(self) -> None:
        self.assertEqual(self.payload["targets"]["primary"]["name"], "frequency")
        self.assertEqual(self.payload["targets"]["secondary_confirmatory"]["name"], "pure_premium")
        gate = self.payload["registered_external_replication_gate"]
        self.assertEqual(gate["minimum_relative_deviance_improvement"], 0.005)
        self.assertEqual(gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"], 0.0)
        self.assertEqual(gate["maximum_additional_abs_log_aggregate_calibration_error"], 0.01)
        bootstrap = self.payload["paired_bootstrap"]
        self.assertEqual(bootstrap["draws"], 500)
        self.assertEqual(bootstrap["seed"], 20260824)

    def test_positive_external_result_cannot_directly_promote(self) -> None:
        decision = self.payload["decision_boundary"]
        self.assertEqual(decision["model_family_decision_after_v36"], "HOLD")
        self.assertEqual(decision["serving_status_after_v36"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["external_replication_can_directly_authorise_model_promotion"])
        self.assertFalse(decision["external_replication_can_directly_authorise_customer_pricing"])
        self.assertTrue(decision["no_rule_split_or_hyperparameter_changes_after_test_results"])

    def test_relaxing_registered_gate_fails_validation(self) -> None:
        changed = json.loads(json.dumps(self.payload))
        changed["registered_external_replication_gate"]["minimum_relative_deviance_improvement"] = 0.0
        with self.assertRaises(ExternalPreregistrationError):
            validate_prereg(changed)

    def test_v36_workflow_contains_no_row_level_download_step(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        lower = workflow.lower()
        for forbidden in ("curl ", "wget ", "pyreadr", "ausprivauto0405.rda"):
            self.assertNotIn(forbidden, lower)
        self.assertIn("validate_external_validation_prereg_v36.py", workflow)
        self.assertIn("scripts/push_evidence_with_rebase.sh", workflow)


if __name__ == "__main__":
    unittest.main()
