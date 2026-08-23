from __future__ import annotations

import csv
import json
import math
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "action_results" / "v33"
SUMMARY = RESULT_DIR / "frequency_recalibration_transport_summary.json"
COHORTS = RESULT_DIR / "frequency_recalibration_transport_cohorts.csv"
STATUS = RESULT_DIR / "ACTION_V33_STATUS.json"

EXPECTED_FIELDS = {"reference_frequency", "challenger_frequency"}
EXPECTED_DIMENSIONS = {
    "seen_before_2024",
    "driver_age_band",
    "policy_type",
    "payment_frequency",
}


class FrequencyRecalibrationTransportEvidenceV33Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
        cls.status = json.loads(STATUS.read_text(encoding="utf-8"))
        with COHORTS.open(newline="", encoding="utf-8") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_main_workflow_status_is_success(self) -> None:
        self.assertEqual(
            self.status["workflow"],
            "Motor pricing frequency recalibration transport review v0.33",
        )
        self.assertEqual(self.status["run_id"], "32631177544")
        self.assertEqual(
            self.status["sha"],
            "3f1c473c9d13d000e2f3143652f112e805f2e6a4",
        )
        self.assertEqual(self.status["status"], "success")

    def test_source_boundary_and_fixed_factor_contract(self) -> None:
        source = self.summary["source"]
        self.assertEqual(self.summary["status"], "V33_FREQUENCY_RECALIBRATION_TRANSPORT_REVIEW_PASS")
        self.assertEqual(source["dataset"], "Mendeley sw4jmdb2sm v1")
        self.assertEqual(source["evaluation_year"], 2024)
        self.assertEqual(source["rows"], 168085)
        self.assertFalse(source["multipliers_refit_in_v33"])
        self.assertFalse(source["2024_labels_used_for_fit"])
        self.assertEqual(set(source["transport_dimensions"]), EXPECTED_DIMENSIONS)
        self.assertNotIn("business_type", source["transport_dimensions"])

    def test_guardrails_remain_pre_registered_project_rules(self) -> None:
        guardrails = self.summary["guardrails"]
        self.assertEqual(guardrails["major_cohort_min_rows"], 2000)
        self.assertTrue(math.isclose(guardrails["major_cohort_min_exposure_share"], 0.02))
        self.assertEqual(guardrails["major_cohort_min_claims"], 100)
        self.assertTrue(math.isclose(guardrails["max_abs_log_calibration_deterioration"], 0.02))
        self.assertTrue(math.isclose(guardrails["max_relative_deviance_worsening"], 0.005))
        self.assertIn("not insurer or regulatory thresholds", guardrails["interpretation"])

    def test_both_frequency_fields_are_transport_stable(self) -> None:
        models = self.summary["models"]
        self.assertEqual(set(models), EXPECTED_FIELDS)
        expected = {
            "reference_frequency": {
                "calibration_improved_count": 8,
                "deviance_improved_count": 10,
                "max_calibration_deterioration": 0.010991523024598243,
                "max_deviance_worsening": 0.0012227945145166785,
            },
            "challenger_frequency": {
                "calibration_improved_count": 9,
                "deviance_improved_count": 10,
                "max_calibration_deterioration": 0.014693424591201112,
                "max_deviance_worsening": 0.0013131938559480805,
            },
        }
        for field, values in expected.items():
            model = models[field]
            self.assertEqual(model["v32_candidate_source"]["fit_year"], 2023)
            self.assertFalse(model["v32_candidate_source"]["test_2024_labels_used_for_fit"])
            self.assertEqual(model["v32_candidate_source"]["v32_decision"], "SUPPORTED_FOR_FURTHER_SHADOW_TESTING")
            replay = model["fresh_replay_reconciliation"]
            self.assertLessEqual(replay["max_relative_difference"], 1e-8)
            self.assertLessEqual(replay["max_relative_difference"], replay["relative_tolerance"])
            summary = model["major_cohort_summary"]
            self.assertEqual(summary["major_cohort_count"], 13)
            self.assertEqual(summary["gate_breach_count"], 0)
            self.assertEqual(summary["calibration_improved_count"], values["calibration_improved_count"])
            self.assertEqual(summary["deviance_improved_count"], values["deviance_improved_count"])
            self.assertTrue(
                math.isclose(
                    summary["max_abs_log_calibration_deterioration"],
                    values["max_calibration_deterioration"],
                    rel_tol=0.0,
                    abs_tol=1e-9,
                )
            )
            self.assertTrue(
                math.isclose(
                    summary["max_relative_deviance_worsening"],
                    values["max_deviance_worsening"],
                    rel_tol=0.0,
                    abs_tol=1e-9,
                )
            )
            self.assertEqual(summary["decision"], "TRANSPORT_STABLE_FOR_FURTHER_SHADOW_TESTING")
            self.assertEqual(model["breaches"], [])

    def test_persisted_cohort_csv_has_no_major_breach_or_identifier(self) -> None:
        self.assertTrue(self.rows)
        columns = set(self.rows[0])
        for forbidden in ("insured_id", "customer_id", "policy_id"):
            self.assertNotIn(forbidden, columns)
        self.assertEqual({row["prediction_field"] for row in self.rows}, EXPECTED_FIELDS)
        self.assertEqual({row["dimension"] for row in self.rows}, EXPECTED_DIMENSIONS)
        self.assertNotIn("business_type", {row["dimension"] for row in self.rows})

        for field in EXPECTED_FIELDS:
            major = [
                row
                for row in self.rows
                if row["prediction_field"] == field and row["major_cohort"] == "True"
            ]
            self.assertEqual(len(major), 13)
            self.assertTrue(all(row["cohort_gate_pass"] == "True" for row in major))

    def test_seen_and_unseen_calibration_both_improve(self) -> None:
        for field in EXPECTED_FIELDS:
            seen_rows = [
                row
                for row in self.rows
                if row["prediction_field"] == field
                and row["dimension"] == "seen_before_2024"
                and row["group"] in {"seen", "unseen"}
            ]
            self.assertEqual({row["group"] for row in seen_rows}, {"seen", "unseen"})
            self.assertTrue(
                all(float(row["abs_log_calibration_error_change"]) < 0.0 for row in seen_rows)
            )

    def test_worst_observed_tradeoffs_are_retained_not_hidden(self) -> None:
        for field in EXPECTED_FIELDS:
            major = [
                row
                for row in self.rows
                if row["prediction_field"] == field and row["major_cohort"] == "True"
            ]
            worst_calibration = max(major, key=lambda row: float(row["abs_log_calibration_error_change"]))
            worst_deviance = max(major, key=lambda row: float(row["relative_deviance_change"]))
            self.assertEqual((worst_calibration["dimension"], worst_calibration["group"]), ("payment_frequency", "Q"))
            self.assertEqual((worst_deviance["dimension"], worst_deviance["group"]), ("policy_type", "TPG"))
            self.assertLessEqual(float(worst_calibration["abs_log_calibration_error_change"]), 0.02)
            self.assertLessEqual(float(worst_deviance["relative_deviance_change"]), 0.005)

    def test_governance_remains_hold_shadow_only(self) -> None:
        decision = self.summary["decision"]
        self.assertEqual(set(decision["stable_fields"]), EXPECTED_FIELDS)
        self.assertEqual(decision["stable_field_count"], 2)
        self.assertEqual(decision["tested_field_count"], 2)
        self.assertFalse(decision["bundle_change_authorised"])
        self.assertFalse(decision["pricing_change_authorised"])
        self.assertFalse(decision["model_promotion_authorised"])
        self.assertEqual(decision["model_family_decision"], "HOLD")
        self.assertEqual(decision["serving_status"], "HOLD_SHADOW_ONLY")


if __name__ == "__main__":
    unittest.main()
