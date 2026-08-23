from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "action_results" / "v35"
SUMMARY = RESULT_DIR / "validation_firewall_summary.json"
STATUS = RESULT_DIR / "ACTION_V35_STATUS.json"
LEDGER = ROOT / "governance" / "validation_use_ledger_v35.json"
README = ROOT / "README.md"


class ValidationFirewallEvidenceV35Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER.read_text(encoding="utf-8"))

    def test_main_workflow_status_is_success(self) -> None:
        self.assertEqual(self.status["workflow"], "Validation reuse firewall v0.35")
        self.assertEqual(self.status["run_id"], "32632841661")
        self.assertEqual(
            self.status["sha"],
            "3ad7019eeb367cff6765af7b648887c4b66c73cc",
        )
        self.assertEqual(self.status["status"], "success")

    def test_2024_is_persisted_as_consumed_validation(self) -> None:
        self.assertEqual(self.summary["status"], "V35_VALIDATION_FIREWALL_PASS")
        period = self.summary["2024"]
        self.assertEqual(period["initial_role"], "LOCKED_OOT_FIRST_USE")
        self.assertEqual(period["current_role"], "CONSUMED_RETROSPECTIVE_VALIDATION")
        self.assertFalse(period["independent_holdout_available"])
        self.assertFalse(period["candidate_selection_allowed"])
        self.assertEqual(period["promotion_evidence_class"], "REUSED_HISTORICAL_VALIDATION")
        self.assertEqual(period["material_reuse_event_count"], 7)
        self.assertEqual(period["post_first_use_reuse_event_count"], 6)
        self.assertEqual(period["label_using_event_count"], 5)
        self.assertEqual(
            period["registered_event_ids"],
            ["initial_locked_oot", "v0.22", "v0.23", "v0.31", "v0.32", "v0.33", "v0.34"],
        )

    def test_future_2024_use_boundary_is_exact(self) -> None:
        firewall = self.summary["firewall"]
        self.assertEqual(firewall["status"], "BLOCK_NEW_PROMOTION_FROM_2024_REUSE")
        self.assertTrue(firewall["requires_new_independent_period_or_external_validation"])
        self.assertEqual(
            set(firewall["allowed_future_2024_purposes"]),
            {"regression_reproduction", "monitoring_replay", "post_hoc_diagnostics", "governance_contract_testing"},
        )
        self.assertEqual(
            set(firewall["forbidden_future_2024_purposes"]),
            {
                "fit_new_model_parameters",
                "fit_new_calibration_parameters",
                "select_new_candidate_policy",
                "independent_confirmation",
                "authorise_model_family_promotion",
                "authorise_customer_pricing",
            },
        )
        self.assertIn("genuinely new independent calendar period or external validation dataset", firewall["next_promotion_evidence_requirement"])

    def test_ledger_and_persisted_summary_agree(self) -> None:
        ledger_period = self.ledger["periods"]["2024"]
        summary_period = self.summary["2024"]
        self.assertEqual(ledger_period["initial_role"], summary_period["initial_role"])
        self.assertEqual(ledger_period["current_role"], summary_period["current_role"])
        self.assertEqual(ledger_period["independent_holdout_available"], summary_period["independent_holdout_available"])
        self.assertEqual(ledger_period["candidate_selection_allowed"], summary_period["candidate_selection_allowed"])
        self.assertEqual(len(ledger_period["material_reuse_events"]), summary_period["material_reuse_event_count"])

    def test_readme_no_longer_claims_current_untouched_holdout(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("2024 untouched at first locked OOT evaluation", readme)
        self.assertIn("CONSUMED_RETROSPECTIVE_VALIDATION", readme)
        self.assertNotIn("2024 untouched OOT**", readme)

    def test_governance_remains_hold_shadow_only(self) -> None:
        decision = self.summary["decision"]
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])


if __name__ == "__main__":
    unittest.main()
