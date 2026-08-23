from __future__ import annotations

import json
import unittest
from pathlib import Path

from build_belgian_external_closeout_v42 import (
    ORIGIN_RESULT_PATH,
    ORIGIN_STATUS_PATH,
    _within_registered_tolerance,
    build_closeout,
)

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "governance" / "belgian_external_reproducibility_observations_v42.json"
LEDGER = ROOT / "governance" / "external_validation_use_ledger_v42.json"
PREREG = ROOT / "governance" / "external_validation_prereg_v40.json"
WORKFLOW = ROOT / ".github" / "workflows" / "v42-belgian-external-closeout.yml"


class BelgianExternalCloseoutV42Tests(unittest.TestCase):
    def test_closeout_builds_from_persisted_aggregate_evidence(self) -> None:
        result = build_closeout()
        self.assertEqual(result["status"], "V42_BELGIAN_EXTERNAL_CLOSEOUT_PASS")
        reproducibility = result["reproducibility"]
        self.assertEqual(reproducibility["completed_model_execution_run_ids"], [32637809066, 32637884887])
        self.assertEqual(reproducibility["observed_regions"], ["eastus2", "centralus"])
        self.assertEqual(reproducibility["aborted_pre_fit_run_id"], 32637645586)
        self.assertFalse(reproducibility["aborted_run_counted_as_completed_execution"])
        self.assertTrue(reproducibility["all_registered_numeric_metrics_within_tolerance"])
        self.assertTrue(reproducibility["registered_decisions_match"])
        self.assertLessEqual(reproducibility["max_absolute_difference"], 1e-10)
        self.assertLessEqual(reproducibility["max_relative_difference"], 1e-8)
        self.assertFalse(reproducibility["universal_bitwise_determinism_claimed"])
        self.assertFalse(reproducibility["hardware_or_region_cause_claimed"])

    def test_registered_negative_results_remain_negative(self) -> None:
        result = build_closeout()
        registered = result["registered_results"]
        self.assertEqual(registered["frequency_decision"], "NO_SECOND_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT")
        self.assertEqual(registered["pure_premium_decision"], "NO_SECOND_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT")
        self.assertAlmostEqual(registered["frequency_relative_deviance_improvement"], 0.0029096217823043613)
        self.assertAlmostEqual(registered["frequency_bootstrap_q025"], 0.000987214124322794)
        self.assertAlmostEqual(registered["pure_premium_relative_deviance_improvement"], 0.0032188406333756303)
        self.assertAlmostEqual(registered["pure_premium_bootstrap_q025"], -0.007917598068074487)
        self.assertFalse(registered["positive_gate_present"])
        self.assertFalse(registered["positive_support_reproduction_required_for_observed_result"])

    def test_observed_large_margin_metric_change_would_fail_registered_tolerance(self) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        runtime = prereg["runtime_reproducibility"]
        self.assertTrue(_within_registered_tolerance(79.84331051378417, 79.84331051378416, rel_tol=runtime["point_metric_relative_tolerance"], abs_tol=runtime["point_metric_absolute_tolerance"]))
        self.assertFalse(_within_registered_tolerance(79.84331051378417, 79.84, rel_tol=runtime["point_metric_relative_tolerance"], abs_tol=runtime["point_metric_absolute_tolerance"]))

    def test_main_execution_is_immutable_origin_evidence(self) -> None:
        status = json.loads(ORIGIN_STATUS_PATH.read_text(encoding="utf-8"))
        result = json.loads(ORIGIN_RESULT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(status["run_id"], "32637884887")
        self.assertEqual(status["sha"], "241df6c2b6e6f20472a0bc236b27474c9b20583b")
        self.assertEqual(status["evidence_role"], "IMMUTABLE_EXECUTION_SNAPSHOT")
        self.assertFalse(status["raw_external_data_persisted"])
        self.assertFalse(status["positive_external_support_authorised"])
        self.assertEqual(result["source"]["file_sha256"], "955a821a7a693bf18076c425e4d5a5a99889f3c89e1fbd99eca6239c11e963a6")
        self.assertEqual(result["source"]["rows"], 163212)
        self.assertEqual(result["split"]["locked_test"]["rows"], 32643)

    def test_pre_fit_source_access_abort_is_not_model_evidence(self) -> None:
        observations = json.loads(OBSERVATIONS.read_text(encoding="utf-8"))
        event = observations["execution_events"][0]
        self.assertEqual(event["run_id"], 32637645586)
        self.assertEqual(event["role"], "SOURCE_ACCESSED_ABORTED_BEFORE_MODEL_FIT")
        self.assertTrue(event["row_level_source_accessed"])
        self.assertFalse(event["model_fit_completed"])
        self.assertFalse(event["locked_test_metrics_generated"])
        self.assertFalse(event["counted_as_completed_model_execution"])

    def test_belgian_locked_test_is_consumed_for_future_candidate_selection(self) -> None:
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(ledger["current_role"], "CONSUMED_EXTERNAL_VALIDATION_DATASET")
        self.assertFalse(ledger["independent_external_validation_available"])
        self.assertFalse(ledger["candidate_selection_allowed"])
        self.assertFalse(ledger["fresh_independent_confirmation_allowed"])
        for forbidden in (
            "fit_new_model_parameters",
            "fit_new_calibration_parameters",
            "hyperparameter_search",
            "change_feature_set_after_outcome_inspection",
            "change_solver_or_tolerance_to_improve_locked_test_result",
            "resplit_or_reseed_for_candidate_selection",
            "select_new_candidate_policy",
            "independent_confirmation",
            "authorise_model_family_promotion",
            "authorise_customer_pricing",
        ):
            self.assertIn(forbidden, ledger["forbidden_future_purposes"])

    def test_governance_stays_hold_shadow_only(self) -> None:
        result = build_closeout()
        self.assertEqual(result["decision"], {
            "model_family_decision": "HOLD",
            "serving_status": "HOLD_SHADOW_ONLY",
            "model_promotion_authorised": False,
            "pricing_change_authorised": False,
        })

    def test_closeout_workflow_is_aggregate_only(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8").lower()
        for forbidden in (
            "download_belgian_motor_v41.py",
            "run_belgian_external_replication_v41.py",
            "pyreadr",
            "bemtpl97.rda",
            "curl ",
            "wget ",
            "pip install -r requirements.txt",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("build_belgian_external_closeout_v42.py", text)
        self.assertIn("scripts/push_evidence_with_rebase.sh", text)


if __name__ == "__main__":
    unittest.main()
