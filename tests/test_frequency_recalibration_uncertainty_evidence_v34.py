from __future__ import annotations

import csv
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "action_results" / "v34"
SUMMARY = RESULT_DIR / "frequency_recalibration_uncertainty_summary.json"
FACTORS = RESULT_DIR / "frequency_recalibration_factor_bootstrap_summary.csv"
STATUS = RESULT_DIR / "ACTION_V34_STATUS.json"
DETAILED_DRAWS = RESULT_DIR / "frequency_recalibration_bootstrap_metrics.csv"


class FrequencyRecalibrationUncertaintyEvidenceV34Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))
        with FACTORS.open(newline="", encoding="utf-8") as handle:
            cls.factor_rows = list(csv.DictReader(handle))

    def test_main_workflow_status_is_success(self) -> None:
        self.assertEqual(
            self.status["workflow"],
            "Motor pricing recalibration factor uncertainty v0.34",
        )
        self.assertEqual(self.status["run_id"], "32632003226")
        self.assertEqual(
            self.status["sha"],
            "17e4c79e5080e05a011d7a7aaab9a50e81d95064",
        )
        self.assertEqual(self.status["status"], "success")

    def test_registered_sampling_boundary_is_persisted(self) -> None:
        source = self.summary["source"]
        self.assertEqual(self.summary["status"], "V34_RECALIBRATION_FACTOR_UNCERTAINTY_REVIEW_PASS")
        self.assertEqual(source["dataset"], "Mendeley sw4jmdb2sm v1")
        self.assertEqual(source["factor_bootstrap_year"], 2023)
        self.assertEqual(source["evaluation_year"], 2024)
        self.assertEqual(source["calibration_rows"], 118835)
        self.assertEqual(source["evaluation_rows"], 168085)
        self.assertEqual(source["bootstrap_draws"], 500)
        self.assertEqual(source["bootstrap_seed"], 20260823)
        self.assertEqual(source["bootstrap_stratified_by"], "business_type")
        self.assertTrue(source["paired_indices_across_frequency_fields"])
        self.assertFalse(source["2024_labels_used_for_bootstrap_factor_fit"])
        self.assertFalse(source["factor_draws_are_clipped"])

    def test_registered_gate_is_not_relaxed_after_result(self) -> None:
        gate = self.summary["registered_robustness_gate"]
        self.assertEqual(gate["factor_draw_guardrails"], [0.5, 2.0])
        self.assertTrue(math.isclose(gate["minimum_deviance_improvement_rate"], 0.8))
        self.assertTrue(math.isclose(gate["minimum_aggregate_calibration_nonworse_rate"], 0.8))
        self.assertTrue(math.isclose(gate["minimum_worst_segment_calibration_improvement_rate"], 0.8))
        self.assertTrue(math.isclose(gate["minimum_original_v32_deviance_guardrail_pass_rate"], 0.95))
        self.assertTrue(math.isclose(gate["original_v32_max_relative_deviance_worsening"], 0.001))
        self.assertTrue(math.isclose(gate["fresh_retrain_relative_tolerance"], 0.002))
        self.assertIn("not insurer or regulatory thresholds", gate["threshold_boundary"])

    def test_glm_narrow_failure_is_preserved(self) -> None:
        glm = self.summary["models"]["reference_frequency"]
        rates = glm["robustness_rates"]
        self.assertTrue(math.isclose(rates["deviance_improvement_rate"], 0.97))
        self.assertTrue(math.isclose(rates["aggregate_calibration_not_worse_rate"], 0.796))
        self.assertTrue(math.isclose(rates["worst_segment_calibration_improvement_rate"], 0.994))
        self.assertTrue(math.isclose(rates["original_v32_deviance_guardrail_pass_rate"], 1.0))
        self.assertLess(rates["aggregate_calibration_not_worse_rate"], 0.8)
        self.assertEqual(
            glm["strong_robustness_gate"]["decision"],
            "FACTOR_UNCERTAINTY_REVIEW_REQUIRED",
        )
        self.assertTrue(glm["strong_robustness_gate"]["factor_interval_direction_stable"])
        self.assertTrue(glm["strong_robustness_gate"]["all_factor_draws_within_guardrails"])

    def test_xgb_strong_pass_is_preserved(self) -> None:
        xgb = self.summary["models"]["challenger_frequency"]
        rates = xgb["robustness_rates"]
        self.assertTrue(math.isclose(rates["deviance_improvement_rate"], 0.998))
        self.assertTrue(math.isclose(rates["aggregate_calibration_not_worse_rate"], 0.848))
        self.assertTrue(math.isclose(rates["worst_segment_calibration_improvement_rate"], 1.0))
        self.assertTrue(math.isclose(rates["original_v32_deviance_guardrail_pass_rate"], 1.0))
        self.assertEqual(
            xgb["strong_robustness_gate"]["decision"],
            "ROBUST_TO_2023_FACTOR_ESTIMATION_FOR_FURTHER_SHADOW_TESTING",
        )
        self.assertTrue(xgb["strong_robustness_gate"]["factor_interval_direction_stable"])
        self.assertTrue(xgb["strong_robustness_gate"]["all_factor_draws_within_guardrails"])

    def test_factor_intervals_retain_direction_and_unclipped_extrema(self) -> None:
        self.assertEqual(len(self.factor_rows), 4)
        expected = {
            ("reference_frequency", "NB"): (0.9558040125937721, 0.9967883380164237, 0.9426306126260621, 1.0065119190084681),
            ("reference_frequency", "P"): (1.0049083206418696, 1.0634076432628412, 0.9959271376107106, 1.0916056141136734),
            ("challenger_frequency", "NB"): (0.9490492396405257, 0.9898801073101873, 0.9346874461036981, 1.0010706265662228),
            ("challenger_frequency", "P"): (1.0154647063057047, 1.0748192518146553, 1.0059206803589462, 1.1044209913845133),
        }
        for row in self.factor_rows:
            key = (row["prediction_field"], row["segment"])
            self.assertIn(key, expected)
            q025, q975, minimum, maximum = expected[key]
            self.assertTrue(math.isclose(float(row["q025"]), q025, rel_tol=0.0, abs_tol=1e-15))
            self.assertTrue(math.isclose(float(row["q975"]), q975, rel_tol=0.0, abs_tol=1e-15))
            self.assertTrue(math.isclose(float(row["min_draw"]), minimum, rel_tol=0.0, abs_tol=1e-15))
            self.assertTrue(math.isclose(float(row["max_draw"]), maximum, rel_tol=0.0, abs_tol=1e-15))
            self.assertEqual(row["interval_crosses_one"], "False")
            self.assertEqual(row["all_draws_within_factor_guardrails"], "True")

    def test_fresh_retrain_reconciliation_is_tolerance_based_not_same_fit_claim(self) -> None:
        for field in ("reference_frequency", "challenger_frequency"):
            model = self.summary["models"][field]
            factor_rec = model["factor_reconciliation"]
            metric_rec = model["fresh_v32_metric_reconciliation"]
            self.assertLessEqual(factor_rec["max_relative_difference"], factor_rec["relative_tolerance"])
            self.assertLessEqual(metric_rec["max_relative_difference"], metric_rec["relative_tolerance"])
        self.assertGreater(
            self.summary["models"]["reference_frequency"]["fresh_v32_metric_reconciliation"]["max_relative_difference"],
            0.0,
        )

    def test_persisted_evidence_is_aggregate_only(self) -> None:
        self.assertFalse(DETAILED_DRAWS.exists())
        factor_columns = set(self.factor_rows[0])
        for forbidden in ("insured_id", "policy_id", "customer_id"):
            self.assertNotIn(forbidden, factor_columns)

    def test_governance_remains_hold_shadow_only(self) -> None:
        decision = self.summary["decision"]
        self.assertEqual(decision["robust_fields"], ["challenger_frequency"])
        self.assertEqual(decision["robust_field_count"], 1)
        self.assertEqual(decision["tested_field_count"], 2)
        self.assertFalse(decision["bundle_change_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")


if __name__ == "__main__":
    unittest.main()
