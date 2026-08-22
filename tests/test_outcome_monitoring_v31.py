from __future__ import annotations

import unittest

import numpy as np

from deployment.outcome_monitoring import (
    deterministic_exposure_maturity_mask,
    outcome_performance_snapshot,
    segment_calibration_snapshot,
)


class OutcomeMonitoringV31Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.exposure = np.array([1.0, 1.0, 1.0, 1.0])
        self.claims = np.array([0.0, 1.0, 0.0, 1.0])
        self.incurred = np.array([0.0, 100.0, 0.0, 200.0])
        self.predictions = {
            "reference_frequency": np.array([0.20, 0.30, 0.25, 0.35]),
            "challenger_frequency": np.array([0.18, 0.34, 0.22, 0.40]),
            "reference_pure_premium": np.array([40.0, 60.0, 55.0, 90.0]),
            "challenger_pure_premium": np.array([35.0, 70.0, 50.0, 110.0]),
        }

    def test_deterministic_maturity_mask_reaches_target(self) -> None:
        keys = ["a", "b", "c", "d"]
        first = deterministic_exposure_maturity_mask(
            keys, self.exposure, target_exposure_fraction=0.50
        )
        second = deterministic_exposure_maturity_mask(
            keys, self.exposure, target_exposure_fraction=0.50
        )
        self.assertTrue(np.array_equal(first, second))
        self.assertGreaterEqual(float(self.exposure[first].sum() / self.exposure.sum()), 0.50)
        self.assertLessEqual(int(first.sum()), 3)

    def test_immature_outcomes_withhold_metrics(self) -> None:
        report = outcome_performance_snapshot(
            self.claims,
            self.incurred,
            self.exposure,
            self.predictions,
            np.array([True, True, False, False]),
            minimum_mature_exposure_fraction=0.75,
        )
        self.assertEqual(report["status"], "WAIT_FOR_OUTCOME_MATURITY")
        self.assertFalse(report["metrics_evaluated"])
        self.assertNotIn("frequency", report)
        self.assertFalse(report["model_promotion_authorised"])
        self.assertFalse(report["pricing_change_authorised"])

    def test_mature_outcomes_evaluate_reference_and_challenger(self) -> None:
        report = outcome_performance_snapshot(
            self.claims,
            self.incurred,
            self.exposure,
            self.predictions,
            np.ones(4, dtype=bool),
            minimum_mature_exposure_fraction=0.95,
        )
        self.assertEqual(report["status"], "OUTCOME_PERFORMANCE_EVALUATED")
        self.assertTrue(report["metrics_evaluated"])
        self.assertIn("reference", report["frequency"])
        self.assertIn("challenger", report["frequency"])
        self.assertIn("reference", report["pure_premium"])
        self.assertIn("challenger", report["pure_premium"])
        self.assertFalse(report["model_promotion_authorised"])
        self.assertFalse(report["pricing_change_authorised"])

    def test_segment_calibration_is_aggregate_only(self) -> None:
        rows = segment_calibration_snapshot(
            ["NB", "NB", "P", "P"],
            self.claims,
            self.incurred,
            self.exposure,
            self.predictions,
            np.ones(4, dtype=bool),
        )
        self.assertEqual([row["segment"] for row in rows], ["NB", "P"])
        for row in rows:
            self.assertNotIn("insured_id", row)
            self.assertIn("reference_frequency_calibration_ratio", row)
            self.assertIn("challenger_pure_premium_calibration_ratio", row)

    def test_segment_metrics_are_suppressed_before_maturity(self) -> None:
        rows = segment_calibration_snapshot(
            ["NB", "NB", "P", "P"],
            self.claims,
            self.incurred,
            self.exposure,
            self.predictions,
            np.array([True, False, False, False]),
            minimum_mature_exposure_fraction=0.95,
        )
        self.assertEqual(rows, [])

    def test_invalid_target_fraction_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            deterministic_exposure_maturity_mask(
                ["a", "b"], [1.0, 1.0], target_exposure_fraction=0.0
            )


if __name__ == "__main__":
    unittest.main()
