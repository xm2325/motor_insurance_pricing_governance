import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "governance" / "prospective_request_registration_v61.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "v61-prospective-source-registration.yml"
VALIDATOR_PATH = ROOT / "validate_prospective_request_registration_v61.py"

spec = importlib.util.spec_from_file_location("v61_validator", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)


class ProspectiveRequestRegistrationV61Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(PROTOCOL_PATH.read_text())

    def test_validator_accepts_locked_registration(self):
        summary = validator.validate(self.protocol)
        self.assertEqual(summary["status"], "V61_PROSPECTIVE_THREE_SOURCE_REGISTRATION_LOCK_PASS")
        self.assertEqual(summary["source_identity_count"], 3)
        self.assertTrue(summary["source_identities_pairwise_distinct"])

    def test_historical_request_remains_terminal_hold(self):
        inherited = self.protocol["inherits"]
        self.assertEqual(inherited["historical_request"], "MCR-XGB-MOTOR-001")
        self.assertEqual(inherited["historical_request_state"], "STRUCTURALLY_BLOCKED_MAX_7_OF_8")
        self.assertEqual((inherited["historical_committee_gate_pass_count"], inherited["historical_committee_gate_count"]), (5, 8))
        self.assertEqual(inherited["historical_model_family_decision"], "HOLD")
        self.assertTrue(inherited["historical_request_is_not_modified_by_v61"])

    def test_global_two_target_scope_is_fixed_before_access(self):
        activation = self.protocol["activation"]
        self.assertEqual(activation["programme_scope"], "GLOBAL_TWO_TARGET")
        self.assertTrue(activation["frequency_required"])
        self.assertTrue(activation["pure_premium_required"])
        self.assertTrue(activation["targets_may_not_compensate_for_each_other"])

    def test_three_underlying_sources_are_atomic_and_pairwise_distinct(self):
        sources = self.protocol["sources"]
        ids = [sources[k]["underlying_source_identity"] for k in self.protocol["activation"]["stage_sequence"]]
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(set(ids)), 3)
        self.assertTrue(self.protocol["activation"]["three_source_identities_registered_atomically"])
        self.assertTrue(sources["S3_SEALED_CONFIRMATION"]["five_files_form_one_underlying_source_identity"])
        self.assertEqual(len(sources["S3_SEALED_CONFIRMATION"]["rda_files"]), 5)

    def test_s1_temporal_and_cross_year_leakage_rules_are_pre_outcome(self):
        s1 = self.protocol["sources"]["S1_TEMPORAL_QUALIFICATION"]
        self.assertEqual(s1["time_contract"]["required_calendar_year_set"], [2009, 2010])
        self.assertEqual(s1["time_contract"]["development_year"], 2009)
        self.assertEqual(s1["time_contract"]["locked_temporal_test_year"], 2010)
        self.assertEqual(s1["pre_outcome_leakage_control"]["allowed_fields_before_outcome_access_after_schema_validation"], ["PolNum", "CalYear"])
        self.assertTrue(s1["pre_outcome_leakage_control"]["observed_cross_year_count_is_descriptive_not_a_tuning_or_validity_target"])
        split = s1["time_contract"]["train_calibration_split"]
        self.assertEqual(split["hash"], "SHA256")
        self.assertEqual(split["salt"], "v61|S1|20260825|")
        self.assertTrue(split["no_outcome_stratification"])
        self.assertTrue(split["no_resplit_after_access"])

    def test_s2_and_s3_cannot_open_at_registration(self):
        sources = self.protocol["sources"]
        self.assertFalse(sources["S2_EXTERNAL_REPLICATION"]["may_open_at_v61"])
        self.assertFalse(sources["S3_SEALED_CONFIRMATION"]["may_open_at_v61"])
        self.assertTrue(sources["S3_SEALED_CONFIRMATION"]["sealed_at_v61"])
        activation = self.protocol["activation"]
        self.assertTrue(activation["s2_may_open_only_after_reproducible_s1_pass"])
        self.assertTrue(activation["s3_may_open_only_after_reproducible_s1_and_s2_pass"])
        self.assertTrue(activation["reserve_cannot_rescue_s1_or_s2_failure"])

    def test_schema_names_are_locked_but_document_order_and_counts_are_not_identity_gates(self):
        rules = self.protocol["source_identity_rules"]
        self.assertEqual(rules["schema_contract"], "REQUIRED_COLUMN_NAME_SET_AND_SEMANTICS_NOT_COLUMN_ORDER")
        self.assertTrue(rules["column_order_is_not_identity_or_schema_gate"])
        self.assertTrue(rules["public_row_counts_are_provenance_expectations_not_binary_identity_gates"])
        self.assertIn("Numtppd", self.protocol["sources"]["S1_TEMPORAL_QUALIFICATION"]["required_columns"])
        self.assertIn("ClaimNb", self.protocol["sources"]["S2_EXTERNAL_REPLICATION"]["required_columns"])
        self.assertIn("ClaimAmountUnknown", self.protocol["sources"]["S3_SEALED_CONFIRMATION"]["required_columns"])

    def test_model_gates_and_positive_reproducibility_are_frozen(self):
        model = self.protocol["registered_model_family"]
        self.assertEqual(model["frequency_reference"]["solver"], "newton-cholesky")
        self.assertEqual(model["pure_premium_reference"]["solver"], "newton-cholesky")
        self.assertEqual(model["frequency_challenger"]["n_jobs"], 1)
        self.assertEqual(model["pure_premium_challenger"]["n_jobs"], 1)
        self.assertFalse(model["hyperparameter_search"])
        self.assertFalse(model["early_stopping"])
        self.assertEqual(self.protocol["target_gate"]["point_relative_deviance_improvement_min"], 0.005)
        self.assertEqual(self.protocol["target_gate"]["challenger_absolute_log_calibration_error_must_be_lte_reference_plus"], 0.01)
        self.assertTrue(self.protocol["stage_gate"]["positive_stage_requires_two_independent_github_actions_executions"])
        self.assertEqual(self.protocol["stage_gate"]["point_metric_relative_reproducibility_tolerance_max"], 0.001)

    def test_registration_has_zero_new_row_or_outcome_access(self):
        state = self.protocol["v61_access_state"]
        for key in ["new_rda_downloaded", "new_rda_decoded", "row_level_new_source_accessed", "new_outcome_values_accessed", "model_fit_executed", "performance_metrics_computed", "s1_open", "s2_open", "s3_open"]:
            self.assertFalse(state[key], key)
        self.assertTrue(state["s3_reserve_sealed"])

    def test_v61_workflow_is_metadata_only(self):
        text = WORKFLOW_PATH.read_text()
        lowered = text.lower()
        forbidden = [
            "curl ", "wget ", "git clone", "py" + "readr", "rdata", "raw.githubusercontent.com/dutangc/casdatasets",
            "pip install pandas", "pip install scikit", "pip install xgboost", ".fit(",
        ]
        for token in forbidden:
            self.assertNotIn(token, lowered, token)
        self.assertIn("validate_prospective_request_registration_v61.py", text)
        self.assertIn("test_prospective_request_registration_v61.py", text)

    def test_governance_boundary_forbids_promotion_and_pricing(self):
        boundary = self.protocol["governance_boundary"]
        self.assertTrue(boundary["this_registration_is_not_validation_evidence"])
        self.assertTrue(boundary["this_registration_is_not_model_performance_evidence"])
        self.assertTrue(boundary["this_registration_is_not_UK_or_First_Central_transport_evidence"])
        self.assertTrue(boundary["this_registration_does_not_authorise_promotion"])
        self.assertTrue(boundary["this_registration_does_not_authorise_customer_pricing"])


if __name__ == "__main__":
    unittest.main()
