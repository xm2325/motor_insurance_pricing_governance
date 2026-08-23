from __future__ import annotations

import json
import unittest
from pathlib import Path

from validate_external_validation_prereg_v40 import (
    ExternalPreregistrationV40Error,
    canonical_sha256,
    ensure_no_row_level_belgian_data_present,
    validate_prereg,
)

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "governance" / "external_validation_prereg_v40.json"
WORKFLOW = ROOT / ".github" / "workflows" / "v40-belgian-external-prereg.yml"


class ExternalValidationPreregV40Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(PREREG.read_text(encoding="utf-8"))

    def test_registered_protocol_validates(self) -> None:
        validate_prereg(self.payload)
        self.assertEqual(len(canonical_sha256(self.payload)), 64)

    def test_no_row_level_belgian_data_are_present(self) -> None:
        ensure_no_row_level_belgian_data_present()

    def test_public_metadata_is_frozen_before_access(self) -> None:
        known = self.payload["source"]["known_from_public_documentation_before_row_level_access"]
        self.assertEqual(known["rows"], 163212)
        self.assertEqual(known["unique_policyholders"], 163212)
        self.assertEqual(known["columns"], 18)
        self.assertEqual(known["claim_count_field"], "nclaims")
        self.assertEqual(known["aggregate_claim_amount_field"], "amount")

    def test_feature_and_leakage_boundaries_are_frozen(self) -> None:
        features = self.payload["features"]
        self.assertEqual(features["numeric"], ["ageph", "bm", "power", "agec"])
        self.assertEqual(features["categorical"], ["coverage", "fuel", "use", "fleet"])
        for excluded in ("id", "claim", "average", "sex", "postcode", "long", "lat"):
            self.assertIn(excluded, features["excluded_from_predictors"])
        self.assertTrue(features["preprocessing"]["fit_on_training_only"])
        self.assertFalse(features["preprocessing"]["category_pooling_or_target_encoding_allowed"])

    def test_split_is_locked_without_outcome_stratification(self) -> None:
        split = self.payload["split"]
        self.assertIn("without outcome stratification", split["method"])
        self.assertEqual(split["seed"], 20260825)
        self.assertEqual((split["train_fraction"], split["calibration_fraction"], split["locked_test_fraction"]), (0.6, 0.2, 0.2))
        self.assertFalse(split["test_used_for_hyperparameter_selection"])
        self.assertFalse(split["calibration_used_for_hyperparameter_selection"])
        self.assertFalse(split["resplitting_after_outcome_inspection_allowed"])

    def test_numeric_reproducibility_rule_is_stricter_than_v37(self) -> None:
        runtime = self.payload["runtime_reproducibility"]
        self.assertEqual(runtime["thread_environment"], {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        self.assertEqual(runtime["minimum_independent_actions_executions_for_positive_external_support"], 2)
        self.assertTrue(runtime["positive_external_support_requires_matching_registered_decisions"])
        self.assertTrue(runtime["positive_external_support_requires_registered_point_metric_reproducibility"])
        self.assertEqual(runtime["point_metric_relative_tolerance"], 1e-8)
        self.assertEqual(runtime["point_metric_absolute_tolerance"], 1e-10)

    def test_glm_solver_is_explicit_and_no_fallback_is_allowed(self) -> None:
        for name in ("frequency_glm", "pure_premium_glm"):
            model = self.payload["models"][name]
            self.assertEqual(model["solver"], "newton-cholesky")
            self.assertEqual(model["tol"], 1e-10)
            self.assertEqual(model["max_iter"], 500)
            self.assertTrue(model["convergence_required"])
            self.assertFalse(model["fallback_solver_allowed"])
        self.assertFalse(self.payload["models"]["post_result_solver_change_allowed"])

    def test_registered_gate_matches_prior_external_thresholds(self) -> None:
        gate = self.payload["registered_external_replication_gate"]
        self.assertEqual(gate["minimum_relative_deviance_improvement"], 0.005)
        self.assertEqual(gate["bootstrap_relative_improvement_ci_lower_bound_must_exceed"], 0.0)
        self.assertEqual(gate["maximum_additional_abs_log_aggregate_calibration_error"], 0.01)
        self.assertEqual(self.payload["paired_bootstrap"]["draws"], 500)
        self.assertEqual(self.payload["paired_bootstrap"]["seed"], 20260826)

    def test_positive_result_cannot_directly_promote_or_change_pricing(self) -> None:
        decision = self.payload["decision_boundary"]
        self.assertEqual(decision["model_family_decision_after_v40"], "HOLD")
        self.assertEqual(decision["serving_status_after_v40"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["external_replication_can_directly_authorise_model_promotion"])
        self.assertFalse(decision["external_replication_can_directly_authorise_customer_pricing"])
        self.assertTrue(decision["execution_allowed_only_after_preregistration_is_on_main"])

    def test_relaxing_reproducibility_or_gate_fails_closed(self) -> None:
        changed = json.loads(json.dumps(self.payload))
        changed["runtime_reproducibility"]["minimum_independent_actions_executions_for_positive_external_support"] = 1
        with self.assertRaises(ExternalPreregistrationV40Error):
            validate_prereg(changed)
        changed = json.loads(json.dumps(self.payload))
        changed["registered_external_replication_gate"]["minimum_relative_deviance_improvement"] = 0.0
        with self.assertRaises(ExternalPreregistrationV40Error):
            validate_prereg(changed)

    def test_workflow_contains_no_belgian_row_level_download(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        lower = workflow.lower()
        for forbidden in ("curl ", "wget ", "pyreadr", "bemtpl97.rda", "download_belgian"):
            self.assertNotIn(forbidden, lower)
        self.assertIn("validate_external_validation_prereg_v40.py", workflow)
        self.assertIn("scripts/push_evidence_with_rebase.sh", workflow)


if __name__ == "__main__":
    unittest.main()
