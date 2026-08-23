from __future__ import annotations

import hashlib
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "governance" / "external_reproducibility_audit_v38.json"
ROLLING_SUMMARY_PATH = ROOT / "action_results" / "v37" / "australian_external_replication_summary.json"
ROLLING_STATUS_PATH = ROOT / "action_results" / "v37" / "ACTION_V37_STATUS.json"
ORIGIN_DIR = ROOT / "action_results" / "v37" / "origin_main_32633520755"
ORIGIN_SUMMARY_PATH = ORIGIN_DIR / "australian_external_replication_summary.json"
ORIGIN_SOURCE_PATH = ORIGIN_DIR / "australian_source_audit.json"
ORIGIN_MANIFEST_PATH = ORIGIN_DIR / "ORIGIN_MANIFEST.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExternalReproducibilityEvidenceV38Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.origin = json.loads(ORIGIN_SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.origin_manifest = json.loads(ORIGIN_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.rolling = json.loads(ROLLING_SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.rolling_status = json.loads(ROLLING_STATUS_PATH.read_text(encoding="utf-8"))

    def test_origin_main_v37_evidence_is_immutably_locked(self) -> None:
        auth = self.audit["authoritative_v37_evidence"]
        self.assertEqual(auth["workflow_run_id"], "32633520755")
        self.assertEqual(auth["source_sha"], "1e975b5258f3442da5c72dd9794fad2bf5303ae6")
        self.assertEqual(
            sha256(ORIGIN_SUMMARY_PATH),
            "da7c30aef7e5e810755b9fb15a4749757c25af79ff4d553ed775d71be0f71017",
        )
        self.assertEqual(sha256(ORIGIN_SUMMARY_PATH), auth["summary_sha256"])
        self.assertEqual(
            sha256(ORIGIN_SOURCE_PATH),
            "ee933f9c051a2f4c25198beb0b7ab8fb275e0ccc0b09efd9a372db0fb94c895e",
        )
        self.assertEqual(self.origin_manifest["evidence_role"], "IMMUTABLE_ORIGIN_MAIN_SNAPSHOT")
        self.assertEqual(self.origin_manifest["workflow_run_id"], "32633520755")
        self.assertEqual(self.origin_manifest["artifact_id"], "9491692169")
        self.assertFalse(self.origin_manifest["raw_external_data_persisted"])

    def test_protocol_was_locked_before_origin_row_level_execution(self) -> None:
        prereg = self.origin["preregistration"]
        self.assertEqual(
            prereg["sha256"],
            "b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1",
        )
        self.assertEqual(prereg["v36_main_sha"], "49339232a6b913e111b6e4e66dfa4517d9396bc9")
        self.assertTrue(prereg["registered_before_row_level_access"])
        self.assertFalse(prereg["rules_changed_after_registration"])
        self.assertFalse(self.origin["source"]["raw_data_persisted_to_repository"])
        self.assertFalse(self.origin["split"]["outcome_stratified"])
        self.assertFalse(self.origin["split"]["resplit_after_outcome_inspection"])

    def test_origin_frequency_negative_replication_is_preserved(self) -> None:
        frequency = self.origin["frequency"]
        self.assertTrue(math.isclose(frequency["locked_test"]["reference_deviance"], 0.8147417525935061))
        self.assertTrue(math.isclose(frequency["locked_test"]["challenger_deviance"], 0.8178777253238009))
        self.assertLess(frequency["locked_test"]["relative_deviance_improvement"], 0.0)
        bootstrap = frequency["paired_bootstrap_relative_deviance_improvement"]
        self.assertEqual(bootstrap["draws"], 500)
        self.assertLess(bootstrap["q975"], 0.0)
        self.assertTrue(math.isclose(bootstrap["positive_draw_rate"], 0.018))
        self.assertEqual(
            frequency["registered_gate"]["decision"],
            "NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT",
        )
        self.assertFalse(frequency["registered_gate"]["passed"])

    def test_origin_pure_premium_point_result_is_not_misrepresented_as_confirmatory(self) -> None:
        pure = self.origin["pure_premium"]
        self.assertTrue(math.isclose(pure["locked_test"]["reference_deviance"], 129.8409094852542))
        self.assertTrue(math.isclose(pure["locked_test"]["challenger_deviance"], 114.95606738904532))
        self.assertTrue(math.isclose(pure["locked_test"]["relative_deviance_improvement"], 0.11463907758516845))
        bootstrap = pure["paired_bootstrap_relative_deviance_improvement"]
        self.assertLess(bootstrap["q025"], 0.0)
        self.assertTrue(math.isclose(bootstrap["positive_draw_rate"], 0.618))
        self.assertEqual(
            pure["registered_gate"]["decision"],
            "NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT",
        )
        self.assertFalse(pure["registered_gate"]["passed"])

    def test_rolling_latest_can_change_run_identity_and_point_family_but_not_gate(self) -> None:
        self.assertEqual(self.rolling_status["workflow"], "Australian external motor replication v0.37")
        self.assertEqual(self.rolling_status["status"], "success")
        self.assertFalse(self.rolling_status["raw_external_data_persisted"])
        self.assertEqual(
            self.rolling["source"]["file_sha256"],
            "c8aeabd0b75e16a2b9a7452cfb3e8e2b3ec36a27171d35c2862bc8278777461c",
        )
        self.assertEqual(
            self.rolling["frequency"]["registered_gate"]["decision"],
            "NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT",
        )
        self.assertEqual(
            self.rolling["pure_premium"]["registered_gate"]["decision"],
            "NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT",
        )
        self.assertIn(
            sha256(ROLLING_SUMMARY_PATH),
            {
                "6f3fd009e70fdb3eaebcfe46126b14bf853848ac164ac8ce23059daa8974d7df",
                "da7c30aef7e5e810755b9fb15a4749757c25af79ff4d553ed775d71be0f71017",
            },
        )

    def test_three_execution_audit_preserves_metric_instability(self) -> None:
        self.assertEqual(self.audit["status"], "V38_DECISION_REPRODUCIBLE_METRIC_VARIATION_REVIEW")
        executions = self.audit["executions"]
        self.assertEqual(len(executions), 3)
        self.assertEqual([x["runner_region"] for x in executions], ["centralus", "westcentralus", "northcentralus"])
        self.assertEqual(executions[0]["summary_sha256"], executions[1]["summary_sha256"])
        self.assertNotEqual(executions[0]["summary_sha256"], executions[2]["summary_sha256"])
        self.assertEqual(executions[0]["source_audit_sha256"], executions[2]["source_audit_sha256"])
        self.assertTrue(math.isclose(executions[0]["pure_premium_reference_deviance"], 126.22046948252975))
        self.assertTrue(math.isclose(executions[2]["pure_premium_reference_deviance"], 129.8409094852542))
        self.assertEqual(
            {x["pure_premium_decision"] for x in executions},
            {"NO_EXTERNAL_PURE_PREMIUM_REPLICATION_SUPPORT"},
        )
        self.assertEqual(
            {x["frequency_decision"] for x in executions},
            {"NO_EXTERNAL_FREQUENCY_REPLICATION_SUPPORT"},
        )

    def test_reconciliation_does_not_claim_unproven_root_cause(self) -> None:
        rec = self.audit["reconciliation"]
        self.assertTrue(rec["source_audit_identical_across_observed_runs"])
        self.assertTrue(rec["dependency_versions_identical"])
        self.assertTrue(rec["runner_image_version_identical"])
        self.assertTrue(rec["runner_regions_differed"])
        self.assertTrue(rec["frequency_decision_reproduced"])
        self.assertTrue(rec["pure_premium_decision_reproduced"])
        self.assertFalse(rec["pure_premium_glm_point_metric_exactly_reproduced"])
        self.assertTrue(math.isclose(rec["pure_premium_glm_deviance_relative_difference_pr_denominator"], 0.02868346170448651))
        self.assertIn("consistent with", rec["observed_cause_boundary"])
        self.assertIn("does not establish", rec["observed_cause_boundary"])

    def test_future_positive_external_evidence_requires_reproducibility(self) -> None:
        policy = self.audit["future_external_evidence_policy"]
        self.assertTrue(policy["applies_to_protocols_registered_after_v38"])
        self.assertEqual(policy["minimum_independent_actions_executions_for_positive_gate"], 2)
        self.assertTrue(policy["decision_labels_must_agree"])
        self.assertTrue(policy["positive_external_support_requires_metric_reproducibility"])
        self.assertTrue(policy["record_iterative_solver_convergence_metadata"])
        self.assertTrue(policy["future_iterative_estimators_must_explicitly_register_solver_and_tolerance"])
        self.assertEqual(policy["future_thread_environment_defaults"]["OMP_NUM_THREADS"], "1")
        self.assertEqual(policy["future_thread_environment_defaults"]["OPENBLAS_NUM_THREADS"], "1")
        self.assertEqual(policy["future_thread_environment_defaults"]["MKL_NUM_THREADS"], "1")
        self.assertTrue(policy["no_retroactive_change_to_v36_protocol"])

    def test_governance_stays_hold(self) -> None:
        decision = self.audit["decision"]
        self.assertFalse(decision["v37_frequency_external_support"])
        self.assertFalse(decision["v37_pure_premium_external_support"])
        self.assertTrue(decision["v37_decision_reproducible_across_observed_runs"])
        self.assertFalse(decision["v37_pure_premium_point_metric_exact_reproducibility_claim_allowed"])
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])


if __name__ == "__main__":
    unittest.main()
