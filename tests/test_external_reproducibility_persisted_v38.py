from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "action_results" / "v38" / "ACTION_V38_STATUS.json"
PERSISTED = ROOT / "action_results" / "v38" / "external_reproducibility_audit_v38.json"
REGISTERED = ROOT / "governance" / "external_reproducibility_audit_v38.json"
V37_STATUS = ROOT / "action_results" / "v37" / "ACTION_V37_STATUS.json"
V37_SUMMARY = ROOT / "action_results" / "v37" / "australian_external_replication_summary.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PersistedExternalReproducibilityV38Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))
        cls.audit = json.loads(PERSISTED.read_text(encoding="utf-8"))
        cls.v37_status = json.loads(V37_STATUS.read_text(encoding="utf-8"))
        cls.v37 = json.loads(V37_SUMMARY.read_text(encoding="utf-8"))

    def test_main_v38_workflow_is_locked(self) -> None:
        self.assertEqual(self.status["workflow"], "External validation numerical reproducibility audit v0.38")
        self.assertEqual(self.status["run_id"], "32634180356")
        self.assertEqual(self.status["sha"], "1ab61c36ed4ad8002d7f3e4391446e88af5c44c1")
        self.assertEqual(self.status["status"], "success")
        self.assertTrue(self.status["v37_decision_reproduced"])
        self.assertFalse(self.status["pure_premium_point_metric_exactly_reproduced"])

    def test_persisted_audit_matches_registered_audit_byte_for_byte(self) -> None:
        self.assertEqual(digest(PERSISTED), digest(REGISTERED))
        self.assertEqual(self.audit["status"], "V38_DECISION_REPRODUCIBLE_METRIC_VARIATION_REVIEW")

    def test_authoritative_v37_main_evidence_is_not_replaced_by_pr_metric(self) -> None:
        auth = self.audit["authoritative_v37_evidence"]
        self.assertEqual(auth["workflow_run_id"], "32633520755")
        self.assertEqual(auth["source_sha"], "1e975b5258f3442da5c72dd9794fad2bf5303ae6")
        self.assertEqual(
            auth["summary_sha256"],
            "da7c30aef7e5e810755b9fb15a4749757c25af79ff4d553ed775d71be0f71017",
        )
        self.assertEqual(self.v37_status["run_id"], "32633520755")
        self.assertEqual(self.v37["pure_premium"]["locked_test"]["reference_deviance"], 129.8409094852542)

    def test_decision_reproducibility_and_metric_variation_are_both_retained(self) -> None:
        rec = self.audit["reconciliation"]
        self.assertTrue(rec["frequency_decision_reproduced"])
        self.assertTrue(rec["pure_premium_decision_reproduced"])
        self.assertFalse(rec["pure_premium_glm_point_metric_exactly_reproduced"])
        self.assertGreater(rec["pure_premium_glm_deviance_relative_difference_pr_denominator"], 0.02)
        self.assertFalse(self.audit["decision"]["v37_pure_premium_point_metric_exact_reproducibility_claim_allowed"])

    def test_future_policy_is_fail_closed_for_positive_external_claims(self) -> None:
        policy = self.audit["future_external_evidence_policy"]
        self.assertEqual(policy["minimum_independent_actions_executions_for_positive_gate"], 2)
        self.assertTrue(policy["decision_labels_must_agree"])
        self.assertTrue(policy["positive_external_support_requires_metric_reproducibility"])
        self.assertIn("NO_POSITIVE_EXTERNAL_CLAIM", policy["if_decision_labels_disagree"])
        self.assertTrue(policy["future_iterative_estimators_must_explicitly_register_solver_and_tolerance"])
        self.assertTrue(policy["no_retroactive_change_to_v36_protocol"])

    def test_governance_remains_hold(self) -> None:
        decision = self.audit["decision"]
        self.assertFalse(decision["v37_frequency_external_support"])
        self.assertFalse(decision["v37_pure_premium_external_support"])
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])


if __name__ == "__main__":
    unittest.main()
