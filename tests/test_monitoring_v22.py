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
