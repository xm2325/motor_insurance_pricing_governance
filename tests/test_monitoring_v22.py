from __future__ import annotations

import unittest

from deployment.monitoring import ShadowTelemetry


class TestShadowTelemetry(unittest.TestCase):
    def test_snapshot_contains_aggregates_only(self) -> None:
        telemetry = ShadowTelemetry()
        telemetry.record_request(12.5)
        telemetry.record_scores([
            {
                "frequency_log_ratio": 0.2,
                "pure_premium_log_ratio": -0.3,
                "warnings": [],
            },
            {
                "frequency_log_ratio": -0.1,
                "pure_premium_log_ratio": 0.4,
                "warnings": ["unseen_category:vehicle_brand=NEW"],
            },
        ])
        snapshot = telemetry.snapshot()
        self.assertEqual(snapshot["privacy_boundary"], "aggregate_non_pii_only")
        self.assertEqual(snapshot["request_count"], 1)
        self.assertEqual(snapshot["records_scored"], 2)
        self.assertAlmostEqual(snapshot["unseen_category_rate"], 0.5)
        self.assertNotIn("records", snapshot)
        self.assertNotIn("features", snapshot)
        self.assertNotIn("payload", snapshot)

    def test_alerts_fire_on_stress(self) -> None:
        telemetry = ShadowTelemetry()
        for _ in range(20):
            telemetry.record_request(250.0, error=True)
            telemetry.record_scores([
                {
                    "frequency_log_ratio": 1.0,
                    "pure_premium_log_ratio": 1.5,
                    "warnings": ["unseen_category:vehicle_brand=NEW"],
                }
            ])
        snapshot = telemetry.snapshot()
        self.assertEqual(snapshot["alert_status"], "RED")
        self.assertTrue(snapshot["alerts"]["error_rate"])
        self.assertTrue(snapshot["alerts"]["unseen_category_rate"])
        self.assertTrue(snapshot["alerts"]["p95_latency_ms"])
        self.assertTrue(snapshot["alerts"]["frequency_disagreement"])
        self.assertTrue(snapshot["alerts"]["pure_premium_disagreement"])

    def test_feature_psi_uses_aggregate_bins(self) -> None:
        baseline = {
            "numeric": {
                "driver_age": {
                    "cut_points": [30.0, 50.0],
                    "expected_proportions": [0.3, 0.4, 0.3, 0.0],
                    "missing_bucket": 3,
                }
            },
            "categorical": {
                "vehicle_brand": {
                    "expected_proportions": {
                        "A": 0.5,
                        "B": 0.5,
                        "__MISSING__": 0.0,
                        "__UNSEEN__": 0.0,
                    }
                }
            },
        }
        telemetry = ShadowTelemetry(monitoring_baseline=baseline)
        scores = [
            {"frequency_log_ratio": 0.1, "pure_premium_log_ratio": 0.1, "warnings": []}
            for _ in range(20)
        ]
        records = [
            {"driver_age": 80.0, "vehicle_brand": "NEW"}
            for _ in range(20)
        ]
        telemetry.record_scores(scores, records)
        snapshot = telemetry.snapshot()
        self.assertGreater(snapshot["feature_drift"]["max_psi"], 0.25)
        self.assertTrue(snapshot["alerts"]["feature_drift"])
        self.assertIn(snapshot["feature_drift"]["max_psi_feature"], {"driver_age", "vehicle_brand"})
        self.assertNotIn("records", snapshot["feature_drift"])

    def test_reset_clears_aggregates(self) -> None:
        telemetry = ShadowTelemetry()
        telemetry.record_request(10.0)
        telemetry.record_scores([
            {"frequency_log_ratio": 0.1, "pure_premium_log_ratio": 0.2, "warnings": []}
        ])
        telemetry.reset()
        snapshot = telemetry.snapshot()
        self.assertEqual(snapshot["request_count"], 0)
        self.assertEqual(snapshot["records_scored"], 0)
        self.assertEqual(snapshot["alert_status"], "GREEN")


if __name__ == "__main__":
    unittest.main()
