from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("MODEL_BUNDLE_DIR", "deployment_artifacts")

from build_deployment_bundle_v21 import canonicalise_features, records_from_frame  # noqa: E402
from deployment.app import app, get_telemetry  # noqa: E402
from run_spanish_oot_2024 import load_data  # noqa: E402

OUTDIR = Path("results_v22")
SAMPLE_SIZE = 5000
BATCH_SIZE = 1000


def stress_record(record: dict) -> dict:
    stressed = dict(record)
    stressed["vehicle_brand"] = "V22_UNSEEN_BRAND"
    stressed["driver_age"] = 18.0
    stressed["vehicle_age"] = 30.0
    stressed["vehicle_value"] = 200000.0
    stressed["power_to_weight_ratio"] = 1.0
    return stressed


def score_batches(client: TestClient, records: list[dict]) -> None:
    for start in range(0, len(records), BATCH_SIZE):
        response = client.post(
            "/batch-score",
            json={"policies": records[start : start + BATCH_SIZE]},
        )
        response.raise_for_status()


def disagreement_shift(baseline: dict, comparison: dict) -> dict:
    base_f = float(baseline["disagreement"]["frequency_abs_log_ratio_p95"])
    comp_f = float(comparison["disagreement"]["frequency_abs_log_ratio_p95"])
    base_p = float(baseline["disagreement"]["pure_premium_abs_log_ratio_p95"])
    comp_p = float(comparison["disagreement"]["pure_premium_abs_log_ratio_p95"])
    return {
        "frequency_p95_baseline": base_f,
        "frequency_p95_comparison": comp_f,
        "frequency_ratio": comp_f / max(base_f, 1e-12),
        "pure_premium_p95_baseline": base_p,
        "pure_premium_p95_comparison": comp_p,
        "pure_premium_ratio": comp_p / max(base_p, 1e-12),
        "relative_alert_rule": "comparison p95 > max(1.5 * baseline p95, baseline p95 + 0.10)",
        "frequency_relative_alert": comp_f > max(1.5 * base_f, base_f + 0.10),
        "pure_premium_relative_alert": comp_p > max(1.5 * base_p, base_p + 0.10),
    }


def categorical_distribution(frame, field: str) -> dict[str, float]:
    counts = frame[field].astype("string").fillna("__MISSING__").value_counts(normalize=True)
    return {str(key): float(value) for key, value in counts.sort_index().items()}


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    telemetry = get_telemetry()
    df = load_data()

    train_full = df[df["year"] == 2022]
    test_full = df[df["year"] == 2024]
    train_sample = train_full.sample(SAMPLE_SIZE, random_state=42)
    test_sample = test_full.sample(SAMPLE_SIZE, random_state=42)
    train_records = records_from_frame(canonicalise_features(train_sample))
    temporal_records = records_from_frame(canonicalise_features(test_sample))

    business_mix = {
        "2022": categorical_distribution(train_full, "business_type"),
        "2024": categorical_distribution(test_full, "business_type"),
    }

    # Warm model execution separately from steady-state monitoring.
    warmup = client.post("/batch-score", json={"policies": train_records[:100]})
    warmup.raise_for_status()
    cold_start_snapshot = client.get("/monitoring").json()

    telemetry.reset()
    score_batches(client, train_records)
    baseline = client.get("/monitoring").json()

    telemetry.reset()
    score_batches(client, temporal_records)
    temporal_2024 = client.get("/monitoring").json()

    telemetry.reset()
    malformed = dict(train_records[0])
    malformed["total_claims"] = 3
    for _ in range(20):
        response = client.post("/score", json=malformed)
        if response.status_code != 422:
            raise RuntimeError(f"Expected 422 for forbidden field, got {response.status_code}")

    stressed = [stress_record(record) for record in train_records]
    score_batches(client, stressed)
    stress = client.get("/monitoring").json()

    temporal_shift = disagreement_shift(baseline, temporal_2024)
    stress_shift = disagreement_shift(baseline, stress)
    checks = {
        "cold_start_recorded_separately": cold_start_snapshot["request_count"] == 1,
        "baseline_privacy_boundary": baseline["privacy_boundary"] == "aggregate_non_pii_only",
        "temporal_privacy_boundary": temporal_2024["privacy_boundary"] == "aggregate_non_pii_only",
        "stress_privacy_boundary": stress["privacy_boundary"] == "aggregate_non_pii_only",
        "baseline_alert_status": baseline["alert_status"],
        "baseline_records_scored": baseline["records_scored"],
        "temporal_records_scored": temporal_2024["records_scored"],
        "stress_records_scored": stress["records_scored"],
        "stress_error_rate_alert": bool(stress["alerts"]["error_rate"]),
        "stress_unseen_category_alert": bool(stress["alerts"]["unseen_category_rate"]),
        "stress_feature_drift_alert": bool(stress["alerts"]["feature_drift"]),
        "stress_unseen_category_rate": float(stress["unseen_category_rate"]),
        "frequency_relative_alert": bool(stress_shift["frequency_relative_alert"]),
        "pure_premium_relative_alert": bool(stress_shift["pure_premium_relative_alert"]),
    }
    if baseline["alert_status"] != "GREEN":
        raise RuntimeError(f"Training-distribution baseline should be GREEN, got {baseline['alerts']}")
    if not all(
        checks[key]
        for key in [
            "baseline_privacy_boundary",
            "temporal_privacy_boundary",
            "stress_privacy_boundary",
        ]
    ):
        raise RuntimeError("Monitoring snapshot violated aggregate-only privacy boundary")
    if not checks["stress_error_rate_alert"]:
        raise RuntimeError("Stress replay failed to trigger error-rate alert")
    if not checks["stress_unseen_category_alert"]:
        raise RuntimeError("Stress replay failed to trigger unseen-category alert")
    if not checks["stress_feature_drift_alert"]:
        raise RuntimeError("Stress replay failed to trigger feature-drift alert")
    if not checks["frequency_relative_alert"] or not checks["pure_premium_relative_alert"]:
        raise RuntimeError("Stress replay failed to trigger relative disagreement-shift alerts")

    payload = {
        "status": "success",
        "interpretation": (
            "The 2022 sample is a monitoring-control replay, the 2024 sample is real temporal "
            "feature/score transport, and the final stress is synthetic. Cold start is recorded "
            "separately. Alert thresholds are project demonstration rules, not insurer SLAs or "
            "regulatory thresholds."
        ),
        "sample_size_per_replay": SAMPLE_SIZE,
        "business_type_distribution_full_year": business_mix,
        "cold_start": cold_start_snapshot,
        "baseline_2022": baseline,
        "temporal_2024": temporal_2024,
        "synthetic_stress": stress,
        "temporal_disagreement_shift": temporal_shift,
        "stress_disagreement_shift": stress_shift,
        "checks": checks,
    }
    (OUTDIR / "monitoring_replay_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "status": "success",
        "checks": checks,
        "business_type_distribution_full_year": business_mix,
        "temporal_feature_drift": temporal_2024["feature_drift"],
        "temporal_disagreement_shift": temporal_shift,
        "stress_disagreement_shift": stress_shift,
    }, indent=2))


if __name__ == "__main__":
    main()
