from __future__ import annotations

import unittest

import numpy as np
from sklearn.metrics import mean_poisson_deviance

from deployment.calibration_uncertainty import (
    evaluate_segment_factor_draw,
    group_frequency_sufficient_statistics,
    paired_stratified_bootstrap_factors,
    quantile_summary,
)


class FrequencyRecalibrationUncertaintyV34Tests(unittest.TestCase):
    def test_sufficient_statistic_deviance_matches_direct_sklearn(self) -> None:
        segment = np.asarray(["NB", "NB", "P", "P", "P"], dtype=object)
        claims = np.asarray([0.0, 2.0, 1.0, 0.0, 3.0])
        exposure = np.asarray([0.5, 1.0, 1.0, 0.75, 1.0])
        baseline = np.asarray([0.8, 1.1, 0.9, 1.3, 1.5])
        factors = {"NB": 0.92, "P": 1.08}
        candidate = baseline * np.where(segment == "NB", factors["NB"], factors["P"])

        baseline_dev = mean_poisson_deviance(claims / exposure, baseline, sample_weight=exposure)
        direct_candidate = mean_poisson_deviance(claims / exposure, candidate, sample_weight=exposure)
        stats = group_frequency_sufficient_statistics(segment, claims, exposure, baseline)
        evaluated = evaluate_segment_factor_draw(
            baseline_poisson_deviance=float(baseline_dev),
            group_stats=stats,
            factors=factors,
        )
        self.assertAlmostEqual(evaluated["poisson_deviance"], direct_candidate, places=13)
        self.assertAlmostEqual(
            evaluated["aggregate_calibration_ratio_pred_over_actual"],
            float(np.sum(candidate * exposure) / claims.sum()),
            places=13,
        )

    def test_bootstrap_factors_are_deterministic_and_paired(self) -> None:
        segment = np.asarray(["NB"] * 6 + ["P"] * 6, dtype=object)
        claims = np.asarray([0, 1, 0, 2, 1, 0, 1, 0, 2, 1, 0, 1], dtype=float)
        exposure = np.ones(len(segment), dtype=float)
        pred_a = np.asarray([0.5, 0.7, 0.6, 0.8, 0.7, 0.6, 0.7, 0.8, 0.9, 0.7, 0.8, 0.9])
        pred_b = pred_a * 2.0
        first = paired_stratified_bootstrap_factors(
            segment,
            claims,
            exposure,
            {"a": pred_a, "b": pred_b},
            draws=20,
            seed=123,
        )
        second = paired_stratified_bootstrap_factors(
            segment,
            claims,
            exposure,
            {"a": pred_a, "b": pred_b},
            draws=20,
            seed=123,
        )
        for group in ("NB", "P"):
            np.testing.assert_allclose(first["a"][group], second["a"][group], rtol=0.0, atol=0.0)
            np.testing.assert_allclose(first["b"][group], first["a"][group] / 2.0, rtol=1e-13, atol=1e-13)

    def test_bootstrap_factors_are_not_clipped(self) -> None:
        segment = np.asarray(["NB"] * 4 + ["P"] * 4, dtype=object)
        claims = np.asarray([5, 5, 5, 5, 1, 1, 1, 1], dtype=float)
        exposure = np.ones(8, dtype=float)
        predictions = np.asarray([1.0] * 4 + [4.0] * 4)
        draws = paired_stratified_bootstrap_factors(
            segment,
            claims,
            exposure,
            {"reference_frequency": predictions},
            draws=5,
            seed=7,
        )
        self.assertTrue(np.all(draws["reference_frequency"]["NB"] > 2.0))
        self.assertTrue(np.all(draws["reference_frequency"]["P"] < 0.5))

    def test_quantile_summary_orders_interval(self) -> None:
        summary = quantile_summary([1, 2, 3, 4, 5])
        self.assertLess(summary["q025"], summary["median"])
        self.assertLess(summary["median"], summary["q975"])

    def test_invalid_factor_is_rejected(self) -> None:
        stats = {"NB": {"rows": 1, "claims": 1.0, "exposure": 1.0, "baseline_expected_claims": 1.0}}
        with self.assertRaises(ValueError):
            evaluate_segment_factor_draw(
                baseline_poisson_deviance=1.0,
                group_stats=stats,
                factors={"NB": 0.0},
            )


if __name__ == "__main__":
    unittest.main()
