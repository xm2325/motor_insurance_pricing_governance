from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from governance.validation_firewall import (
    ALLOWED_REUSED_2024_PURPOSES,
    FORBIDDEN_REUSED_2024_PURPOSES,
    ValidationFirewallError,
    assess_proposed_use,
    validate_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "governance" / "validation_use_ledger_v35.json"


class ValidationFirewallV35Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    def test_registered_ledger_is_valid_and_traceable(self) -> None:
        validate_ledger(self.ledger)
        period = self.ledger["periods"]["2024"]
        self.assertEqual(period["initial_role"], "LOCKED_OOT_FIRST_USE")
        self.assertEqual(period["current_role"], "CONSUMED_RETROSPECTIVE_VALIDATION")
        self.assertFalse(period["independent_holdout_available"])
        self.assertFalse(period["candidate_selection_allowed"])
        events = period["material_reuse_events"]
        self.assertEqual(len(events), 7)
        self.assertTrue(events[0]["independent_at_time_of_use"])
        self.assertTrue(all(not event["independent_at_time_of_use"] for event in events[1:]))
        for event in events:
            self.assertTrue((ROOT / event["source"]).is_file(), event["source"])

    def test_future_2024_diagnostic_uses_are_allowed_but_not_independent(self) -> None:
        for purpose in ALLOWED_REUSED_2024_PURPOSES:
            decision = assess_proposed_use(self.ledger, year=2024, purpose=purpose)
            self.assertTrue(decision["allowed"])
            self.assertEqual(decision["evidence_class"], "REUSED_HISTORICAL_VALIDATION")
            self.assertFalse(decision["independent_confirmation"])
            self.assertFalse(decision["promotion_authorised"])

    def test_candidate_selection_and_promotion_uses_fail_closed(self) -> None:
        for purpose in FORBIDDEN_REUSED_2024_PURPOSES:
            with self.assertRaises(ValidationFirewallError):
                assess_proposed_use(self.ledger, year=2024, purpose=purpose)

    def test_unknown_2024_use_fails_closed(self) -> None:
        with self.assertRaises(ValidationFirewallError):
            assess_proposed_use(self.ledger, year=2024, purpose="new_unregistered_analysis")

    def test_cannot_restore_2024_independence_by_editing_flag(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["periods"]["2024"]["independent_holdout_available"] = True
        with self.assertRaises(ValidationFirewallError):
            validate_ledger(mutated)

    def test_cannot_reenable_2024_candidate_selection(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["periods"]["2024"]["candidate_selection_allowed"] = True
        with self.assertRaises(ValidationFirewallError):
            validate_ledger(mutated)

    def test_material_reuse_history_cannot_drop_v034(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["periods"]["2024"]["material_reuse_events"] = [
            event
            for event in mutated["periods"]["2024"]["material_reuse_events"]
            if event["id"] != "v0.34"
        ]
        with self.assertRaises(ValidationFirewallError):
            validate_ledger(mutated)

    def test_new_independent_data_is_required_for_promotion(self) -> None:
        firewall = self.ledger["promotion_firewall"]
        self.assertEqual(firewall["status"], "BLOCK_NEW_PROMOTION_FROM_2024_REUSE")
        self.assertTrue(firewall["requires_new_independent_period_or_external_validation"])
        self.assertEqual(firewall["model_family_decision"], "HOLD")
        self.assertEqual(firewall["serving_status"], "HOLD_SHADOW_ONLY")


if __name__ == "__main__":
    unittest.main()
