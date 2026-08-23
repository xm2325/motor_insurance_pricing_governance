from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from governance.external_validation_firewall_v39 import (
    ALLOWED_CONSUMED_PURPOSES,
    FORBIDDEN_CONSUMED_PURPOSES,
    PREREGISTRATION_ONLY_PURPOSE,
    ExternalValidationFirewallError,
    assess_external_use,
    validate_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "governance" / "external_validation_use_ledger_v39.json"


class ExternalValidationFirewallV39Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))

    def test_registered_ledger_is_valid_and_traceable(self) -> None:
        validate_ledger(self.ledger)
        dataset = self.ledger["datasets"]["ausprivauto0405"]
        self.assertEqual(dataset["initial_role"], "INDEPENDENT_EXTERNAL_VALIDATION_FIRST_USE")
        self.assertEqual(dataset["current_role"], "CONSUMED_EXTERNAL_VALIDATION_DATASET")
        self.assertFalse(dataset["independent_external_validation_available"])
        self.assertFalse(dataset["candidate_selection_allowed"])
        self.assertEqual(dataset["locked_test_rows"], 13572)
        self.assertEqual([x["id"] for x in dataset["material_use_events"]], ["v0.36", "v0.37", "v0.38"])

    def test_consumed_australian_diagnostic_uses_are_allowed_but_never_independent(self) -> None:
        for purpose in ALLOWED_CONSUMED_PURPOSES:
            result = assess_external_use(self.ledger, dataset_id="ausprivauto0405", purpose=purpose)
            self.assertTrue(result["allowed"])
            self.assertEqual(result["evidence_class"], "CONSUMED_EXTERNAL_VALIDATION_REUSE")
            self.assertFalse(result["independent_confirmation"])
            self.assertFalse(result["candidate_selection_allowed"])
            self.assertFalse(result["promotion_authorised"])
            self.assertFalse(result["pricing_change_authorised"])

    def test_consumed_australian_candidate_and_promotion_uses_fail_closed(self) -> None:
        for purpose in FORBIDDEN_CONSUMED_PURPOSES:
            with self.assertRaises(ExternalValidationFirewallError):
                assess_external_use(self.ledger, dataset_id="ausprivauto0405", purpose=purpose)

    def test_unknown_use_on_consumed_dataset_fails_closed(self) -> None:
        with self.assertRaises(ExternalValidationFirewallError):
            assess_external_use(
                self.ledger,
                dataset_id="ausprivauto0405",
                purpose="new_unregistered_analysis",
            )

    def test_unknown_dataset_can_only_enter_as_preregistration_without_row_access(self) -> None:
        result = assess_external_use(
            self.ledger,
            dataset_id="future_external_motor_dataset",
            purpose=PREREGISTRATION_ONLY_PURPOSE,
        )
        self.assertTrue(result["allowed"])
        self.assertEqual(result["evidence_class"], "UNSEEN_EXTERNAL_PREREGISTRATION_ONLY")
        self.assertFalse(result["row_level_access_allowed"])
        self.assertFalse(result["independent_confirmation"])
        self.assertFalse(result["promotion_authorised"])
        self.assertEqual(result["next_required_state"], "REGISTER_PROTOCOL_ON_MAIN_BEFORE_ROW_LEVEL_ACCESS")

    def test_unknown_dataset_row_level_or_analysis_use_fails_before_registration(self) -> None:
        with self.assertRaises(ExternalValidationFirewallError):
            assess_external_use(
                self.ledger,
                dataset_id="future_external_motor_dataset",
                purpose="independent_confirmation",
            )

    def test_consumed_dataset_cannot_regain_independence_by_flag_edit(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["datasets"]["ausprivauto0405"]["independent_external_validation_available"] = True
        with self.assertRaises(ExternalValidationFirewallError):
            validate_ledger(mutated)

    def test_consumed_dataset_cannot_reenable_candidate_selection(self) -> None:
        mutated = copy.deepcopy(self.ledger)
        mutated["datasets"]["ausprivauto0405"]["candidate_selection_allowed"] = True
        with self.assertRaises(ExternalValidationFirewallError):
            validate_ledger(mutated)

    def test_external_history_cannot_drop_v37_or_v38(self) -> None:
        for missing in ("v0.37", "v0.38"):
            mutated = copy.deepcopy(self.ledger)
            mutated["datasets"]["ausprivauto0405"]["material_use_events"] = [
                event
                for event in mutated["datasets"]["ausprivauto0405"]["material_use_events"]
                if event["id"] != missing
            ]
            with self.assertRaises(ExternalValidationFirewallError):
                validate_ledger(mutated)

    def test_future_positive_external_evidence_inherits_v38_reproducibility_gate(self) -> None:
        firewall = self.ledger["new_external_dataset_firewall"]
        self.assertTrue(firewall["row_level_access_requires_registered_dataset"])
        self.assertEqual(firewall["minimum_independent_actions_executions_for_positive_external_support"], 2)
        self.assertTrue(firewall["positive_external_support_requires_matching_decisions"])
        self.assertTrue(firewall["positive_external_support_requires_registered_metric_reproducibility"])
        self.assertTrue(firewall["iterative_estimators_require_registered_solver_and_tolerance"])
        self.assertEqual(firewall["default_thread_environment"], {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        })

    def test_governance_remains_hold_shadow_only(self) -> None:
        decision = self.ledger["decision"]
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])


if __name__ == "__main__":
    unittest.main()
