import inspect
import json
import math
import unittest
from pathlib import Path

import pandas as pd

import run_frozen_model_disagreement_attribution_v47 as v47
from deployment.contracts import FEATURES

ROOT = Path(__file__).resolve().parents[1]


class DisagreementAttributionV47Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "results_v47/disagreement_attribution_summary_v47.json").read_text(encoding="utf-8")
        )
        cls.attr = pd.read_csv(ROOT / "results_v47/feature_disagreement_attribution_v47.csv")
        cls.segments = pd.read_csv(ROOT / "results_v47/segment_disagreement_v47.csv")
        cls.manifest = json.loads(
            (ROOT / "results_v47/diagnostic_sample_manifest_v47.json").read_text(encoding="utf-8")
        )

    def test_analysis_is_post_hoc_and_cannot_change_model_decision(self):
        s = self.summary
        self.assertEqual(s["analysis_role"], "POST_HOC_DIAGNOSTIC_ON_CONSUMED_RETROSPECTIVE_VALIDATION")
        self.assertFalse(s["candidate_selection_allowed"])
        self.assertFalse(s["model_or_calibration_parameter_change"])
        self.assertFalse(s["promotion_evidence_created"])
        self.assertFalse(s["customer_pricing_authorised"])
        self.assertFalse(s["persisted_row_level_data"])

    def test_2024_diagnostic_reader_excludes_outcomes(self):
        source = inspect.getsource(v47.read_2024_features_only)
        self.assertNotIn("total_claims", source)
        self.assertNotIn("total_incurred", source)
        self.assertIn("total_exposure", source)
        self.assertFalse(self.summary["source"]["diagnostic_2024_outcome_labels_read"])
        self.assertFalse(self.manifest["2024_outcome_labels_used"])
        self.assertFalse(self.manifest["outcome_stratified"])

    def test_diagnostic_sample_is_fixed_and_non_outcome_stratified(self):
        source = self.summary["source"]
        self.assertEqual(source["diagnostic_sample_seed"], 20260823)
        self.assertEqual(source["diagnostic_sample_rows"], min(20000, source["diagnostic_rows_with_positive_exposure"]))
        self.assertFalse(source["outcome_stratified_sample"])
        self.assertEqual(self.manifest["seed"], 20260823)
        self.assertEqual(len(self.manifest["sample_index_sha256"]), 64)

    def test_every_registered_feature_has_both_target_diagnostics(self):
        self.assertEqual(set(self.attr["feature"]), set(FEATURES))
        self.assertEqual(set(self.attr["target"]), {"frequency", "pure_premium"})
        counts = self.attr.groupby("target")["feature"].nunique().to_dict()
        self.assertEqual(counts, {"frequency": len(FEATURES), "pure_premium": len(FEATURES)})

    def test_attribution_numbers_are_finite(self):
        numeric_cols = [
            "counterfactual_mean_absolute_log_disagreement",
            "absolute_disagreement_reduction",
            "fraction_of_baseline_abs_disagreement_reduced",
            "weighted_sign_flip_rate",
        ]
        for col in numeric_cols:
            self.assertTrue(self.attr[col].map(math.isfinite).all(), col)
        self.assertTrue(((self.attr["weighted_sign_flip_rate"] >= 0) & (self.attr["weighted_sign_flip_rate"] <= 1)).all())

    def test_method_is_explicitly_non_additive_and_non_causal(self):
        b = self.summary["method_boundary"]
        self.assertTrue(b["one_factor_at_a_time_reference_substitution"])
        self.assertFalse(b["effects_additive"])
        self.assertFalse(b["causal_interpretation_claimed"])
        self.assertFalse(b["shap_values_claimed"])
        self.assertFalse(b["feature_importance_for_model_performance_claimed"])

    def test_top_feature_shortlists_are_descriptive_only(self):
        top = self.summary["top_features_by_disagreement_reduction"]
        for target in ["frequency", "pure_premium"]:
            self.assertEqual(len(top[target]), 5)
            self.assertTrue(all(item["feature"] in FEATURES for item in top[target]))

    def test_segment_output_is_aggregate_and_label_free(self):
        forbidden = {"insured_id", "total_claims", "total_incurred", "total_premium"}
        self.assertTrue(forbidden.isdisjoint(self.segments.columns))
        self.assertEqual(set(self.segments["dimension"]), {
            "business_type", "policy_type", "payment_frequency", "driver_age_band"
        })
        self.assertTrue((self.segments["rows"] > 0).all())
        self.assertTrue((self.segments["exposure"] > 0).all())
        self.assertTrue(((self.segments["exposure_share"] > 0) & (self.segments["exposure_share"] <= 1)).all())

    def test_current_validation_firewall_allows_only_post_hoc_use(self):
        firewall = json.loads(
            (ROOT / "action_results/v35/validation_firewall_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(firewall["2024"]["current_role"], "CONSUMED_RETROSPECTIVE_VALIDATION")
        allowed = firewall["firewall"]["allowed_future_2024_purposes"]
        forbidden = firewall["firewall"]["forbidden_future_2024_purposes"]
        self.assertIn("post_hoc_diagnostics", allowed)
        self.assertIn("select_new_candidate_policy", forbidden)
        self.assertIn("authorise_model_family_promotion", forbidden)


if __name__ == "__main__":
    unittest.main()
