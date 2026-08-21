from __future__ import annotations

import unittest

from deployment.review import ReviewLifecycle, aggregate_evidence, evidence_digest


def snapshot(*, alerts: dict[str, bool], max_psi: float = 0.0, max_feature: str | None = None):
    return {
        "service_version": "0.22",
        "model_version": "v0.21-shadow-2022-train-2023-calibration",
        "governance_status": "HOLD_SHADOW_ONLY",
        "privacy_boundary": "aggregate_non_pii_only",
        "request_count": 5,
        "records_scored": 5000,
        "error_rate": 0.0,
        "unseen_category_rate": 0.0,
        "latency_ms": {"p95": 80.0},
        "disagreement": {
            "frequency_abs_log_ratio_p95": 0.3,
            "pure_premium_abs_log_ratio_p95": 0.8,
        },
        "feature_drift": {
            "max_psi": max_psi,
            "max_psi_feature": max_feature,
            "alert_eligible": True,
        },
        "alerts": alerts,
    }


class TestReviewLifecycle(unittest.TestCase):
    def test_two_breaches_open_and_two_green_close(self) -> None:
        green = snapshot(alerts={"feature_drift": False})
        drift = snapshot(alerts={"feature_drift": True}, max_psi=1.4, max_feature="business_type")
        lifecycle = ReviewLifecycle(open_after_breaches=2, close_after_green=2)
        states = [
            lifecycle.observe(green, "green")["state"],
            lifecycle.observe(drift, "drift-1")["state"],
            lifecycle.observe(drift, "drift-2")["state"],
            lifecycle.observe(green, "recover-1")["state"],
            lifecycle.observe(green, "recover-2")["state"],
        ]
        self.assertEqual(states, ["HEALTHY", "WATCH", "REVIEW_REQUIRED", "RECOVERING", "HEALTHY"])
        self.assertEqual(
            lifecycle.history[2]["recommended_action"],
            "REVIEW_PORTFOLIO_MIX_AND_SEGMENT_CALIBRATION",
        )
        self.assertIsNone(lifecycle.review_id)

    def test_high_severity_stress_recommends_joint_investigation(self) -> None:
        stress = snapshot(
            alerts={
                "error_rate": True,
                "unseen_category_rate": True,
                "frequency_disagreement": True,
                "pure_premium_disagreement": True,
                "feature_drift": True,
            },
            max_psi=20.0,
            max_feature="vehicle_brand",
        )
        lifecycle = ReviewLifecycle(open_after_breaches=2, close_after_green=2)
        lifecycle.observe(stress, "stress-1")
        event = lifecycle.observe(stress, "stress-2")
        self.assertEqual(event["state"], "REVIEW_REQUIRED")
        self.assertEqual(event["severity"], "HIGH")
        self.assertEqual(event["recommended_action"], "INVESTIGATE_SERVING_DATA_AND_MODEL")

    def test_evidence_is_aggregate_and_digest_is_deterministic(self) -> None:
        source = snapshot(alerts={"feature_drift": True}, max_psi=1.4, max_feature="business_type")
        first = aggregate_evidence(source, "window")
        second = aggregate_evidence(source, "window")
        self.assertEqual(evidence_digest(first), evidence_digest(second))
        self.assertNotIn("records", first)
        self.assertNotIn("payload", first)
        self.assertNotIn("features", first)
        self.assertEqual(first["privacy_boundary"], "aggregate_non_pii_only")

    def test_controller_never_claims_automatic_model_change(self) -> None:
        lifecycle = ReviewLifecycle()
        result = lifecycle.snapshot()
        boundary = result["automation_boundary"].lower()
        self.assertIn("no automatic pricing", boundary)
        self.assertIn("model promotion", boundary)


if __name__ == "__main__":
    unittest.main()
