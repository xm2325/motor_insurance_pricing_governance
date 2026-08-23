from __future__ import annotations

import unittest

import numpy as np

from run_frequency_recalibration_transport_v33 import evaluate_cohorts


class FrequencyRecalibrationTransportV33Tests(unittest.TestCase):
    @staticmethod
    def dimensions(n: int, label: str = "A") -> dict[str, np.ndarray]:
        values = np.asarray([label] * n, dtype=object)
        return {
            "seen_before_2024": values.copy(),
            "driver_age_band": values.copy(),
            "policy_type": values.copy(),
            "payment_frequency": values.copy(),
        }

    def test_major_cohort_improvement_passes(self) -> None:
        n = 3000
        claims = np.ones(n)
        exposure = np.ones(n)
        baseline = np.full(n, 0.90)
        candidate = np.full(n, 0.98)
        rows = evaluate_cohorts(
            self.dimensions(n), claims, exposure, baseline, candidate
        )
        self.assertEqual(len(rows), 4)
        for row in rows:
            self.assertTrue(row["major_cohort"])
            self.assertLess(row["abs_log_calibration_error_change"], 0.0)
            self.assertLess(row["relative_deviance_change"], 0.0)
            self.assertTrue(row["cohort_gate_pass"])

    def test_material_calibration_deterioration_fails_major_cohort(self) -> None:
        n = 3000
        claims = np.ones(n)
        exposure = np.ones(n)
        baseline = np.full(n, 1.0)
        candidate = np.full(n, 1.05)
        rows = evaluate_cohorts(
            self.dimensions(n), claims, exposure, baseline, candidate
        )
        for row in rows:
            self.assertTrue(row["major_cohort"])
            self.assertGreater(row["abs_log_calibration_error_change"], 0.02)
            self.assertFalse(row["calibration_guardrail_pass"])
            self.assertFalse(row["cohort_gate_pass"])

    def test_small_cohort_is_reported_but_not_gated(self) -> None:
        n = 100
        claims = np.ones(n)
        exposure = np.ones(n)
        baseline = np.full(n, 1.0)
        candidate = np.full(n, 1.5)
        rows = evaluate_cohorts(
            self.dimensions(n), claims, exposure, baseline, candidate
        )
        for row in rows:
            self.assertFalse(row["major_cohort"])
            self.assertTrue(row["calibration_guardrail_pass"])
            self.assertTrue(row["deviance_guardrail_pass"])
            self.assertTrue(row["cohort_gate_pass"])

    def test_dimension_length_mismatch_is_rejected(self) -> None:
        dimensions = self.dimensions(10)
        dimensions["policy_type"] = np.asarray(["A"] * 9, dtype=object)
        with self.assertRaises(ValueError):
            evaluate_cohorts(
                dimensions,
                np.ones(10),
                np.ones(10),
                np.ones(10),
                np.ones(10),
            )

    def test_nonpositive_exposure_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            evaluate_cohorts(
                self.dimensions(3),
                np.ones(3),
                np.asarray([1.0, 0.0, 1.0]),
                np.ones(3),
                np.ones(3),
            )


if __name__ == "__main__":
    unittest.main()
