import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "governance" / "source_contract_qualification_policy_v63.json"
RUNNER_PATH = ROOT / "run_source_contract_qualification_v63.py"
EXECUTOR_PATH = ROOT / "execute_source_contract_qualification_v63.py"
V58_STATUS = ROOT / "action_results" / "v58" / "ACTION_V58_STATUS.json"
V62_STATUS = ROOT / "action_results" / "v62" / "ACTION_V62_STATUS.json"

spec = importlib.util.spec_from_file_location("v63_runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(runner)


class SourceContractQualificationV63Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads(POLICY_PATH.read_text())
        cls.runner_text = RUNNER_PATH.read_text()
        cls.executor_text = EXECUTOR_PATH.read_text()
        cls.v58 = json.loads(V58_STATUS.read_text())
        cls.v62 = json.loads(V62_STATUS.read_text())

    def test_q0_is_required_before_future_seal(self):
        q0 = self.policy["qualification_stage"]
        self.assertEqual(q0["name"], "Q0_SOURCE_CONTRACT_QUALIFICATION")
        self.assertTrue(q0["must_complete_before_new_change_request_or_source_stage_is_sealed"])
        self.assertIn("pyreadr.list_objects_for_object_names_and_column_names_only", q0["allowed_operations"])
        self.assertIn("pyreadr.read_r", q0["forbidden_operations"])

    def test_runner_uses_schema_metadata_not_value_decode(self):
        self.assertIn("pyreadr.list_objects(", self.runner_text)
        self.assertNotIn("pyreadr.read_r(", self.runner_text)
        self.assertNotIn(".fit(", self.runner_text)
        self.assertNotIn("mean_poisson_deviance", self.runner_text)
        self.assertNotIn("mean_tweedie_deviance", self.runner_text)
        self.assertIn('Path("/tmp/source_qualification_v63")', self.runner_text)

    def test_metadata_patch_is_narrow_noop_row_name_handler(self):
        self.assertIn("ListObjectsParser", self.executor_text)
        self.assertIn("def _discard_row_name(self, name, index):", self.executor_text)
        self.assertIn("return None", self.executor_text)
        self.assertNotIn("pyreadr.read_r(", self.executor_text)
        self.assertNotIn("handle_column =", self.executor_text)
        self.assertNotIn("handle_text_value =", self.executor_text)
        self.assertIn('"column_values_callback_added": False', self.executor_text)
        self.assertIn('"row_names_persisted": False', self.executor_text)
        self.assertIn('"value_decode_api_used": False', self.executor_text)

    def test_near_match_is_review_only_never_alias(self):
        self.assertEqual(runner.levenshtein("Expdays", "Exppdays"), 1)
        self.assertEqual(runner.levenshtein("cost_fcd", "cost_fcg"), 1)
        self.assertFalse(self.policy["binary_schema_gate"]["automatic_aliasing"])
        self.assertTrue(self.policy["near_match_rule"]["near_match_never_auto_corrects"])

    def test_column_order_and_row_counts_are_not_schema_identity_gates(self):
        self.assertTrue(self.policy["binary_schema_gate"]["column_order_is_not_a_gate"])
        self.assertTrue(self.policy["documentation_gate"]["documentation_row_counts_are_not_binary_identity_gates"])

    def test_historical_incidents_remain_terminal(self):
        self.assertEqual(self.v58["incident_status"], "V58_FAIL_CLOSED_SOURCE_SCHEMA_PREREGISTRATION_MISMATCH")
        self.assertFalse(self.v58["eumtpl_fresh_confirmatory_eligible"])
        self.assertEqual(self.v62["request_state"], "TERMINAL_S1_SOURCE_CONTRACT_INCIDENT")
        self.assertTrue(self.v62["s1_stage_consumed"])
        self.assertFalse(self.v62["s2_open_authorised"])
        self.assertFalse(self.v62["s3_open_authorised"])

    def test_v63_does_not_create_request_or_model_authority(self):
        g = self.policy["historical_governance_boundary"]
        self.assertFalse(g["v63_creates_new_change_request"])
        self.assertFalse(g["v63_opens_new_fresh_source"])
        self.assertFalse(g["v63_creates_model_performance_evidence"])
        self.assertEqual(g["historical_committee_gate_pass_count"], 5)
        self.assertEqual(g["historical_committee_gate_count"], 8)
        self.assertEqual(g["historical_model_family_decision"], "HOLD")
        self.assertFalse(g["customer_pricing_authorised"])


if __name__ == "__main__":
    unittest.main()
