import inspect
import json
import math
import unittest
from pathlib import Path

import pandas as pd

import run_rating_factor_support_audit_v52 as v52
from deployment.contracts import CATEGORICAL_FEATURES, NUMERIC_FEATURES

ROOT = Path(__file__).resolve().parents[1]


class RatingFactorSupportV52Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "results_v52/rating_factor_support_summary_v52.json").read_text(encoding="utf-8")
        )
        cls.numeric = pd.read_csv(ROOT / "results_v52/numeric_feature_support_v52.csv")
        cls.categorical = pd.read_csv(ROOT / "results_v52/categorical_feature_support_v52.csv")
        cls.levels = pd.read_csv(ROOT / "results_v52/categorical_level_shift_v52.csv")

    def test_scope_is_label_free_2022_vs_2024_features(self):
        s = self.summary
        self.assertEqual(s["status"], "V52_LABEL_FREE_RATING_FACTOR_SUPPORT_AUDIT_COMPLETE")
        self.assertEqual(s["analysis_role"], "POST_HOC_LABEL_FREE_FEATURE_SUPPORT_AND_MIX_AUDIT")
        source = s["source"]
        self.assertEqual(source["source_file_sha256"], "6a47d19d5278a049ea0aeaf39c955cc26068639bdc58cb4523b201e740f0faf4")
        self.assertEqual(source["years_read"], [2022, 2024])
        self.assertEqual(source["development_rows"], 67171)
        self.assertEqual(source["current_rows"], 168085)
        self.assertFalse(source["2023_rows_read"])
        self.assertFalse(source["claim_outcomes_read"])
        self.assertFalse(source["incurred_loss_read"])
        self.assertFalse(source["actual_premium_read"])
        self.assertFalse(source["customer_id_read"])
        self.assertFalse(source["policy_status_read"])
        self.assertGreater(source["development_exposure"], 0)
        self.assertGreater(source["current_exposure"], 0)

    def test_reader_does_not_reference_outcome_or_commercial_fields(self):
        source = inspect.getsource(v52.read_feature_populations)
        for forbidden in ["total_claims", "total_incurred", "total_premium", "insured_id", "policy_status"]:
            self.assertNotIn(forbidden, source)
        self.assertIn('"year"', source)
        self.assertIn('"total_exposure"', source)

    def test_runner_has_no_ml_stack_dependency_or_model_fit(self):
        module_source = inspect.getsource(v52)
        for forbidden in ["sklearn", "xgboost", ".fit(", "model_definitions"]:
            self.assertNotIn(forbidden, module_source)
        self.assertFalse(self.summary["interpretation_boundary"]["model_fit_executed"])

    def test_strict_support_is_distinct_from_tail_shift(self):
        d = self.summary["definitions"]
        self.assertIn("observed 2022 minimum", d["strict_numeric_extrapolation"])
        self.assertIn("q05-q95", d["numeric_tail_shift"])
        self.assertIn("not automatically extrapolation", d["numeric_tail_shift"].lower())
        self.assertTrue(d["no_composite_score"])
        self.assertTrue(d["no_alert_or_acceptance_threshold_created"])

    def test_numeric_support_contract(self):
        self.assertEqual(set(self.numeric["feature"]), set(NUMERIC_FEATURES))
        for row in self.numeric.to_dict(orient="records"):
            self.assertLessEqual(row["development_observed_min"], row["development_q01"])
            self.assertLessEqual(row["development_q01"], row["development_q05"])
            self.assertLessEqual(row["development_q05"], row["development_q50"])
            self.assertLessEqual(row["development_q50"], row["development_q95"])
            self.assertLessEqual(row["development_q95"], row["development_q99"])
            self.assertLessEqual(row["development_q99"], row["development_observed_max"])
            for key in [
                "current_missing_exposure_share",
                "current_outside_development_observed_range_exposure_share",
                "current_outside_development_q01_q99_exposure_share",
                "current_outside_development_q05_q95_exposure_share",
            ]:
                self.assertGreaterEqual(row[key], 0.0)
                self.assertLessEqual(row[key], 1.0 + 1e-12)
            self.assertLessEqual(
                row["current_outside_development_observed_range_exposure_share"],
                row["current_outside_development_q01_q99_exposure_share"] + 1e-12,
            )
            self.assertLessEqual(
                row["current_outside_development_q01_q99_exposure_share"],
                row["current_outside_development_q05_q95_exposure_share"] + 1e-12,
            )
            self.assertTrue(math.isfinite(row["v51_max_absolute_log_relativity_gap"]))

    def test_categorical_support_contract(self):
        self.assertEqual(set(self.categorical["feature"]), set(CATEGORICAL_FEATURES))
        self.assertEqual(set(self.levels["feature"]), set(CATEGORICAL_FEATURES))
        for row in self.categorical.to_dict(orient="records"):
            self.assertGreaterEqual(row["current_unseen_nonmissing_exposure_share"], 0)
            self.assertLessEqual(row["current_unseen_nonmissing_exposure_share"], 1 + 1e-12)
            self.assertGreaterEqual(row["total_variation_distance_2022_vs_2024"], 0)
            self.assertLessEqual(row["total_variation_distance_2022_vs_2024"], 1 + 1e-12)
            self.assertGreaterEqual(row["max_absolute_level_share_change"], 0)
            self.assertLessEqual(row["max_absolute_level_share_change"], 1 + 1e-12)
            self.assertTrue(math.isfinite(row["v51_max_absolute_log_relativity_gap"]))

    def test_level_distributions_reconcile_to_one(self):
        for feature in CATEGORICAL_FEATURES:
            rows = self.levels[self.levels["feature"] == feature]
            self.assertAlmostEqual(float(rows["development_share"].sum()), 1.0, places=12)
            self.assertAlmostEqual(float(rows["current_share"].sum()), 1.0, places=12)
            expected_tv = 0.5 * float(rows["absolute_share_change"].sum())
            observed_tv = float(
                self.categorical.loc[
                    self.categorical["feature"] == feature,
                    "total_variation_distance_2022_vs_2024",
                ].iloc[0]
            )
            self.assertAlmostEqual(expected_tv, observed_tv, places=12)

    def test_descriptive_regression_separates_shape_support_and_mix(self):
        numeric = self.summary["numeric_features"]
        categorical = self.summary["categorical_features"]
        self.assertAlmostEqual(numeric["driver_age"]["v51_max_absolute_log_relativity_gap"], 0.26865990121735667, places=12)
        self.assertAlmostEqual(numeric["driver_age"]["current_outside_development_observed_range_exposure_share"], 1.5871206507159884e-05, places=12)
        self.assertAlmostEqual(numeric["vehicle_age"]["current_outside_development_observed_range_exposure_share"], 7.935603253579942e-06, places=12)
        self.assertAlmostEqual(numeric["vehicle_value"]["current_outside_development_q05_q95_exposure_share"], 0.09574485778888048, places=12)
        self.assertAlmostEqual(categorical["business_type"]["v51_max_absolute_log_relativity_gap"], 0.02571338968862851, places=12)
        self.assertAlmostEqual(categorical["business_type"]["total_variation_distance_2022_vs_2024"], 0.48595824222641637, places=12)
        self.assertEqual(categorical["business_type"]["current_unseen_nonmissing_level_count"], 0)
        self.assertAlmostEqual(categorical["vehicle_brand"]["current_unseen_nonmissing_exposure_share"], 3.452530949776697e-05, places=12)
        self.assertEqual(categorical["vehicle_brand"]["current_unseen_nonmissing_level_count"], 6)

    def test_business_type_mix_reconciles_under_v52_filter(self):
        rows = self.levels[self.levels["feature"] == "business_type"].set_index("level")
        self.assertAlmostEqual(float(rows.loc["NB", "development_share"]), 0.9677561751126499, places=12)
        self.assertAlmostEqual(float(rows.loc["P", "development_share"]), 0.0322438248873501, places=12)
        self.assertAlmostEqual(float(rows.loc["NB", "current_share"]), 0.4817979328862335, places=12)
        self.assertAlmostEqual(float(rows.loc["P", "current_share"]), 0.5182020671137666, places=12)

    def test_v51_shape_gap_is_lineage_not_composite_score(self):
        lineage = self.summary["v51_lineage"]
        self.assertEqual(lineage["source_analysis_role"], "DEVELOPMENT_ONLY_REFERENCE_PROFILE_INTERPRETABILITY_AUDIT")
        self.assertTrue(lineage["development_shape_gap_used_descriptively"])
        self.assertTrue(self.summary["definitions"]["no_composite_score"])
        self.assertEqual(set(self.summary["numeric_features"]), set(NUMERIC_FEATURES))
        self.assertEqual(set(self.summary["categorical_features"]), set(CATEGORICAL_FEATURES))

    def test_interpretation_boundary_remains_non_promotional(self):
        b = self.summary["interpretation_boundary"]
        self.assertTrue(b["post_hoc_consumed_validation_features_only"])
        self.assertFalse(b["validation_performance_evidence_created"])
        self.assertFalse(b["candidate_selection_allowed"])
        self.assertFalse(b["model_fit_executed"])
        self.assertFalse(b["model_promotion_evidence_created"])
        self.assertFalse(b["customer_pricing_authorised"])
        self.assertFalse(b["causal_interpretation_claimed"])
        self.assertFalse(b["fairness_conclusion_claimed"])
        self.assertFalse(b["first_central_or_current_uk_transport_claimed"])
        lower = b["interpretation"].lower()
        self.assertIn("no 2024 claim/loss outcomes", lower)
        self.assertIn("subjective score", lower)

    def test_outputs_are_aggregate_only(self):
        forbidden = {"insured_id", "total_claims", "total_incurred", "total_premium"}
        self.assertTrue(forbidden.isdisjoint(self.numeric.columns))
        self.assertTrue(forbidden.isdisjoint(self.categorical.columns))
        self.assertTrue(forbidden.isdisjoint(self.levels.columns))
        self.assertFalse(self.summary["persisted_row_level_data"])


if __name__ == "__main__":
    unittest.main()
