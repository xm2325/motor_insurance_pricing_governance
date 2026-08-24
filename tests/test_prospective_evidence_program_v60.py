import json
import unittest
from pathlib import Path

T = json.loads(Path("governance/prospective_evidence_program_template_v60.json").read_text(encoding="utf-8"))


class ProspectiveEvidenceProgramV60Tests(unittest.TestCase):
    def test_template_is_not_an_active_request(self):
        self.assertEqual(T["status"], "V60_PROSPECTIVE_EVIDENCE_PROGRAM_TEMPLATE_NOT_ACTIVE_REQUEST")
        self.assertIsNone(T["future_request_registration"]["active_request_id"])
        self.assertIsNone(T["future_request_registration"]["selected_scope_mode"])
        self.assertTrue(T["future_request_registration"]["template_does_not_authorise_MCR_XGB_MOTOR_002"])

    def test_failed_mcr001_history_is_preserved(self):
        parent = T["historical_parent"]
        self.assertEqual(parent["request_id"], "MCR-XGB-MOTOR-001")
        self.assertEqual(parent["required_state"], "TERMINAL_EVIDENCE_GAP_HOLD_FOR_EXISTING_REQUEST")
        self.assertTrue(parent["history_must_remain_visible"])
        self.assertTrue(parent["old_gate_results_may_not_be_relabelled"])
        self.assertTrue(parent["old_request_is_not_reopened_by_this_template"])

    def test_three_pairwise_distinct_fresh_evidence_roles_are_required(self):
        stages = {x["stage_id"]: x for x in T["fresh_evidence_stages"]}
        self.assertEqual(set(stages), {
            "S1_LOCKED_TEMPORAL_QUALIFICATION",
            "S2_INDEPENDENT_EXTERNAL_REPLICATION",
            "S3_SEALED_RESERVE_CONFIRMATION",
        })
        self.assertEqual(T["independence_contract"]["minimum_pairwise_distinct_fresh_source_identities"], 3)
        self.assertTrue(T["independence_contract"]["one_dataset_cannot_simultaneously_count_as_qualification_replication_and_reserve"])
        self.assertEqual(stages["S2_INDEPENDENT_EXTERNAL_REPLICATION"]["must_be_distinct_from"], ["S1_LOCKED_TEMPORAL_QUALIFICATION"])
        self.assertEqual(set(stages["S3_SEALED_RESERVE_CONFIRMATION"]["must_be_distinct_from"]), {
            "S1_LOCKED_TEMPORAL_QUALIFICATION",
            "S2_INDEPENDENT_EXTERNAL_REPLICATION",
        })

    def test_reserve_is_sealed_and_cannot_rescue_failure(self):
        reserve = next(x for x in T["fresh_evidence_stages"] if x["stage_id"] == "S3_SEALED_RESERVE_CONFIRMATION")
        self.assertTrue(reserve["must_remain_row_level_unaccessed_until_separate_authorised_release"])
        self.assertFalse(reserve["can_be_used_for_candidate_selection"])
        self.assertFalse(reserve["can_be_used_to_rescue_failed_S1_or_S2"])

    def test_evidence_budget_prevents_dataset_shopping(self):
        b = T["evidence_budget_and_stop_rules"]
        self.assertEqual(b["maximum_fresh_source_identities_registered_for_S1"], 1)
        self.assertEqual(b["maximum_fresh_source_identities_registered_for_S2"], 1)
        self.assertEqual(b["maximum_fresh_source_identities_registered_for_S3"], 1)
        self.assertFalse(b["replace_failed_S1_with_another_dataset_allowed"])
        self.assertFalse(b["replace_failed_S2_with_another_dataset_allowed"])
        self.assertFalse(b["promote_S3_to_rescue_failed_S1_or_S2_allowed"])
        self.assertFalse(b["change_target_scope_after_failure_allowed"])
        self.assertFalse(b["weaken_performance_gate_after_failure_allowed"])

    def test_scope_must_be_selected_prospectively(self):
        r = T["future_request_registration"]
        self.assertTrue(r["scope_must_be_selected_before_fresh_outcome_access"])
        self.assertTrue(r["target_scope_cannot_change_after_first_fresh_outcome_access"])
        self.assertEqual(set(r["allowed_scope_modes"]), {"FREQUENCY_ONLY", "PURE_PREMIUM_ONLY", "GLOBAL_TWO_TARGET"})
        self.assertIn("both frequency and pure-premium registered gates must pass", T["scope_gate_logic"]["GLOBAL_TWO_TARGET"])

    def test_project_gate_thresholds_are_not_weakened(self):
        g = T["registered_default_performance_gate"]
        self.assertEqual(g["minimum_relative_deviance_improvement"], 0.005)
        self.assertEqual(g["bootstrap_relative_improvement_ci_lower_bound_must_exceed"], 0.0)
        self.assertEqual(g["maximum_additional_abs_log_aggregate_calibration_error"], 0.01)
        self.assertEqual(g["calibration_scale_guardrails"], [0.5, 2.0])
        self.assertFalse(g["calibration_scale_clipping_allowed"])
        self.assertEqual(g["paired_bootstrap_draws"], 500)
        self.assertTrue(g["thresholds_are_project_review_rules_not_insurer_or_regulatory_standards"])

    def test_positive_support_keeps_two_run_reproducibility(self):
        r = T["reproducibility_contract"]
        self.assertEqual(r["minimum_independent_actions_executions_for_positive_support"], 2)
        self.assertTrue(r["matching_registered_decision_required"])
        self.assertTrue(r["registered_metric_tolerance_required"])
        self.assertTrue(r["single_thread_numerical_defaults_required"])
        self.assertTrue(r["iterative_solver_and_tolerance_must_be_explicit"])
        self.assertFalse(r["post_result_solver_or_hyperparameter_change_allowed"])

    def test_current_state_remains_hold_and_no_data(self):
        c = T["current_state"]
        self.assertTrue(c["template_only"])
        self.assertFalse(c["fresh_source_identity_selected"])
        self.assertFalse(c["row_level_external_data_accessed"])
        self.assertFalse(c["outcome_values_inspected"])
        self.assertFalse(c["candidate_selection_performed"])
        self.assertEqual(c["model_family_decision"], "HOLD")
        self.assertEqual(c["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(c["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(c["customer_pricing_authorised"])


if __name__ == "__main__":
    unittest.main()
