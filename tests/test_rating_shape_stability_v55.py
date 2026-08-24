import inspect
import json
import math
import unittest
from pathlib import Path

import pandas as pd

import run_rating_factor_relativity_audit_v51 as v51
import run_rating_shape_stability_audit_v55 as v55

ROOT = Path(__file__).resolve().parents[1]


class RatingShapeStabilityV55Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol = json.loads(
            (ROOT / "governance/rating_shape_stability_protocol_v55.json").read_text(encoding="utf-8")
        )
        cls.summary = json.loads(
            (ROOT / "results_v55/rating_shape_stability_summary_v55.json").read_text(encoding="utf-8")
        )
        cls.fold_points = pd.read_csv(ROOT / "results_v55/rating_shape_stability_fold_points_v55.csv")
        cls.point_summary = pd.read_csv(ROOT / "results_v55/rating_shape_stability_point_summary_v55.csv")

    def test_protocol_is_locked_and_result_does_not_change_design(self):
        p = self.protocol
        self.assertEqual(p["status"], "V55_DEVELOPMENT_RATING_SHAPE_STABILITY_PROTOCOL_LOCKED")
        self.assertEqual(p["fold_design"]["fold_count"], 5)
        self.assertEqual(p["fold_design"]["seed"], 20260824)
        self.assertFalse(p["fold_design"]["outcome_stratification"])
        self.assertFalse(p["evaluation_grid"]["grid_reestimated_per_fold"])
        self.assertFalse(p["evaluation_grid"]["reference_profile_reestimated_per_fold"])
        self.assertTrue(self.summary["protocol"]["locked_before_first_execution"])
        self.assertEqual(self.summary["protocol"]["sha256"], v55.sha256_file(v55.PROTOCOL_PATH))

    def test_scope_is_2022_development_frequency_only(self):
        s = self.summary
        self.assertEqual(s["status"], "V55_DEVELOPMENT_RATING_SHAPE_STABILITY_AUDIT_COMPLETE")
        self.assertEqual(s["analysis_role"], "DEVELOPMENT_ONLY_FIXED_FOLD_RESPONSE_SHAPE_STABILITY_AUDIT")
        source = s["source"]
        self.assertEqual(source["years_read"], [2022])
        for key in ["2023_rows_read", "2024_rows_read", "incurred_loss_read", "actual_premium_read", "customer_id_read", "policy_status_read"]:
            self.assertFalse(source[key])
        self.assertEqual(source["rows"], 67171)
        self.assertGreater(source["exposure"], 0)
        self.assertGreater(source["claims"], 0)
        models = s["models"]
        self.assertEqual(set(models["names"]), {"poisson_glm_frequency", "xgb_poisson_frequency"})
        self.assertEqual(models["target"], "frequency")
        self.assertTrue(models["model_fit_executed"])
        self.assertFalse(models["calibration_applied"])
        self.assertFalse(models["grid_reestimated_per_fold"])
        self.assertFalse(models["reference_profile_reestimated_per_fold"])

    def test_reused_reader_has_no_loss_premium_id_or_status_fields(self):
        source = inspect.getsource(v51.read_2022_development)
        for forbidden in ["total_incurred", "total_premium", "insured_id", "policy_status"]:
            self.assertNotIn(forbidden, source)
        self.assertIn('(frame["year"] == 2022)', source)
        self.assertIn("total_claims", source)
        self.assertIn("total_exposure", source)

    def test_fold_assignment_is_balanced_and_exhaustive(self):
        s = self.summary
        folds = s["fold_design"]["folds"]
        self.assertEqual(len(folds), 5)
        excluded = [row["excluded_rows"] for row in folds]
        self.assertLessEqual(max(excluded) - min(excluded), 1)
        self.assertEqual(sum(excluded), s["source"]["rows"])
        self.assertEqual(s["fold_design"]["excluded_row_count_sum"], s["source"]["rows"])
        self.assertAlmostEqual(sum(row["excluded_exposure"] for row in folds), s["source"]["exposure"], places=9)
        self.assertAlmostEqual(sum(row["excluded_claims"] for row in folds), s["source"]["claims"], places=9)
        for row in folds:
            self.assertEqual(row["train_rows"] + row["excluded_rows"], s["source"]["rows"])

    def test_registered_grid_is_exactly_five_fold_repeats(self):
        g = self.summary["registered_grid"]
        self.assertGreater(g["numeric_point_count"], 0)
        self.assertGreater(g["categorical_point_count"], 0)
        self.assertEqual(g["fold_point_row_count"], 5 * (g["numeric_point_count"] + g["categorical_point_count"]))
        self.assertEqual(g["point_summary_row_count"], g["numeric_point_count"] + g["categorical_point_count"])
        counts = self.fold_points.groupby(["feature", "point_type", "point_key"], dropna=False).size()
        self.assertTrue((counts == 5).all())
        self.assertEqual(set(self.fold_points["fold_id"]), {0, 1, 2, 3, 4})

    def test_point_summary_statistics_reconcile_to_fold_points(self):
        for row in self.point_summary.to_dict(orient="records"):
            mask = (
                (self.fold_points["feature"] == row["feature"])
                & (self.fold_points["point_type"] == row["point_type"])
                & (self.fold_points["point_key"].astype(str) == str(row["point_key"]))
            )
            values = self.fold_points.loc[mask, "log_xgb_over_glm_relativity"].astype(float)
            self.assertEqual(len(values), 5)
            self.assertAlmostEqual(float(values.min()), row["fold_min_log_gap"], places=12)
            self.assertAlmostEqual(float(values.max()), row["fold_max_log_gap"], places=12)
            self.assertAlmostEqual(float(values.max() - values.min()), row["fold_log_gap_range"], places=12)
            self.assertAlmostEqual(float(values.mean()), row["fold_mean_log_gap"], places=12)
            self.assertGreaterEqual(row["fold_std_log_gap"], 0)
            self.assertTrue(math.isfinite(row["v51_full_fit_log_gap"]))

    def test_feature_summaries_cover_v51_feature_contract(self):
        fs = self.summary["feature_summary"]
        v51_summary = json.loads((ROOT / "action_results/v51/rating_factor_relativity_summary_v51.json").read_text())
        expected = set(v51_summary["numeric_grid"]["features"]) | set(v51_summary["categorical_grid"]["features"])
        self.assertEqual(set(fs), expected)
        for item in fs.values():
            self.assertGreaterEqual(item["v51_max_absolute_log_gap"], 0)
            self.assertGreaterEqual(item["max_fold_log_gap_range_over_registered_points"], 0)
            self.assertGreater(item["registered_point_count"], 0)
            if item["minimum_same_sign_fraction_over_nonzero_v51_points"] is not None:
                self.assertGreaterEqual(item["minimum_same_sign_fraction_over_nonzero_v51_points"], 0)
                self.assertLessEqual(item["minimum_same_sign_fraction_over_nonzero_v51_points"], 1)

    def test_preselected_review_points_are_exactly_preregistered(self):
        observed = {(r["feature"], r["point_key"]) for r in self.summary["preselected_review_points"]}
        self.assertEqual(observed, {("driver_age", "q0.95"), ("vehicle_age", "q0.95"), ("vehicle_value", "q0.95")})
        for row in self.summary["preselected_review_points"]:
            self.assertGreaterEqual(row["fold_log_gap_range"], 0)
            fraction = row["fraction_folds_same_sign_as_v51_full_fit"]
            self.assertIsNotNone(fraction)
            self.assertGreaterEqual(fraction, 0)
            self.assertLessEqual(fraction, 1)

    def test_interpretation_is_not_ci_validation_or_pricing(self):
        b = self.summary["interpretation_boundary"]
        for key in [
            "confidence_interval_claimed",
            "bootstrap_claimed",
            "predictive_validation_evidence_created",
            "candidate_selection_allowed",
            "model_promotion_evidence_created",
            "customer_pricing_authorised",
            "causal_interpretation_claimed",
            "population_average_pdp_claimed",
            "stability_acceptance_threshold_created",
            "composite_score_created",
            "first_central_or_current_uk_transport_claimed",
        ]:
            self.assertFalse(b[key])
        lower = b["interpretation"].lower()
        self.assertIn("not confidence intervals", lower)
        self.assertIn("not", lower)
        self.assertIn("held-out predictive validation", lower)

    def test_persisted_curve_outputs_are_aggregate_only(self):
        forbidden = {"insured_id", "total_claims", "total_exposure", "total_incurred", "total_premium"}
        self.assertTrue(forbidden.isdisjoint(self.fold_points.columns))
        self.assertTrue(forbidden.isdisjoint(self.point_summary.columns))
        self.assertFalse(self.summary["persisted_row_level_data"])


if __name__ == "__main__":
    unittest.main()
