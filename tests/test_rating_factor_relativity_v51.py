import inspect
import json
import math
import unittest
from pathlib import Path

import pandas as pd

import run_rating_factor_relativity_audit_v51 as v51
from deployment.contracts import CATEGORICAL_FEATURES, NUMERIC_FEATURES

ROOT = Path(__file__).resolve().parents[1]


class RatingFactorRelativityV51Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads(
            (ROOT / "results_v51/rating_factor_relativity_summary_v51.json").read_text(encoding="utf-8")
        )
        cls.numeric = pd.read_csv(ROOT / "results_v51/numeric_rating_factor_relativities_v51.csv")
        cls.categorical = pd.read_csv(ROOT / "results_v51/categorical_rating_factor_relativities_v51.csv")
        cls.repeat = json.loads(
            (ROOT / "governance/v51_repeat_run_audit.json").read_text(encoding="utf-8")
        )

    def test_scope_is_2022_development_only(self):
        s = self.summary
        self.assertEqual(s["status"], "V51_DEVELOPMENT_RATING_FACTOR_RELATIVITY_AUDIT_COMPLETE")
        self.assertEqual(s["analysis_role"], "DEVELOPMENT_ONLY_REFERENCE_PROFILE_INTERPRETABILITY_AUDIT")
        source = s["source"]
        self.assertEqual(source["years_read"], [2022])
        self.assertFalse(source["2023_rows_read"])
        self.assertFalse(source["2024_rows_read"])
        self.assertFalse(source["incurred_loss_read"])
        self.assertFalse(source["actual_premium_read"])
        self.assertFalse(source["customer_id_read"])
        self.assertGreater(source["rows"], 0)
        self.assertGreater(source["exposure"], 0)
        self.assertGreater(source["claims"], 0)

    def test_reader_excludes_loss_premium_id_and_status_fields(self):
        source = inspect.getsource(v51.read_2022_development)
        for forbidden in ["total_incurred", "total_premium", "insured_id", "policy_status"]:
            self.assertNotIn(forbidden, source)
        self.assertIn('frame["year"] == 2022', source)
        self.assertIn("total_claims", source)
        self.assertIn("total_exposure", source)

    def test_only_frozen_frequency_models_are_fitted(self):
        f = self.summary["frozen_frequency_definition"]
        self.assertEqual(f["source"], "build_deployment_bundle_v21.py::model_definitions")
        self.assertEqual(set(f["models"]), {"poisson_glm_frequency", "xgb_poisson_frequency"})
        self.assertTrue(f["model_fit_executed"])
        self.assertFalse(f["calibration_applied"])
        self.assertIn("cancel", f["reason_calibration_not_needed"].lower())

    def test_reference_profile_covers_feature_contract(self):
        reference = self.summary["reference_profile"]
        self.assertEqual(set(reference), set(NUMERIC_FEATURES) | set(CATEGORICAL_FEATURES))
        scores = self.summary["reference_profile_scores"]
        self.assertEqual(set(scores), {"poisson_glm_frequency", "xgb_poisson_frequency"})
        self.assertTrue(all(math.isfinite(float(v)) and float(v) > 0 for v in scores.values()))

    def test_numeric_grid_is_registered_and_supported(self):
        self.assertEqual(set(self.numeric["feature"]), set(NUMERIC_FEATURES))
        expected_quantiles = v51.QUANTILES
        for feature in NUMERIC_FEATURES:
            g = self.numeric[self.numeric["feature"] == feature]
            self.assertEqual(len(g), len(expected_quantiles))
            self.assertEqual(g["quantile"].tolist(), expected_quantiles)
            self.assertEqual(g["value"].tolist(), sorted(g["value"].tolist()))
            self.assertTrue((g["glm_frequency_relativity"] > 0).all())
            self.assertTrue((g["xgb_frequency_relativity"] > 0).all())
            self.assertTrue(g["log_xgb_over_glm_relativity"].map(math.isfinite).all())

    def test_categorical_grid_is_top_exposure_plus_reference(self):
        self.assertEqual(set(self.categorical["feature"]), set(CATEGORICAL_FEATURES))
        summaries = self.summary["categorical_grid"]["features"]
        for feature in CATEGORICAL_FEATURES:
            g = self.categorical[self.categorical["feature"] == feature]
            self.assertGreaterEqual(len(g), 1)
            self.assertLessEqual(len(g), v51.MAX_CATEGORICAL_LEVELS + 1)
            self.assertEqual(int(g["is_reference_level"].sum()), 1)
            ref = g[g["is_reference_level"]].iloc[0]
            self.assertAlmostEqual(float(ref["glm_frequency_relativity"]), 1.0, places=12)
            self.assertAlmostEqual(float(ref["xgb_frequency_relativity"]), 1.0, places=12)
            self.assertGreater(float(g["exposure_share"].sum()), 0)
            self.assertLessEqual(float(g["exposure_share"].sum()), 1.0 + 1e-12)
            self.assertEqual(summaries[feature]["reference_level"], str(ref["level"]))

    def test_shape_summaries_exist_for_all_factors(self):
        numeric = self.summary["numeric_grid"]["features"]
        categorical = self.summary["categorical_grid"]["features"]
        self.assertEqual(set(numeric), set(NUMERIC_FEATURES))
        self.assertEqual(set(categorical), set(CATEGORICAL_FEATURES))
        for item in numeric.values():
            self.assertGreaterEqual(item["max_absolute_log_relativity_gap"], 0)
            self.assertGreaterEqual(item["glm_direction_changes_over_quantile_grid"], 0)
            self.assertGreaterEqual(item["xgb_direction_changes_over_quantile_grid"], 0)
        for item in categorical.values():
            self.assertGreaterEqual(item["max_absolute_log_relativity_gap"], 0)
            self.assertGreater(item["displayed_exposure_share"], 0)
            self.assertLessEqual(item["displayed_exposure_share"], 1.0 + 1e-12)

    def test_repeat_run_audit_is_descriptive_and_stable_at_reported_precision(self):
        r = self.repeat
        self.assertEqual(r["status"], "V51_DEVELOPMENT_INTERPRETABILITY_REPEAT_RUN_AUDIT_PASS")
        self.assertEqual(r["evidence_role"], "DEVELOPMENT_INTERPRETABILITY_NUMERICAL_REPRODUCIBILITY_AUDIT")
        self.assertEqual(len(r["executions"]), 2)
        self.assertTrue(all(x["workflow_conclusion"] == "success" for x in r["executions"]))
        c = r["comparison"]
        self.assertTrue(c["numeric_grid_keys_identical"])
        self.assertTrue(c["categorical_grid_keys_identical"])
        self.assertTrue(c["numeric_factor_ranking_identical"])
        self.assertTrue(c["categorical_factor_ranking_identical"])
        self.assertEqual(c["numeric_xgb_relativity_max_absolute_difference"], 0.0)
        self.assertEqual(c["categorical_xgb_relativity_max_absolute_difference"], 0.0)
        self.assertLess(c["numeric_glm_relativity_max_absolute_difference"], 1e-6)
        self.assertLess(c["categorical_glm_relativity_max_absolute_difference"], 1e-6)
        self.assertFalse(r["validation_performance_evidence_created"])
        self.assertFalse(r["candidate_selection_allowed"])
        self.assertFalse(r["model_promotion_evidence_created"])
        self.assertFalse(r["customer_pricing_authorised"])
        self.assertFalse(r["interpretation"]["bitwise_reproducibility_claimed"])
        self.assertFalse(r["interpretation"]["validation_reproducibility_claimed"])
        self.assertFalse(r["interpretation"]["performance_reproducibility_claimed"])

    def test_interpretation_is_not_pdp_validation_or_pricing(self):
        b = self.summary["interpretation_boundary"]
        self.assertTrue(b["reference_profile_not_population_average_pdp"])
        self.assertFalse(b["causal_interpretation_claimed"])
        self.assertFalse(b["validation_performance_evidence_created"])
        self.assertFalse(b["candidate_selection_allowed"])
        self.assertFalse(b["model_promotion_evidence_created"])
        self.assertFalse(b["customer_pricing_authorised"])
        self.assertFalse(b["actual_premium_or_quote"])
        lower = b["interpretation"].lower()
        self.assertIn("not a population-average pdp", lower)
        self.assertIn("customer premium", lower)
        self.assertIn("model-promotion gate", lower)
        self.assertIn("not a population-average pdp, validation result, causal effect, customer premium or model-promotion gate", lower)

    def test_outputs_are_aggregate_reference_profiles_only(self):
        forbidden = {"insured_id", "total_claims", "total_exposure", "total_premium", "total_incurred"}
        self.assertTrue(forbidden.isdisjoint(self.numeric.columns))
        self.assertTrue(forbidden.isdisjoint(self.categorical.columns))
        self.assertFalse(self.summary["persisted_row_level_data"])


if __name__ == "__main__":
    unittest.main()
