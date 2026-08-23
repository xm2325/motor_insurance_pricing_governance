from __future__ import annotations

import unittest

import numpy as np

from deployment.recalibration import (
    apply_segment_multipliers,
    fit_segment_multipliers,
    portfolio_mix_decomposition,
    segment_calibration_rows,
)


class BusinessTypeRecalibrationV32Tests(unittest.TestCase):
    def test_supported_segment_multipliers_recalibrate_fit_period(self) -> None:
        segment = ["NB", "NB", "P", "P"]
        actual = np.array([1.0, 1.0, 2.0, 2.0])
        exposure = np.ones(4)
        baseline = np.array([0.8, 0.8, 2.4, 2.4])

        fitted = fit_segment_multipliers(
            segment,
            actual,
            baseline,
            exposure,
            minimum_segment_rows=1,
            minimum_segment_exposure_share=0.10,
        )
        self.assertAlmostEqual(fitted["NB"]["locked_multiplier"], 1.25, places=12)
        self.assertAlmostEqual(fitted["P"]["locked_multiplier"], 1.0 / 1.2, places=12)
        candidate = apply_segment_multipliers(segment, baseline, fitted)

        rows = segment_calibration_rows(segment, actual, exposure, baseline, candidate)
        for row in rows:
            self.assertAlmostEqual(row["candidate_calibration_ratio"], 1.0, places=12)
            self.assertLess(
                row["candidate_abs_log_calibration_error"],
                row["baseline_abs_log_calibration_error"],
            )

    def test_unsupported_segment_falls_back_to_global_scale(self) -> None:
        fitted = fit_segment_multipliers(
            ["NB", "NB", "P"],
            [1.0, 1.0, 1.0],
            [0.5, 0.5, 0.5],
            [1.0, 1.0, 1.0],
            minimum_segment_rows=2,
            minimum_segment_exposure_share=0.10,
        )
        self.assertTrue(fitted["NB"]["supported"])
        self.assertFalse(fitted["P"]["supported"])
        self.assertEqual(fitted["P"]["locked_multiplier"], 1.0)
        self.assertEqual(fitted["P"]["fallback_reason"], "INSUFFICIENT_ROWS")

    def test_multiplier_guardrail_clips_extreme_fit(self) -> None:
        fitted = fit_segment_multipliers(
            ["NB", "NB"],
            [10.0, 10.0],
            [1.0, 1.0],
            [1.0, 1.0],
            minimum_segment_rows=1,
            minimum_segment_exposure_share=0.10,
            multiplier_floor=0.50,
            multiplier_cap=2.00,
        )
        self.assertTrue(fitted["NB"]["supported"])
        self.assertEqual(fitted["NB"]["locked_multiplier"], 2.0)
        self.assertTrue(fitted["NB"]["multiplier_was_clipped"])

    def test_unseen_evaluation_segment_uses_multiplier_one(self) -> None:
        fitted = {
            "NB": {"locked_multiplier": 1.2},
            "P": {"locked_multiplier": 0.8},
        }
        adjusted = apply_segment_multipliers(
            ["NB", "NEW", "P"],
            [1.0, 1.0, 1.0],
            fitted,
        )
        np.testing.assert_allclose(adjusted, [1.2, 1.0, 0.8], rtol=0.0, atol=0.0)

    def test_mix_decomposition_is_exact_on_log_ratio_scale(self) -> None:
        result = portfolio_mix_decomposition(
            calibration_segment=["NB", "NB", "P", "P"],
            calibration_actual=[1.0, 1.0, 3.0, 3.0],
            calibration_exposure=[1.0, 1.0, 1.0, 1.0],
            calibration_pred=[0.9, 0.9, 3.1, 3.1],
            test_segment=["NB", "NB", "NB", "P"],
            test_actual=[1.0, 1.0, 1.0, 3.5],
            test_exposure=[1.0, 1.0, 1.0, 1.0],
            test_pred=[0.95, 0.95, 0.95, 3.0],
        )
        self.assertAlmostEqual(result["shared_test_exposure_share"], 1.0, places=12)
        self.assertAlmostEqual(result["decomposition_residual"], 0.0, places=15)
        self.assertAlmostEqual(
            result["total_log_calibration_change"],
            result["portfolio_mix_log_component"]
            + result["within_segment_time_log_component"],
            places=15,
        )

    def test_invalid_exposure_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fit_segment_multipliers(
                ["NB"], [1.0], [1.0], [0.0], minimum_segment_rows=1
            )


if __name__ == "__main__":
    unittest.main()
