import json
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


class RatingContextSensitivityV56Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (ROOT / "governance/rating_context_sensitivity_protocol_v56.json").read_text(encoding="utf-8")
        )
        cls.summary = json.loads(
            (ROOT / "results_v56/rating_context_sensitivity_summary_v56.json").read_text(encoding="utf-8")
        )
        cls.curves = pd.read_csv(ROOT / "results_v56/rating_context_curve_points_v56.csv")
        cls.feature_context = pd.read_csv(ROOT / "results_v56/rating_context_feature_summary_v56.csv")
        cls.cross_context = pd.read_csv(ROOT / "results_v56/rating_context_cross_context_summary_v56.csv")

    def test_protocol_is_locked_before_execution(self):
        p = self.protocol
        self.assertEqual(p["status"], "V56_DEVELOPMENT_RATING_CONTEXT_SENSITIVITY_PROTOCOL_LOCKED")
        self.assertTrue(p["protocol_locked_before_first_v56_execution"])
        self.assertEqual(p["base_repository_commit"], "fe4f0d1638068879de40e1f76b5f2ebdaad2d894")
        self.assertFalse(p["interpretation_rules"]["context_stability_acceptance_threshold_created"])

    def test_scope_is_2022_development_frequency_only(self):
        s = self.summary
        self.assertEqual(s["analysis_role"], "DEVELOPMENT_ONLY_REFERENCE_PROFILE_CONTEXT_SENSITIVITY")
        self.assertEqual(s["source"]["years_read"], [2022])
        self.assertFalse(s["source"]["2023_rows_read"])
        self.assertFalse(s["source"]["2024_rows_read"])
        self.assertFalse(s["source"]["incurred_loss_read"])
        self.assertFalse(s["source"]["actual_premium_read"])
        self.assertFalse(s["source"]["customer_id_read"])
        self.assertFalse(s["source"]["policy_status_read"])
        self.assertTrue(s["models"]["model_fit_executed"])
        self.assertFalse(s["models"]["model_refit_per_context"])
        self.assertFalse(s["models"]["hyperparameter_search"])

    def test_contexts_are_exactly_preregistered(self):
        expected = {
            "BASE": ({}, 1.0),
            "BUSINESS_TYPE_P": ({"business_type": "P"}, 0.0322438248873501),
            "POLICY_TYPE_COMP_E": ({"policy_type": "COMP_E"}, 0.2375225200108693),
            "FUEL_TYPE_G": ({"fuel_type": "G"}, 0.36069678525926124),
            "CIRCULATION_AREA_R": ({"circulation_area": "R"}, 0.45981696634625785),
        }
        observed = {
            c["context_id"]: (
                c["change_from_v51_reference"],
                c["v51_marginal_exposure_share_of_changed_level"],
            )
            for c in self.summary["contexts"]
        }
        self.assertEqual(set(observed), set(expected))
        for key, (change, share) in expected.items():
            self.assertEqual(observed[key][0], change)
            self.assertAlmostEqual(observed[key][1], share, places=14)
        self.assertTrue(self.summary["contexts_are_synthetic_reference_profiles"])
        self.assertTrue(self.summary["marginal_exposure_share_is_not_joint_profile_prevalence"])

    def test_registered_grid_has_exact_dimensions(self):
        self.assertEqual(set(self.curves["feature"]), {"driver_age", "vehicle_age"})
        self.assertEqual(self.curves["context_id"].nunique(), 5)
        self.assertEqual(len(self.curves), 110)
        self.assertEqual(len(self.feature_context), 10)
        self.assertEqual(len(self.cross_context), 2)
        self.assertEqual(self.summary["registered_curve_point_count"], 110)
        self.assertEqual(self.summary["registered_feature_context_summary_count"], 10)
        counts = self.curves.groupby(["feature", "context_id"]).size()
        self.assertTrue((counts == 11).all())

    def test_reference_points_are_normalised_to_one(self):
        for feature, spec in self.protocol["target_features"].items():
            rows = self.curves[
                (self.curves["feature"] == feature)
                & np.isclose(self.curves["value"], spec["reference_value"])
            ]
            self.assertEqual(len(rows), 5)
            self.assertLess(float((rows["glm_frequency_relativity"] - 1.0).abs().max()), 1e-10)
            self.assertLess(float((rows["xgb_frequency_relativity"] - 1.0).abs().max()), 1e-10)
            self.assertLess(float(rows["log_xgb_over_glm_relativity"].abs().max()), 1e-10)

    def test_additive_glm_context_invariance_contract(self):
        c = self.summary["computational_contracts"]
        self.assertTrue(c["glm_context_invariance_contract_pass"])
        self.assertLessEqual(
            c["max_glm_log_relativity_range_across_contexts"],
            c["glm_context_invariance_tolerance"],
        )
        self.assertLessEqual(
            float(self.cross_context["max_glm_log_relativity_range_across_contexts_over_registered_grid"].max()),
            1e-8,
        )

    def test_preselected_points_are_exactly_registered_not_posthoc(self):
        expected = {("driver_age", 0.95, 68.0), ("vehicle_age", 0.95, 44.0)}
        protocol_points = {
            (p["feature"], p["quantile"], p["value"])
            for p in self.protocol["preselected_review_points"]
        }
        result_points = {
            (p["feature"], p["quantile"], p["value"])
            for p in self.summary["preselected_review_points"]
        }
        self.assertEqual(protocol_points, expected)
        self.assertEqual(result_points, expected)
        for p in self.summary["preselected_review_points"]:
            self.assertEqual(len(p["by_context"]), 5)

    def test_base_curve_rebuild_is_tied_back_to_v51(self):
        for row in self.cross_context.itertuples(index=False):
            self.assertLess(abs(row.base_q95_minus_v51_registered), 1e-6)

    def test_outputs_are_aggregate_profile_scores_only(self):
        forbidden = {
            "insured_id", "customer_id", "policy_id", "total_premium", "premium",
            "total_claims", "claim_count", "incurred", "loss", "policy_status",
        }
        observed_cols = set(map(str.lower, self.curves.columns)) | set(map(str.lower, self.feature_context.columns))
        self.assertTrue(forbidden.isdisjoint(observed_cols))
        self.assertFalse(self.summary["persisted_row_level_data"])

    def test_interpretation_is_not_validation_causality_or_pricing(self):
        b = self.summary["interpretation_boundary"]
        self.assertFalse(b["context_stability_acceptance_threshold_created"])
        self.assertFalse(b["composite_score_created"])
        self.assertFalse(b["confidence_interval_claimed"])
        self.assertFalse(b["predictive_validation_evidence_created"])
        self.assertFalse(b["causal_interaction_claimed"])
        self.assertFalse(b["observed_segment_effect_claimed"])
        self.assertFalse(b["customer_premium_effect_claimed"])
        self.assertFalse(b["candidate_selection_allowed"])
        self.assertFalse(b["model_promotion_evidence_created"])
        self.assertFalse(b["customer_pricing_authorised"])
        self.assertFalse(b["first_central_or_current_uk_transport_claimed"])
        g = self.summary["governance_state_unchanged"]
        self.assertEqual(g["committee_status"], "EVIDENCE_GAP_HOLD")
        self.assertEqual((g["committee_gate_pass_count"], g["committee_gate_count"]), (5, 8))
        self.assertEqual(g["external_target_gates"], "0/4")
        self.assertEqual(g["model_family_decision"], "HOLD")
        self.assertEqual(g["serving_status"], "HOLD_SHADOW_ONLY")
        self.assertEqual(g["promotion_review_status"], "NOT_OPEN")
        self.assertFalse(g["customer_pricing_authorised"])


if __name__ == "__main__":
    unittest.main()
