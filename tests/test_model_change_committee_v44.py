import json
import unittest
from pathlib import Path

import build_model_change_committee_decision_v44 as builder
from governance.model_change_committee_v44 import (
    EVIDENCE_GAP_HOLD,
    READY_FOR_HUMAN_REVIEW,
    GateInput,
    evaluate_change_request,
)

ROOT = Path(__file__).resolve().parents[1]


class ModelChangeCommitteeV44Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        builder.main()
        cls.policy = json.loads(
            (ROOT / "governance/model_change_committee_policy_v44.json").read_text(encoding="utf-8")
        )
        cls.result = json.loads(
            (ROOT / "results_v44/model_change_committee_decision_v44.json").read_text(encoding="utf-8")
        )

    def test_current_request_is_evidence_gap_hold(self):
        d = self.result["machine_gate_decision"]
        self.assertEqual(d["status"], EVIDENCE_GAP_HOLD)
        self.assertEqual(d["required_gate_count"], 8)
        self.assertEqual(d["required_gate_pass_count"], 5)
        self.assertEqual(d["required_gate_fail_count"], 3)
        self.assertFalse(d["human_committee_review_open"])

    def test_exact_blockers_are_validation_evidence_gaps(self):
        self.assertEqual(
            self.result["machine_gate_decision"]["blocker_ids"],
            [
                "G2_LOCKED_TEMPORAL_SUPPORT",
                "G3_PREREGISTERED_EXTERNAL_SUPPORT",
                "G4_FRESH_INDEPENDENT_EVIDENCE",
            ],
        )

    def test_operational_readiness_cannot_compensate_for_evidence_failure(self):
        op = self.result["operational_readiness"]
        self.assertTrue(op["shadow_deployment_boundary"])
        self.assertTrue(op["release_and_rollback_control"])
        self.assertTrue(op["attested_shadow_admission"])
        self.assertEqual(self.result["machine_gate_decision"]["status"], EVIDENCE_GAP_HOLD)

    def test_benchmark_signal_cannot_override_validation_failure(self):
        self.assertTrue(self.result["evidence_readiness"]["development_signal_present"])
        self.assertFalse(self.result["evidence_readiness"]["locked_temporal_support"])
        self.assertFalse(self.result["evidence_readiness"]["preregistered_external_support"])
        self.assertFalse(self.policy["decision_policy"]["benchmark_can_override_validation_failure"])

    def test_human_signoff_flag_cannot_override_failed_evidence(self):
        decision = evaluate_change_request(
            "synthetic-failed",
            [
                GateInput("EVIDENCE", False, "failed evidence"),
                GateInput("OPERATIONS", True, "operationally ready"),
            ],
            human_signoff_recorded=True,
        )
        self.assertEqual(decision.status, EVIDENCE_GAP_HOLD)
        self.assertFalse(decision.human_committee_review_open)
        self.assertTrue(decision.human_signoff_recorded)
        self.assertFalse(decision.human_signoff_can_override_failed_evidence_gate)
        self.assertFalse(decision.automatic_model_promotion_authorised)
        self.assertFalse(decision.automatic_customer_pricing_change_authorised)

    def test_all_machine_gates_can_only_open_human_review_not_promote(self):
        decision = evaluate_change_request(
            "synthetic-all-pass",
            [GateInput(f"G{i}", True, "synthetic pass") for i in range(1, 5)],
        )
        self.assertEqual(decision.status, READY_FOR_HUMAN_REVIEW)
        self.assertTrue(decision.human_committee_review_open)
        self.assertFalse(decision.automatic_model_promotion_authorised)
        self.assertFalse(decision.automatic_customer_pricing_change_authorised)

    def test_duplicate_or_empty_gates_fail_closed(self):
        with self.assertRaises(ValueError):
            evaluate_change_request("empty", [])
        with self.assertRaises(ValueError):
            evaluate_change_request(
                "duplicate",
                [GateInput("G1", True, "a"), GateInput("G1", False, "b")],
            )

    def test_policy_never_allows_automatic_promotion_or_pricing(self):
        p = self.policy["decision_policy"]
        self.assertFalse(p["automatic_model_promotion_allowed"])
        self.assertFalse(p["automatic_customer_pricing_change_allowed"])
        self.assertFalse(p["human_signoff_can_override_failed_evidence_gate"])
        self.assertFalse(p["consumed_validation_can_be_relabelled_fresh"])

    def test_no_first_central_or_uk_transfer_claim(self):
        boundary = self.result["governance_boundary"]
        self.assertTrue(boundary["project_demo_not_insurer_policy"])
        self.assertFalse(boundary["first_central_or_current_uk_transport_claimed"])
        self.assertFalse(boundary["human_committee_decision_recorded"])
        self.assertFalse(boundary["customer_pricing_authority_present"])


if __name__ == "__main__":
    unittest.main()
