import json
import unittest
from pathlib import Path

P = json.loads(Path("governance/model_change_reachability_policy_v59.json").read_text(encoding="utf-8"))
V44_POLICY = json.loads(Path("governance/model_change_committee_policy_v44.json").read_text(encoding="utf-8"))
V44_DECISION = json.loads(Path("action_results/v44/model_change_committee_decision_v44.json").read_text(encoding="utf-8"))
V43 = json.loads(Path("action_results/v43/model_family_evidence_synthesis_summary.json").read_text(encoding="utf-8"))


class ModelChangeReachabilityV59Tests(unittest.TestCase):
    def test_existing_request_identity_is_fixed(self):
        self.assertEqual(P["request_id"], "MCR-XGB-MOTOR-001")
        self.assertEqual(V44_POLICY["candidate_change_request"]["request_id"], P["request_id"])
        self.assertEqual(V44_DECISION["request"]["request_id"], P["request_id"])

    def test_g2_is_defined_on_original_locked_temporal_evaluation(self):
        gate = next(g for g in V44_POLICY["gates"] if g["id"] == "G2_LOCKED_TEMPORAL_SUPPORT")
        self.assertEqual(
            gate["description"],
            "The original locked temporal evaluation supports a global model-family change under its registered rule.",
        )
        result = next(g for g in V44_DECISION["gate_results"] if g["gate_id"] == "G2_LOCKED_TEMPORAL_SUPPORT")
        self.assertFalse(result["passed"])
        self.assertEqual(result["status"], "FAIL")

    def test_both_spanish_locked_target_decisions_are_hold(self):
        spanish = {
            x["id"]: x for x in V43["evidence_basis"]
            if x["id"] in {"spanish_2024_frequency", "spanish_2024_pure_premium"}
        }
        self.assertEqual(set(spanish), {"spanish_2024_frequency", "spanish_2024_pure_premium"})
        for item in spanish.values():
            self.assertEqual(item["registered_decision"], "HOLD")
            self.assertFalse(item["gate_passed"])

    def test_failed_evidence_cannot_be_overridden_or_relabelled(self):
        d = V44_POLICY["decision_policy"]
        self.assertTrue(d["all_required_gates_must_pass_to_advance_to_human_review"])
        self.assertFalse(d["human_signoff_can_override_failed_evidence_gate"])
        self.assertFalse(d["benchmark_can_override_validation_failure"])
        self.assertFalse(d["consumed_validation_can_be_relabelled_fresh"])

    def test_stop_rule_does_not_rewrite_existing_policy(self):
        h = P["historical_integrity_rules"]
        self.assertTrue(h["existing_request_id_must_not_change"])
        self.assertTrue(h["existing_gate_descriptions_must_not_change"])
        self.assertTrue(h["original_locked_spanish_gate_result_must_not_be_relabelled"])
        self.assertTrue(P["stop_rule"]["a_new_change_request_must_not_relabel_or_delete_the_failed_MCR_XGB_MOTOR_001_history"])

    def test_v59_is_no_data_no_candidate_selection(self):
        workflow = Path(".github/workflows/v59-committee-reachability.yml").read_text(encoding="utf-8")
        forbidden = ["pyreadr", "curl ", "wget ", "data_external", "pg15training.rda", "euMTPL.rda", "beMTPL97.rda", "ausprivauto0405.rda"]
        for token in forbidden:
            self.assertNotIn(token, workflow)
        runner = Path("audit_model_change_reachability_v59.py").read_text(encoding="utf-8")
        self.assertNotIn("sklearn", runner)
        self.assertNotIn("xgboost", runner)

    def test_current_policy_has_exact_three_blockers(self):
        blockers = V44_DECISION["machine_gate_decision"]["blocker_ids"]
        self.assertEqual(blockers, [
            "G2_LOCKED_TEMPORAL_SUPPORT",
            "G3_PREREGISTERED_EXTERNAL_SUPPORT",
            "G4_FRESH_INDEPENDENT_EVIDENCE",
        ])
        self.assertEqual(V44_DECISION["machine_gate_decision"]["required_gate_pass_count"], 5)
        self.assertEqual(V44_DECISION["machine_gate_decision"]["required_gate_count"], 8)

    def test_audit_does_not_authorise_any_operational_change(self):
        b = P["governance_boundary"]
        self.assertTrue(b["this_audit_does_not_authorise_a_new_change_request"])
        self.assertTrue(b["this_audit_does_not_authorise_model_promotion"])
        self.assertTrue(b["this_audit_does_not_authorise_customer_pricing"])
        self.assertFalse(b["first_central_or_current_uk_transport_claimed"])


if __name__ == "__main__":
    unittest.main()
