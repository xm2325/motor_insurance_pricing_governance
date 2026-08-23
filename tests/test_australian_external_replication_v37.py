from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from external_validation.replication import (
    aggregate_calibration,
    deterministic_split_indices,
    evaluate_replication_gate,
    multiplicative_calibration_scale,
    paired_bootstrap_relative_improvement,
    poisson_deviance,
    top_exposure_capture,
)
from validate_external_validation_prereg_v36 import canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "governance" / "external_validation_prereg_v36.json"
LOCK = ROOT / "action_results" / "v36" / "external_validation_prereg_lock.json"
STATUS = ROOT / "action_results" / "v36" / "ACTION_V36_STATUS.json"
RUNNER = ROOT / "run_australian_external_replication_v37.py"
EXPECTED_DIGEST = "b20d38b51f767761fe4b4f85d58988f7032dbcc7d7afc96041f3858c0165e3c1"


class AustralianExternalReplicationV37Tests(unittest.TestCase):
    def test_v36_preregistration_is_main_locked_before_execution(self) -> None:
        prereg = json.loads(PREREG.read_text(encoding="utf-8"))
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        status = json.loads(STATUS.read_text(encoding="utf-8"))
        self.assertEqual(canonical_sha256(prereg), EXPECTED_DIGEST)
        self.assertEqual(lock["preregistration_sha256"], EXPECTED_DIGEST)
        self.assertEqual(status["sha"], "49339232a6b913e111b6e4e66dfa4517d9396bc9")
        self.assertEqual(status["status"], "success")
        self.assertFalse(status["row_level_external_data_accessed"])

    def test_registered_split_counts_are_deterministic(self) -> None:
        first = deterministic_split_indices(
            67856, seed=20260823, train_fraction=0.60, calibration_fraction=0.20
        )
        second = deterministic_split_indices(
            67856, seed=20260823, train_fraction=0.60, calibration_fraction=0.20
        )
        self.assertEqual((len(first["train"]), len(first["calibration"]), len(first["test"])), (40713, 13571, 13572))
        for key in first:
            np.testing.assert_array_equal(first[key], second[key])
        all_rows = np.concatenate([first["train"], first["calibration"], first["test"]])
        self.assertEqual(len(np.unique(all_rows)), 67856)

    def test_calibration_scale_and_aggregate_ratio(self) -> None:
        observed = np.asarray([1.0, 0.0, 2.0])
        exposure = np.asarray([1.0, 0.5, 1.5])
        predicted = np.asarray([0.5, 0.5, 0.5])
        scale = multiplicative_calibration_scale(observed, predicted, exposure)
        calibrated = predicted * scale
        summary = aggregate_calibration(observed, calibrated, exposure)
        self.assertAlmostEqual(summary["calibration_ratio_pred_over_actual"], 1.0, places=14)

    def test_top_exposure_capture_fractionally_allocates_boundary(self) -> None:
        observed = np.asarray([10.0, 0.0])
        predicted = np.asarray([2.0, 1.0])
        exposure = np.asarray([0.2, 0.8])
        capture = top_exposure_capture(observed, predicted, exposure, fraction=0.10)
        self.assertAlmostEqual(capture, 0.5, places=14)

    def test_paired_bootstrap_is_seeded_and_uses_same_rows(self) -> None:
        observed = np.asarray([0.0, 1.0, 0.0, 2.0, 1.0, 0.0])
        exposure = np.ones(6)
        reference = np.asarray([0.3, 0.4, 0.5, 0.6, 0.5, 0.4])
        challenger = reference * 0.98
        first = paired_bootstrap_relative_improvement(
            observed,
            reference,
            challenger,
            exposure,
            metric=poisson_deviance,
            draws=25,
            seed=20260824,
        )
        second = paired_bootstrap_relative_improvement(
            observed,
            reference,
            challenger,
            exposure,
            metric=poisson_deviance,
            draws=25,
            seed=20260824,
        )
        np.testing.assert_allclose(first, second, rtol=0.0, atol=0.0)

    def test_registered_gate_requires_all_three_evidence_checks(self) -> None:
        passed = evaluate_replication_gate(
            reference_deviance=1.0,
            challenger_deviance=0.99,
            reference_abs_log_calibration_error=0.02,
            challenger_abs_log_calibration_error=0.025,
            bootstrap_interval={"q025": 0.001, "median": 0.01, "q975": 0.02},
            minimum_relative_deviance_improvement=0.005,
            bootstrap_ci_lower_bound_must_exceed=0.0,
            maximum_additional_abs_log_calibration_error=0.01,
            calibration_scales_valid=True,
            pass_label="PASS",
            fail_label="FAIL",
        )
        self.assertTrue(passed["passed"])
        failed = evaluate_replication_gate(
            reference_deviance=1.0,
            challenger_deviance=0.99,
            reference_abs_log_calibration_error=0.02,
            challenger_abs_log_calibration_error=0.025,
            bootstrap_interval={"q025": -0.001, "median": 0.01, "q975": 0.02},
            minimum_relative_deviance_improvement=0.005,
            bootstrap_ci_lower_bound_must_exceed=0.0,
            maximum_additional_abs_log_calibration_error=0.01,
            calibration_scales_valid=True,
            pass_label="PASS",
            fail_label="FAIL",
        )
        self.assertFalse(failed["passed"])
        self.assertEqual(failed["decision"], "FAIL")

    def test_execution_runner_uses_locked_protocol_not_new_gate_constants(self) -> None:
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_V36_PREREG_SHA256", source)
        self.assertIn("prereg[\"registered_external_replication_gate\"]", source)
        self.assertIn("prereg[\"models\"]", source)
        self.assertIn("prereg[\"paired_bootstrap\"]", source)
        self.assertNotIn("minimum_relative_deviance_improvement=0.005", source)
        self.assertNotIn("maximum_additional_abs_log_calibration_error=0.01", source)


if __name__ == "__main__":
    unittest.main()
