import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ModelRiskInventoryV46Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(
            (ROOT / "results_v46/model_risk_inventory_v46.json").read_text(encoding="utf-8")
        )
        cls.card = (ROOT / "MODEL_CARD.md").read_text(encoding="utf-8")

    def test_inventory_is_aggregate_only(self):
        self.assertEqual(self.inventory["status"], "V46_MODEL_RISK_INVENTORY_COMPLETE")
        self.assertFalse(self.inventory["row_level_data_accessed"])
        self.assertFalse(self.inventory["model_fit_executed"])
        self.assertFalse(self.inventory["historical_decisions_changed"])

    def test_four_models_remain_shadow_only(self):
        models = self.inventory["models"]
        self.assertEqual(len(models), 4)
        self.assertEqual({m["role"] for m in models}, {"reference", "challenger"})
        for model in models:
            self.assertEqual(model["serving_boundary"], "SHADOW_COMPARISON_ONLY")
            self.assertFalse(model["customer_pricing_authorised"])

    def test_validation_assets_are_consumed_not_fresh(self):
        assets = {x["dataset"]: x for x in self.inventory["validation_assets"]}
        self.assertEqual(set(assets), {
            "Spanish 2024",
            "Australian ausprivauto0405",
            "Belgian beMTPL97",
        })
        self.assertEqual(assets["Spanish 2024"]["current_role"], "CONSUMED_RETROSPECTIVE_VALIDATION")
        self.assertEqual(assets["Australian ausprivauto0405"]["current_role"], "CONSUMED_EXTERNAL_VALIDATION_DATASET")
        self.assertEqual(assets["Belgian beMTPL97"]["current_role"], "CONSUMED_EXTERNAL_VALIDATION_DATASET")
        for asset in assets.values():
            self.assertFalse(asset["fresh_independent_evidence_available"])
            self.assertFalse(asset["candidate_selection_allowed"])

    def test_external_evidence_is_zero_of_four_without_pooling(self):
        evidence = self.inventory["evidence_summary"]
        self.assertEqual(evidence["external_portfolios_evaluated"], 2)
        self.assertEqual(evidence["preregistered_external_target_gates_evaluated"], 4)
        self.assertEqual(evidence["preregistered_external_target_gates_passed"], 0)
        self.assertFalse(evidence["current_fresh_independent_validation_dataset_available"])
        self.assertFalse(evidence["pooled_meta_analysis_used"])
        self.assertFalse(evidence["subjective_evidence_weighting_used"])

    def test_operational_readiness_cannot_imply_approval(self):
        controls = self.inventory["operational_controls"]
        self.assertTrue(controls["shadow_serving_boundary"])
        self.assertTrue(controls["manual_rollback_control"])
        self.assertFalse(controls["automatic_review_serving_switch"])
        self.assertTrue(controls["attested_shadow_admission"])
        self.assertEqual(controls["raw_source_data_members_in_release_archive"], 0)
        decision = self.inventory["current_decision"]
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(decision["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])

    def test_committee_gate_has_three_evidence_blockers(self):
        gate = self.inventory["committee_readiness"]
        self.assertEqual(gate["status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual(gate["required_gate_pass_count"], 5)
        self.assertEqual(gate["required_gate_count"], 8)
        self.assertEqual(gate["required_gate_fail_count"], 3)
        self.assertEqual(gate["blocker_ids"], [
            "G2_LOCKED_TEMPORAL_SUPPORT",
            "G3_PREREGISTERED_EXTERNAL_SUPPORT",
            "G4_FRESH_INDEPENDENT_EVIDENCE",
        ])
        self.assertFalse(gate["human_committee_review_open"])
        self.assertFalse(gate["human_signoff_can_override_failed_evidence_gate"])

    def test_model_card_is_current_and_does_not_recycle_holdout(self):
        for marker in [
            "CONSUMED_RETROSPECTIVE_VALIDATION",
            "CONSUMED_EXTERNAL_VALIDATION_DATASET",
            "0 / 4 pass",
            "EVIDENCE_GAP_HOLD",
            "5 / 8 gates pass",
            "Australian `ausprivauto0405`",
            "Belgian `beMTPL97`",
            "1.42×10⁻¹⁴",
        ]:
            self.assertIn(marker, self.card)
        self.assertNotIn("2024: untouched final OOT evaluation", self.card)
        self.assertNotIn("Two public motor-insurance sources have different roles", self.card)

    def test_model_card_preserves_claim_boundaries(self):
        lower = self.card.lower()
        for marker in [
            "not an out-of-time pricing uplift",
            "not an insurer or regulatory standard",
            "not direct validation",
            "not a real customer-pricing or underwriting system",
            "proof of transfer to the current uk motor market",
            "a real model change committee decision",
        ]:
            self.assertIn(marker, lower)


if __name__ == "__main__":
    unittest.main()
