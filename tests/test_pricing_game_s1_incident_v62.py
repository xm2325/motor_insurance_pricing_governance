import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = json.loads((ROOT / "governance/prospective_request_registration_v61.json").read_text())
RECORDER = (ROOT / "record_pricing_game_s1_schema_incident_v62.py").read_text()
WORKFLOW = (ROOT / ".github/workflows/v62-pricing-game-s1-temporal.yml").read_text()
RESULTS = (ROOT / "RESULTS_V62.md").read_text()


class PricingGameS1IncidentV62Tests(unittest.TestCase):
    def test_registered_schema_is_not_amended_after_access(self):
        s1 = REG["sources"]["S1_TEMPORAL_QUALIFICATION"]
        self.assertIn("Expdays", s1["required_columns"])
        self.assertNotIn("Exppdays", s1["required_columns"])
        self.assertEqual(s1["exposure"]["source_field"], "Expdays")
        self.assertIn('registered_only != ["Expdays"]', RECORDER)
        self.assertIn('decoded_only != ["Exppdays"]', RECORDER)

    def test_v61_source_incident_rules_make_s1_terminal(self):
        a = REG["activation"]
        self.assertTrue(a["failed_or_source_contract_incident_consumes_stage"])
        self.assertTrue(a["source_substitution_after_stage_access_forbidden"])
        self.assertTrue(a["reserve_cannot_rescue_s1_or_s2_failure"])
        self.assertTrue(a["s2_may_open_only_after_reproducible_s1_pass"])
        self.assertTrue(a["s3_may_open_only_after_reproducible_s1_and_s2_pass"])

    def test_incident_recorder_stops_at_schema_names(self):
        forbidden_value_reads = [
            'frame["PolNum"]', 'frame["CalYear"]', 'frame["Expdays"]',
            'frame["Exppdays"]', 'frame["Numtppd"]', 'frame["Numtpbi"]',
            'frame["Indtppd"]', 'frame["Indtpbi"]',
        ]
        for needle in forbidden_value_reads:
            self.assertNotIn(needle, RECORDER)
        self.assertNotIn(".fit(", RECORDER)
        self.assertNotIn("mean_poisson_deviance", RECORDER)
        self.assertNotIn("mean_tweedie_deviance", RECORDER)
        self.assertNotIn("len(frame)", RECORDER)

    def test_active_workflow_records_incident_not_model_execution(self):
        self.assertIn("Record fail-closed S1 semantic schema incident", WORKFLOW)
        self.assertIn("record_pricing_game_s1_schema_incident_v62.py", WORKFLOW)
        self.assertNotIn("run: python run_pricing_game_s1_temporal_v62.py", WORKFLOW)
        self.assertIn("S2/S3 remain sealed", WORKFLOW)

    def test_incident_boundary_is_documented_without_model_claim(self):
        self.assertIn("TERMINAL_S1_SOURCE_CONTRACT_INCIDENT", RESULTS)
        self.assertIn("model fit/calibration: **no**", RESULTS)
        self.assertIn("performance metrics/bootstrap/gates: **no**", RESULTS)
        self.assertIn("S2 (`swmotorcycle`) and S3 (`brvehins1`) remain sealed", RESULTS)
        self.assertIn("customer pricing unauthorised", RESULTS)

    def test_historical_governance_is_not_upgraded(self):
        self.assertIn('"historical_committee_gate_pass_count": 5', RECORDER)
        self.assertIn('"historical_committee_gate_count": 8', RECORDER)
        self.assertIn('"historical_model_family_decision": "HOLD"', RECORDER)
        self.assertIn('"historical_serving_status": "HOLD_SHADOW_ONLY"', RECORDER)
        self.assertIn('"historical_promotion_review_status": "NOT_OPEN"', RECORDER)
        self.assertIn('"customer_pricing_authorised": False', RECORDER)


if __name__ == "__main__":
    unittest.main()
