import inspect
import json
import math
import unittest
from pathlib import Path

import pandas as pd

import run_frozen_model_disagreement_attribution_v47 as v47
import run_portfolio_neutral_relativity_migration_v48 as v48

ROOT = Path(__file__).resolve().parents[1]


class PortfolioNeutralRelativityV48Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "results_v48/portfolio_neutral_relativity_summary_v48.json").read_text(encoding="utf-8")
        )
        cls.bands = pd.read_csv(ROOT / "results_v48/relativity_migration_bands_v48.csv")
        cls.segments = pd.read_csv(ROOT / "results_v48/segment_relativity_migration_v48.csv")

    def test_analysis_is_label_free_post_hoc_only(self):
        s = self.summary
        self.assertEqual(s["analysis_role"], "POST_HOC_LABEL_FREE_TECHNICAL_RELATIVITY_DIAGNOSTIC")
        self.assertEqual(s["validation_role"], "CONSUMED_RETROSPECTIVE_VALIDATION_DIAGNOSTIC_ONLY")
        self.assertFalse(s["candidate_selection_allowed"])
        self.assertFalse(s["model_or_calibration_parameter_change"])
        self.assertFalse(s["promotion_evidence_created"])
        self.assertFalse(s["customer_pricing_authorised"])
        self.assertFalse(s["actual_customer_premium_used"])
        self.assertFalse(s["commercial_uplift_claimed"])
        self.assertFalse(s["persisted_row_level_data"])

    def test_2024_reader_still_excludes_outcomes_and_premium(self):
        source = inspect.getsource(v47.read_2024_features_only)
        self.assertNotIn("total_claims", source)
        self.assertNotIn("total_incurred", source)
        self.assertNotIn("total_premium", source)
        self.assertIn("total_exposure", source)
        self.assertFalse(self.summary["source"]["diagnostic_2024_outcome_labels_read"])
        self.assertFalse(self.summary["actual_customer_premium_used"])

    def test_full_positive_exposure_population_is_used(self):
        source = self.summary["source"]
        v47_summary = json.loads(
            (ROOT / "action_results/v47/disagreement_attribution_summary_v47.json").read_text(encoding="utf-8")
        )
        self.assertTrue(source["full_positive_exposure_population_used"])
        self.assertEqual(source["diagnostic_rows"], v47_summary["source"]["diagnostic_rows_with_positive_exposure"])
        self.assertEqual(source["diagnostic_rows"], 168085)
        self.assertGreater(source["diagnostic_exposure"], 0)

    def test_portfolio_neutralisation_is_exact_within_numeric_tolerance(self):
        for target in ["frequency", "pure_premium"]:
            n = self.summary["targets"][target]["portfolio_neutralisation"]
            self.assertTrue(math.isfinite(n["portfolio_neutral_scale_applied_to_challenger"]))
            self.assertGreater(n["portfolio_neutral_scale_applied_to_challenger"], 0)
            self.assertAlmostEqual(n["normalised_total_over_reference"], 1.0, places=12)
            tolerance = max(1e-9, 1e-12 * n["reference_predicted_total"])
            self.assertLessEqual(n["absolute_total_difference_after_neutralisation"], tolerance)

    def test_change_bands_are_fixed_and_exhaustive(self):
        expected = [
            "LT_MINUS_20",
            "MINUS_20_TO_MINUS_10",
            "MINUS_10_TO_MINUS_5",
            "WITHIN_5",
            "PLUS_5_TO_PLUS_10",
            "PLUS_10_TO_PLUS_20",
            "GT_PLUS_20",
        ]
        self.assertEqual([x["id"] for x in self.summary["fixed_change_bands"]], expected)
        for target in ["frequency", "pure_premium"]:
            x = self.bands[self.bands["target"] == target]
            self.assertEqual(x["band_id"].tolist(), expected)
            self.assertEqual(int(x["rows"].sum()), self.summary["source"]["diagnostic_rows"])
            self.assertAlmostEqual(float(x["exposure_share"].sum()), 1.0, places=12)

    def test_distribution_metrics_are_valid(self):
        for target in ["frequency", "pure_premium"]:
            d = self.summary["targets"][target]["relativity_change_distribution"]
            for key in [
                "challenger_higher_exposure_share",
                "challenger_lower_exposure_share",
                "absolute_change_gt_5pct_exposure_share",
                "absolute_change_gt_10pct_exposure_share",
                "absolute_change_gt_20pct_exposure_share",
            ]:
                self.assertGreaterEqual(d[key], 0.0)
                self.assertLessEqual(d[key], 1.0)
            q = d["quantiles"]
            ordered = [q[k] for k in ["q05", "q10", "q25", "q50", "q75", "q90", "q95"]]
            self.assertEqual(ordered, sorted(ordered))

    def test_segment_migration_is_aggregate_only(self):
        forbidden = {"insured_id", "total_claims", "total_incurred", "total_premium", "reference", "challenger"}
        self.assertTrue(forbidden.isdisjoint(self.segments.columns))
        self.assertEqual(set(self.segments["dimension"]), {
            "business_type", "policy_type", "payment_frequency", "driver_age_band"
        })
        self.assertTrue((self.segments["rows"] > 0).all())
        self.assertTrue((self.segments["exposure"] > 0).all())
        self.assertTrue(((self.segments["exposure_share"] > 0) & (self.segments["exposure_share"] <= 1)).all())

    def test_interpretation_boundary_is_not_customer_pricing(self):
        b = self.summary["interpretation_boundary"]
        self.assertTrue(b["technical_risk_score_only"])
        self.assertFalse(b["actual_premium_or_quote"])
        self.assertFalse(b["pricing_action_or_rate_change"])
        self.assertFalse(b["expense_commission_reinsurance_profit_tax_demand_components_included"])
        self.assertFalse(b["fairness_or_regulatory_conclusion_claimed"])
        self.assertFalse(b["causal_interpretation_claimed"])
        self.assertIn("not a customer premium", b["interpretation"].lower())
        self.assertIn("not", b["interpretation"].lower())
        self.assertIn("pricing recommendation", b["interpretation"].lower())

    def test_frozen_model_warning_boundary_is_inherited(self):
        self.assertTrue(
            self.summary["frozen_model_definition"]["frozen_tweedie_glm_convergence_limitation_inherited"]
        )
        self.assertIn("build_deployment_bundle_v21.py", self.summary["frozen_model_definition"]["source"])

    def test_current_governance_still_forbids_promotion_from_2024(self):
        firewall = json.loads(
            (ROOT / "action_results/v35/validation_firewall_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(firewall["2024"]["current_role"], "CONSUMED_RETROSPECTIVE_VALIDATION")
        self.assertIn("post_hoc_diagnostics", firewall["firewall"]["allowed_future_2024_purposes"])
        self.assertIn("authorise_customer_pricing", firewall["firewall"]["forbidden_future_2024_purposes"])


if __name__ == "__main__":
    unittest.main()
