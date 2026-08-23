from __future__ import annotations

import csv
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY_PATH = ROOT / "action_results/v32/business_type_recalibration_summary.json"
MULTIPLIERS_PATH = ROOT / "action_results/v32/business_type_recalibration_multipliers.csv"
COMPARISON_PATH = ROOT / "action_results/v32/business_type_2024_candidate_comparison.csv"
DECOMPOSITION_PATH = ROOT / "action_results/v32/business_type_mix_decomposition.csv"
STATUS_PATH = ROOT / "action_results/v32/ACTION_V32_STATUS.json"


class BusinessTypeRecalibrationEvidenceV32Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
        cls.tables = {}
        for name, path in (
            ("multipliers", MULTIPLIERS_PATH),
            ("comparison", COMPARISON_PATH),
            ("decomposition", DECOMPOSITION_PATH),
        ):
            with path.open(newline="", encoding="utf-8") as handle:
                cls.tables[name] = list(csv.DictReader(handle))

    def test_workflow_persisted_success(self) -> None:
        self.assertEqual(self.status["status"], "success")
        self.assertEqual(
            self.status["workflow"],
            "Motor pricing business-type recalibration review v0.32",
        )
        self.assertEqual(len(self.status["sha"]), 40)
        self.assertTrue(str(self.status["run_id"]).isdigit())

    def test_fit_and_evaluation_periods_are_locked(self) -> None:
        source = self.summary["source"]
        self.assertEqual(self.summary["status"], "V32_BUSINESS_TYPE_RECALIBRATION_REVIEW_PASS")
        self.assertEqual(source["model_train_year"], 2022)
        self.assertEqual(source["global_calibration_year"], 2023)
        self.assertEqual(source["segment_recalibration_fit_year"], 2023)
        self.assertEqual(source["untouched_evaluation_year"], 2024)
        self.assertEqual(source["segment"], "business_type")
        self.assertEqual(source["calibration_rows"], 118835)
        self.assertEqual(source["evaluation_rows"], 168085)
        self.assertFalse(source["2024_labels_used_for_candidate_fit"])
        for result in self.summary["results"].values():
            self.assertEqual(result["fit_period"]["year"], 2023)
            self.assertFalse(result["fit_period"]["test_2024_labels_used_for_fit"])

    def test_candidate_support_is_frequency_only(self) -> None:
        candidates = self.summary["candidate_summary"]
        self.assertEqual(
            candidates["supported_fields"],
            ["reference_frequency", "challenger_frequency"],
        )
        self.assertEqual(candidates["supported_field_count"], 2)
        self.assertEqual(candidates["total_field_count"], 4)

        results = self.summary["results"]
        for field in ("reference_frequency", "challenger_frequency"):
            self.assertEqual(
                results[field]["candidate_gate"]["decision"],
                "SUPPORTED_FOR_FURTHER_SHADOW_TESTING",
            )
            self.assertTrue(results[field]["candidate_gate"]["segment_calibration_improved"])
            self.assertTrue(results[field]["candidate_gate"]["aggregate_calibration_not_worse"])
            self.assertTrue(results[field]["candidate_gate"]["deviance_guardrail_pass"])

        for field in ("reference_pure_premium", "challenger_pure_premium"):
            self.assertEqual(
                results[field]["candidate_gate"]["decision"],
                "RETAIN_GLOBAL_CALIBRATION",
            )

    def test_frequency_candidates_improve_registered_2024_metrics(self) -> None:
        results = self.summary["results"]
        expected = {
            "reference_frequency": {
                "baseline_deviance": 1.1185362628672493,
                "candidate_deviance": 1.1180907056053262,
                "baseline_calibration": 0.963088025952147,
                "candidate_calibration": 0.9704466803524903,
                "baseline_segment_error": 0.06573686352109095,
                "candidate_segment_error": 0.03114515859221435,
            },
            "challenger_frequency": {
                "baseline_deviance": 1.1188352761606644,
                "candidate_deviance": 1.1181190316026728,
                "baseline_calibration": 0.9600850351705676,
                "candidate_calibration": 0.9695617558874555,
                "baseline_segment_error": 0.07805071060984149,
                "candidate_segment_error": 0.033044114703298176,
            },
        }
        for field, values in expected.items():
            baseline = results[field]["baseline_2024"]
            candidate = results[field]["candidate_2024"]
            self.assertAlmostEqual(baseline["deviance"], values["baseline_deviance"], places=12)
            self.assertAlmostEqual(candidate["deviance"], values["candidate_deviance"], places=12)
            self.assertAlmostEqual(
                baseline["calibration_ratio_pred_over_actual"],
                values["baseline_calibration"],
                places=12,
            )
            self.assertAlmostEqual(
                candidate["calibration_ratio_pred_over_actual"],
                values["candidate_calibration"],
                places=12,
            )
            self.assertAlmostEqual(
                baseline["max_segment_abs_log_calibration_error"],
                values["baseline_segment_error"],
                places=12,
            )
            self.assertAlmostEqual(
                candidate["max_segment_abs_log_calibration_error"],
                values["candidate_segment_error"],
                places=12,
            )
            self.assertLess(candidate["deviance"], baseline["deviance"])
            self.assertLess(
                abs(math.log(candidate["calibration_ratio_pred_over_actual"])),
                abs(math.log(baseline["calibration_ratio_pred_over_actual"])),
            )

    def test_pure_premium_candidates_fail_for_registered_reasons(self) -> None:
        results = self.summary["results"]
        glm = results["reference_pure_premium"]
        xgb = results["challenger_pure_premium"]

        self.assertTrue(glm["candidate_gate"]["segment_calibration_improved"])
        self.assertFalse(glm["candidate_gate"]["aggregate_calibration_not_worse"])
        self.assertLess(glm["candidate_2024"]["deviance"], glm["baseline_2024"]["deviance"])
        self.assertGreater(
            abs(math.log(glm["candidate_2024"]["calibration_ratio_pred_over_actual"])),
            abs(math.log(glm["baseline_2024"]["calibration_ratio_pred_over_actual"])),
        )

        self.assertFalse(xgb["candidate_gate"]["segment_calibration_improved"])
        self.assertTrue(xgb["candidate_gate"]["aggregate_calibration_not_worse"])
        self.assertGreater(
            xgb["candidate_2024"]["max_segment_abs_log_calibration_error"],
            xgb["baseline_2024"]["max_segment_abs_log_calibration_error"],
        )

    def test_locked_multipliers_are_supported_and_bounded(self) -> None:
        self.assertEqual(len(self.tables["multipliers"]), 8)
        for row in self.tables["multipliers"]:
            self.assertIn(row["prediction_field"], self.summary["results"])
            self.assertIn(row["segment"], {"NB", "P"})
            self.assertEqual(row["supported"], "True")
            multiplier = float(row["locked_multiplier"])
            self.assertGreaterEqual(multiplier, 0.5)
            self.assertLessEqual(multiplier, 2.0)
            self.assertEqual(row["multiplier_was_clipped"], "False")

    def test_mix_decomposition_is_exact_and_not_policy_level(self) -> None:
        self.assertEqual(len(self.tables["decomposition"]), 4)
        for row in self.tables["decomposition"]:
            total = float(row["total_log_calibration_change"])
            mix = float(row["portfolio_mix_log_component"])
            within = float(row["within_segment_time_log_component"])
            residual = float(row["decomposition_residual"])
            self.assertAlmostEqual(total, mix + within, places=14)
            self.assertAlmostEqual(residual, 0.0, places=14)
            self.assertAlmostEqual(float(row["shared_test_exposure_share"]), 1.0, places=12)

        forbidden = {"insured_id", "policy_id", "quote_id", "customer_id"}
        for table in self.tables.values():
            self.assertTrue(forbidden.isdisjoint(table[0].keys()))

        glm_loss = self.summary["results"]["reference_pure_premium"]["portfolio_mix_decomposition"]
        self.assertGreater(glm_loss["portfolio_mix_log_component"], 0.0)
        self.assertLess(glm_loss["within_segment_time_log_component"], 0.0)
        self.assertLess(glm_loss["test_period_ratio"], 1.0)

    def test_v31_baseline_reconciliation_and_governance_hold(self) -> None:
        reconciliation = self.summary["v31_baseline_reconciliation"]
        self.assertEqual(reconciliation["status"], "V31_BASELINE_RECONCILIATION_PASS")
        self.assertEqual(len(reconciliation["checks"]), 4)
        self.assertAlmostEqual(reconciliation["max_relative_difference"], 0.0, places=15)
        self.assertAlmostEqual(reconciliation["relative_tolerance"], 0.002, places=12)

        candidates = self.summary["candidate_summary"]
        self.assertFalse(candidates["bundle_change_authorised"])
        self.assertFalse(candidates["pricing_change_authorised"])
        self.assertFalse(candidates["model_promotion_authorised"])
        self.assertEqual(candidates["model_family_decision"], "HOLD")
        self.assertEqual(candidates["serving_status"], "HOLD_SHADOW_ONLY")


if __name__ == "__main__":
    unittest.main()
