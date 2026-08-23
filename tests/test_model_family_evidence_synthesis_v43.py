import json
import unittest
from pathlib import Path

import build_model_family_review_pack_v43 as v43

ROOT = Path(__file__).resolve().parents[1]


class ModelFamilyEvidenceSynthesisV43Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        v43.main()
        cls.policy = json.loads(
            (ROOT / "governance/model_family_evidence_synthesis_policy_v43.json").read_text(encoding="utf-8")
        )
        cls.summary = json.loads(
            (ROOT / "results_v43/model_family_evidence_synthesis_summary.json").read_text(encoding="utf-8")
        )

    def test_synthesis_is_aggregate_only_and_cannot_tune(self):
        rules = self.policy["synthesis_rules"]
        self.assertFalse(rules["row_level_data_access_allowed"])
        self.assertFalse(rules["model_fit_allowed"])
        self.assertFalse(rules["recalibration_allowed"])
        self.assertFalse(rules["hyperparameter_search_allowed"])
        self.assertFalse(rules["resplitting_or_reseeding_allowed"])
        self.assertFalse(rules["historical_gate_changes_allowed"])

    def test_no_pooled_score_can_override_registered_decisions(self):
        rules = self.policy["synthesis_rules"]
        self.assertFalse(rules["pooled_meta_analysis_claim_allowed"])
        self.assertFalse(rules["evidence_weighting_score_allowed"])
        self.assertFalse(rules["benchmark_can_authorise_promotion"])
        self.assertTrue(rules["external_registered_gate_failure_remains_failure"])
        self.assertFalse(rules["numerical_reproducibility_can_convert_negative_gate_to_positive"])

    def test_all_preregistered_external_target_gates_remain_failed(self):
        p = self.summary["portfolio_level_summary"]
        self.assertEqual(p["external_portfolios_evaluated"], 2)
        self.assertEqual(p["external_target_gates_evaluated"], 4)
        self.assertEqual(p["external_target_gates_passed"], 0)
        self.assertEqual(p["external_frequency_gates_passed"], 0)
        self.assertEqual(p["external_pure_premium_gates_passed"], 0)

    def test_benchmark_signal_is_retained_but_not_promotion_evidence(self):
        benchmark = next(e for e in self.summary["evidence_basis"] if e["id"] == "fremtpl2_cross_sectional_frequency")
        self.assertGreater(benchmark["relative_deviance_improvement"], 0.05)
        self.assertEqual(benchmark["registered_decision"], "DEVELOPMENT_BENCHMARK_ONLY")
        self.assertIsNone(benchmark["gate_passed"])
        self.assertFalse(self.summary["synthesis_boundaries"]["benchmark_used_as_promotion_evidence"])

    def test_spanish_australian_and_belgian_validation_are_consumed(self):
        p = self.summary["portfolio_level_summary"]
        self.assertEqual(
            p["current_consumed_validation_datasets"],
            ["Spanish 2024", "Australian ausprivauto0405", "Belgian beMTPL97"],
        )
        self.assertFalse(p["current_fresh_independent_validation_dataset_available"])
        self.assertFalse(self.summary["synthesis_boundaries"]["consumed_validation_relabelled_independent"])

    def test_belgian_negative_results_are_numerically_reproduced(self):
        belgian = [e for e in self.summary["evidence_basis"] if e["id"].startswith("belgian_external_")]
        self.assertEqual(len(belgian), 2)
        for evidence in belgian:
            self.assertFalse(evidence["gate_passed"])
            self.assertTrue(evidence["numerically_reproduced_within_registered_tolerance"])

    def test_decision_is_hold_and_review_not_open(self):
        decision = self.summary["decision"]
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(decision["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])

    def test_future_reopen_requires_new_unseen_preregistered_evidence(self):
        requirements = " ".join(self.summary["reopen_requirements"]).lower()
        self.assertIn("genuinely new independent", requirements)
        self.assertIn("protocol merged before row-level", requirements)
        self.assertIn("two-independent-actions", requirements)
        self.assertIn("separate authorised governance decision", requirements)

    def test_no_first_central_or_current_uk_transport_claim(self):
        self.assertFalse(self.summary["synthesis_boundaries"]["first_central_or_current_uk_transport_claimed"])
        pack = (ROOT / "results_v43/MODEL_FAMILY_REVIEW_PACK_V43.md").read_text(encoding="utf-8")
        self.assertIn("Nothing here establishes transport to FIRST CENTRAL", pack)


if __name__ == "__main__":
    unittest.main()
