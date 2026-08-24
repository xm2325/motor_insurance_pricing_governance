import json
import unittest
from pathlib import Path

P = json.loads(Path("governance/external_temporal_prereg_v57.json").read_text(encoding="utf-8"))
LOCK = json.loads(Path("action_results/v57/eumtpl_external_temporal_prereg_lock.json").read_text(encoding="utf-8"))
STATUS = json.loads(Path("action_results/v57/ACTION_V57_STATUS.json").read_text(encoding="utf-8"))


class EumtplExternalTemporalV58Tests(unittest.TestCase):
    def test_v57_main_lock_exists_before_v58_data_access(self):
        self.assertEqual(LOCK["protocol_sha256"], "a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5")
        self.assertEqual(STATUS["sha"], "cacb55a039c6132b7c2466f6356903250dc624d3")
        self.assertEqual(STATUS["status"], "success")
        self.assertFalse(STATUS["row_level_external_data_accessed"])
        self.assertFalse(STATUS["outcomes_inspected"])
        self.assertTrue(STATUS["future_row_level_execution_allowed_only_in_v58_or_later"])

    def test_source_identity_is_pinned_before_download(self):
        s = P["source"]
        self.assertEqual(s["upstream_commit"], "227fb56b8734bdb7c0327a41180e01d2ddaeaf26")
        self.assertEqual(s["upstream_git_blob_sha"], "4bb386d89606eb5b529206d0835e11074103042b")
        self.assertEqual(s["upstream_blob_size_bytes"], 17829164)
        downloader = Path("download_eumtpl_motor_v58.py").read_text(encoding="utf-8")
        self.assertIn("git_blob_sha1", downloader)
        self.assertIn("upstream_git_blob_sha", downloader)
        self.assertIn("upstream_blob_size_bytes", downloader)
        self.assertNotIn("pyreadr", downloader)

    def test_future_schema_contract_is_exact(self):
        c = P["data_contract_for_future_execution"]
        self.assertEqual(c["required_rows"], 2373197)
        self.assertEqual(len(c["required_columns_exactly"]), 19)
        self.assertTrue(c["require_exactly_three_distinct_years"])
        self.assertTrue(c["policy_id_overlap_audit_required"])
        self.assertTrue(c["policy_id_overlap_across_years_does_not_change_split_or_filter_rows"])
        self.assertTrue(c["no_post_download_row_filtering"])

    def test_temporal_split_is_not_source_group_or_random(self):
        s = P["temporal_split"]
        self.assertEqual(s["train"], "all rows in the earliest distinct year")
        self.assertEqual(s["calibration"], "all rows in the middle distinct year")
        self.assertEqual(s["locked_test"], "all rows in the latest distinct year")
        self.assertFalse(s["preexisting_group_column_used"])
        self.assertFalse(s["random_resplitting"])
        self.assertFalse(s["outcome_stratification"])
        runner = Path("run_eumtpl_external_temporal_replication_v58.py").read_text(encoding="utf-8")
        self.assertIn('"train": year_int == years[0]', runner)
        self.assertIn('"calibration": year_int == years[1]', runner)
        self.assertIn('"test": year_int == years[2]', runner)
        self.assertNotIn("deterministic_split_indices", runner)

    def test_registered_aggregate_targets_are_implemented_exactly(self):
        self.assertEqual(P["targets"]["frequency"]["observed_count"], "num_nc + num_cg + num_cd + num_fcd")
        self.assertEqual(P["targets"]["pure_premium"]["observed_amount"], "cost_nc + cost_cg + cost_cd + cost_fcd")
        runner = Path("run_eumtpl_external_temporal_replication_v58.py").read_text(encoding="utf-8")
        self.assertIn('claim_count_components', runner)
        self.assertIn('claim_cost_components', runner)

    def test_feature_contract_excludes_time_group_ids_gender_and_outcomes(self):
        f = P["features"]
        self.assertEqual(f["numeric"], ["horsepower", "age"])
        self.assertEqual(f["categorical"], ["fuel_type", "vehicle_category", "vehicle_use", "province"])
        forbidden = {"policy_id", "year", "group", "gender", "exposure", "num_nc", "cost_nc", "num_cg", "cost_cg", "num_cd", "cost_cd", "num_fcd", "cost_fcd"}
        self.assertFalse(forbidden & set(f["numeric"] + f["categorical"]))

    def test_no_model_or_gate_change_is_introduced_in_v58(self):
        self.assertFalse(P["models"]["hyperparameter_search_allowed"])
        self.assertFalse(P["models"]["early_stopping_allowed"])
        self.assertFalse(P["models"]["post_result_solver_or_parameter_change_allowed"])
        self.assertEqual(P["models"]["frequency_glm"]["solver"], "newton-cholesky")
        self.assertEqual(P["models"]["pure_premium_glm"]["solver"], "newton-cholesky")
        self.assertEqual(P["registered_external_temporal_gate"]["minimum_relative_deviance_improvement"], 0.005)
        self.assertEqual(P["registered_external_temporal_gate"]["bootstrap_relative_improvement_ci_lower_bound_must_exceed"], 0.0)
        self.assertEqual(P["registered_external_temporal_gate"]["maximum_additional_abs_log_aggregate_calibration_error"], 0.01)
        self.assertEqual(P["paired_bootstrap"]["draws"], 500)

    def test_positive_support_requires_two_independent_executions(self):
        r = P["runtime_reproducibility"]
        self.assertEqual(r["minimum_independent_actions_executions_for_positive_external_support"], 2)
        self.assertTrue(r["positive_external_support_requires_matching_registered_decisions"])
        self.assertTrue(r["positive_external_support_requires_registered_point_metric_reproducibility"])

    def test_raw_external_data_can_never_be_persisted(self):
        workflow = Path(".github/workflows/v58-eumtpl-temporal-execution.yml").read_text(encoding="utf-8")
        self.assertIn("Assert raw euMTPL data are not staged", workflow)
        self.assertNotIn("git add -- data_external_v58", workflow)
        self.assertNotIn("cp data_external_v58", workflow)

    def test_governance_remains_hold_for_first_execution(self):
        runner = Path("run_eumtpl_external_temporal_replication_v58.py").read_text(encoding="utf-8")
        self.assertIn('"model_family_decision": "HOLD"', runner)
        self.assertIn('"serving_status": "HOLD_SHADOW_ONLY"', runner)
        self.assertIn('"promotion_review_status": "NOT_OPEN"', runner)
        self.assertIn('"positive_external_support_authorised": False', runner)


if __name__ == "__main__":
    unittest.main()
