import json
import unittest
from pathlib import Path

P = json.loads(Path("governance/external_temporal_prereg_v57.json").read_text(encoding="utf-8"))
V40 = json.loads(Path("governance/external_validation_prereg_v40.json").read_text(encoding="utf-8"))
V56 = json.loads(Path("action_results/v56/ACTION_V56_STATUS.json").read_text(encoding="utf-8"))


class ExternalTemporalPreregV57Tests(unittest.TestCase):
    def test_protocol_is_locked_before_first_execution(self):
        self.assertEqual(P["status"], "V57_EUMTPL_EXTERNAL_TEMPORAL_PREREGISTRATION_LOCKED")
        self.assertTrue(P["protocol_locked_before_first_v57_execution"])
        self.assertEqual(P["base_repository_commit"], "8100497c7b26d51856b60972b07b3412ffde1748")

    def test_source_metadata_is_exact_and_documentation_only(self):
        s = P["source"]
        self.assertEqual(s["dataset"], "euMTPL")
        self.assertEqual(s["upstream_commit"], "227fb56b8734bdb7c0327a41180e01d2ddaeaf26")
        self.assertEqual(s["upstream_path"], "data/euMTPL.rda")
        self.assertEqual(s["upstream_git_blob_sha"], "4bb386d89606eb5b529206d0835e11074103042b")
        self.assertEqual(s["upstream_blob_size_bytes"], 17829164)
        self.assertEqual(s["documentation_git_blob_sha"], "c50e96b2a4a470edb000fd71de0f2f01334799c7")
        known = s["known_from_public_documentation_before_row_level_access"]
        self.assertEqual(known["rows"], 2373197)
        self.assertEqual(known["columns"], 19)
        self.assertEqual(len(known["column_names"]), 19)
        self.assertEqual(known["documented_year_count"], 3)

    def test_no_row_level_access_is_allowed_in_v57(self):
        f = P["pre_access_firewall"]
        self.assertFalse(f["row_level_access_allowed_in_v57"])
        self.assertFalse(f["rda_download_allowed_in_v57"])
        self.assertFalse(f["rda_decode_allowed_in_v57"])
        self.assertFalse(f["outcome_summary_allowed_in_v57"])
        self.assertTrue(f["execution_allowed_only_after_preregistration_status_is_persisted_on_main"])
        self.assertFalse(Path("data/euMTPL.rda").exists())

    def test_temporal_split_is_chronological_and_outcome_free(self):
        s = P["temporal_split"]
        self.assertTrue(s["year_values_must_not_be_inspected_before_main_registration"])
        self.assertEqual(s["train"], "all rows in the earliest distinct year")
        self.assertEqual(s["calibration"], "all rows in the middle distinct year")
        self.assertEqual(s["locked_test"], "all rows in the latest distinct year")
        self.assertFalse(s["preexisting_group_column_used"])
        self.assertFalse(s["outcome_stratification"])
        self.assertFalse(s["random_resplitting"])
        self.assertFalse(s["resplitting_after_outcome_inspection_allowed"])

    def test_predictor_contract_excludes_identifiers_time_group_gender_and_outcomes(self):
        f = P["features"]
        self.assertEqual(f["numeric"], ["horsepower", "age"])
        self.assertEqual(f["categorical"], ["fuel_type", "vehicle_category", "vehicle_use", "province"])
        excluded = set(f["excluded_from_predictors"])
        required = {
            "policy_id", "year", "group", "gender", "exposure",
            "cost_nc", "num_nc", "cost_cg", "num_cg", "cost_cd", "num_cd", "cost_fcd", "num_fcd"
        }
        self.assertTrue(required.issubset(excluded))
        self.assertFalse(set(f["numeric"] + f["categorical"]) & required)

    def test_outcome_aggregation_is_frozen(self):
        t = P["targets"]
        self.assertEqual(t["frequency"]["observed_count"], "num_nc + num_cg + num_cd + num_fcd")
        self.assertEqual(t["pure_premium"]["observed_amount"], "cost_nc + cost_cg + cost_cd + cost_fcd")
        self.assertFalse(t["component_specific_model_selection_allowed"])
        self.assertFalse(t["post_result_target_redefinition_allowed"])

    def test_model_specs_match_v40_without_result_driven_tuning(self):
        for key in ("frequency_glm", "frequency_xgb", "pure_premium_glm", "pure_premium_xgb"):
            self.assertEqual(P["models"][key], V40["models"][key])
        self.assertFalse(P["models"]["hyperparameter_search_allowed"])
        self.assertFalse(P["models"]["early_stopping_allowed"])
        self.assertFalse(P["models"]["post_result_solver_or_parameter_change_allowed"])

    def test_gate_and_reproducibility_rules_are_not_weakened_from_v40(self):
        g = P["registered_external_temporal_gate"]
        old = V40["registered_external_replication_gate"]
        self.assertEqual(g["minimum_relative_deviance_improvement"], old["minimum_relative_deviance_improvement"])
        self.assertEqual(g["bootstrap_relative_improvement_ci_lower_bound_must_exceed"], old["bootstrap_relative_improvement_ci_lower_bound_must_exceed"])
        self.assertEqual(g["maximum_additional_abs_log_aggregate_calibration_error"], old["maximum_additional_abs_log_aggregate_calibration_error"])
        self.assertEqual(P["paired_bootstrap"]["draws"], 500)
        r = P["runtime_reproducibility"]
        self.assertEqual(r["minimum_independent_actions_executions_for_positive_external_support"], 2)
        self.assertEqual(r["point_metric_relative_tolerance"], V40["runtime_reproducibility"]["point_metric_relative_tolerance"])
        self.assertEqual(r["point_metric_absolute_tolerance"], V40["runtime_reproducibility"]["point_metric_absolute_tolerance"])

    def test_preregistration_does_not_clear_existing_governance_gates(self):
        d = P["decision_boundary"]
        self.assertFalse(d["preregistration_itself_changes_committee_machine_gate_count"])
        self.assertEqual(d["model_family_decision_after_v57"], "HOLD")
        self.assertEqual(d["serving_status_after_v57"], "HOLD_SHADOW_ONLY")
        self.assertEqual(d["promotion_review_status_after_v57"], "NOT_OPEN")
        self.assertFalse(d["future_positive_replication_can_directly_authorise_model_promotion"])
        self.assertFalse(d["future_positive_replication_can_directly_authorise_customer_pricing"])
        self.assertEqual(V56["committee_gate_pass_count"], 5)
        self.assertEqual(V56["committee_gate_count"], 8)

    def test_v57_workflow_is_no_data_by_construction(self):
        workflow = Path(".github/workflows/v57-eumtpl-temporal-prereg.yml").read_text(encoding="utf-8").lower()
        forbidden = ["pyreadr", "wget ", "curl ", "git clone", "data/eumtpl.rda", "download eumtpl"]
        for token in forbidden:
            self.assertNotIn(token, workflow)
        self.assertIn("validate_external_temporal_prereg_v57.py", workflow)
        self.assertIn("test_external_temporal_prereg_v57.py", workflow)


if __name__ == "__main__":
    unittest.main()
