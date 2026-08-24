import json
import unittest
from pathlib import Path

P = json.loads(Path("governance/external_temporal_prereg_v57.json").read_text(encoding="utf-8"))
LOCK = json.loads(Path("action_results/v57/eumtpl_external_temporal_prereg_lock.json").read_text(encoding="utf-8"))
STATUS = json.loads(Path("action_results/v57/ACTION_V57_STATUS.json").read_text(encoding="utf-8"))


class EumtplExternalTemporalV58Tests(unittest.TestCase):
    def test_v57_main_lock_preceded_first_decode(self):
        self.assertEqual(LOCK["protocol_sha256"], "a2b49e26aeca619323129ee4b56ff39d110cf68a08bfe0064fbd3f5886f74ff5")
        self.assertEqual(STATUS["sha"], "cacb55a039c6132b7c2466f6356903250dc624d3")
        self.assertEqual(STATUS["status"], "success")
        self.assertFalse(STATUS["row_level_external_data_accessed"])
        self.assertFalse(STATUS["outcomes_inspected"])

    def test_source_binary_identity_remains_exactly_pinned(self):
        s = P["source"]
        self.assertEqual(s["upstream_commit"], "227fb56b8734bdb7c0327a41180e01d2ddaeaf26")
        self.assertEqual(s["upstream_git_blob_sha"], "4bb386d89606eb5b529206d0835e11074103042b")
        self.assertEqual(s["upstream_blob_size_bytes"], 17829164)
        downloader = Path("download_eumtpl_motor_v58.py").read_text(encoding="utf-8")
        self.assertIn("git_blob_sha1", downloader)
        self.assertNotIn("pyreadr", downloader)

    def test_registered_schema_is_not_silently_amended(self):
        c = P["data_contract_for_future_execution"]
        self.assertIn("cost_fcd", c["required_columns_exactly"])
        self.assertIn("num_fcd", c["required_columns_exactly"])
        self.assertNotIn("cost_fcg", c["required_columns_exactly"])
        self.assertNotIn("num_fcg", c["required_columns_exactly"])
        incident = Path("record_eumtpl_schema_contract_incident_v58.py").read_text(encoding="utf-8")
        self.assertIn('"cost_fcd", "num_fcd"', incident)
        self.assertIn('"cost_fcg", "num_fcg"', incident)
        self.assertNotIn("rename(", incident)
        self.assertNotIn("columns = registered_columns", incident)

    def test_incident_recorder_does_not_inspect_outcome_or_year_values(self):
        incident = Path("record_eumtpl_schema_contract_incident_v58.py").read_text(encoding="utf-8")
        self.assertNotIn(".sum(", incident)
        self.assertNotIn(".mean(", incident)
        self.assertNotIn("groupby(", incident)
        self.assertNotIn("unique(", incident)
        self.assertNotIn("PoissonRegressor", incident)
        self.assertNotIn("XGBRegressor", incident)
        self.assertNotIn("TweedieRegressor", incident)

    def test_model_execution_is_removed_from_active_workflow(self):
        workflow = Path(".github/workflows/v58-eumtpl-temporal-execution.yml").read_text(encoding="utf-8")
        self.assertNotIn("run_eumtpl_external_temporal_replication_v58.py", workflow)
        self.assertIn("record_eumtpl_schema_contract_incident_v58.py", workflow)
        self.assertNotIn("frequency_relative_improvement", workflow)
        self.assertNotIn("pure_premium_relative_improvement", workflow)

    def test_raw_external_data_can_never_be_persisted(self):
        workflow = Path(".github/workflows/v58-eumtpl-temporal-execution.yml").read_text(encoding="utf-8")
        self.assertIn("Assert raw euMTPL data are not staged", workflow)
        self.assertNotIn("git add -- data_external_v58", workflow)
        self.assertNotIn("cp data_external_v58", workflow)

    def test_mismatch_makes_dataset_ineligible_for_fresh_confirmatory_claim(self):
        incident = Path("record_eumtpl_schema_contract_incident_v58.py").read_text(encoding="utf-8")
        self.assertIn('"euMTPL_still_eligible_as_fresh_confirmatory_dataset": False', incident)
        self.assertIn('"confirmatory_external_temporal_evidence_created": False', incident)
        self.assertIn('"post_access_schema_amendment_used_for_confirmatory_claim": False', incident)

    def test_no_gate_or_committee_credit_is_created(self):
        incident = Path("record_eumtpl_schema_contract_incident_v58.py").read_text(encoding="utf-8")
        self.assertIn('"committee_gate_pass_count": 5', incident)
        self.assertIn('"committee_gate_count": 8', incident)
        self.assertIn('"model_family_decision": "HOLD"', incident)
        self.assertIn('"serving_status": "HOLD_SHADOW_ONLY"', incident)
        self.assertIn('"promotion_review_status": "NOT_OPEN"', incident)

    def test_original_model_and_gate_preregistration_is_retained_unchanged(self):
        self.assertFalse(P["models"]["hyperparameter_search_allowed"])
        self.assertFalse(P["models"]["post_result_solver_or_parameter_change_allowed"])
        self.assertEqual(P["registered_external_temporal_gate"]["minimum_relative_deviance_improvement"], 0.005)
        self.assertEqual(P["paired_bootstrap"]["draws"], 500)

    def test_incident_status_is_explicitly_fail_closed(self):
        incident = Path("record_eumtpl_schema_contract_incident_v58.py").read_text(encoding="utf-8")
        self.assertIn("V58_FAIL_CLOSED_SOURCE_SCHEMA_PREREGISTRATION_MISMATCH", incident)
        self.assertIn('"model_fit_executed": False', incident)
        self.assertIn('"locked_test_performance_metrics_computed": False', incident)
        self.assertIn('"registered_gate_evaluated": False', incident)


if __name__ == "__main__":
    unittest.main()
