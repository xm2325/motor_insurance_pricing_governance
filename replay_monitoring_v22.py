from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ.setdefault("MODEL_BUNDLE_DIR", "deployment_artifacts")

from deployment.app import app, get_telemetry  # noqa: E402

OUTDIR = Path("results_v22")
BUNDLE = Path(os.environ["MODEL_BUNDLE_DIR"])


def load_records() -> list[dict]:
    payload = json.loads((BUNDLE / "parity_reference.json").read_text(encoding="utf-8"))
    return payload["records"]


def stress_record(record: dict) -> dict:
    stressed = dict(record)
    stressed["vehicle_brand"] = "V22_UNSEEN_BRAND"
    stressed["driver_age"] = 18.0
    stressed["vehicle_age"] = 30.0
    stressed["vehicle_value"] = 200000.0
    stressed["power_to_weight_ratio"] = 1.0
    return stressed


def disagreement_shift(baseline: dict, stress: dict) -> dict:
    base_f = float(baseline["disagreement"]["frequency_abs_log_ratio_p95"])
    stress_f = float(stress["disagreement"]["frequency_abs_log_ratio_p95"])
    base_p = float(baseline["disagreement"]["pure_premium_abs_log_ratio_p95"])
    stress_p = float(stress["disagreement"]["pure_premium_abs_log_ratio_p95"])
    return {
        "frequency_p95_baseline": base_f,
        "frequency_p95_stress": stress_f,
        "frequency_ratio": stress_f / max(base_f, 1e-12),
        "pure_premium_p95_baseline": base_p,
        "pure_premium_p95_stress": stress_p,
        "pure_premium_ratio": stress_p / max(base_p, 1e-12),
        "relative_alert_rule": "stress p95 > max(1.5 * baseline p95, baseline p95 + 0.10)",
        "frequency_relative_alert": stress_f > max(1.5 * base_f, base_f + 0.10),
        "pure_premium_relative_alert": stress_p > max(1.5 * base_p, base_p + 0.10),
    }


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    client = TestClient(app)
    records = load_records()
    telemetry = get_telemetry()

    # Warm the fitted pipelines before defining a steady-state latency baseline.
    warmup = client.post("/batch-score", json={"policies": records})
    warmup.raise_for_status()
    cold_start_snapshot = client.get("/monitoring").json()

    telemetry.reset()
    for _ in range(10):
        response = client.post("/batch-score", json={"policies": records})
        response.raise_for_status()
    baseline = client.get("/monitoring").json()

    telemetry.reset()
    malformed = dict(records[0])
    malformed["total_claims"] = 3
    for _ in range(20):
        response = client.post("/score", json=malformed)
        if response.status_code != 422:
            raise RuntimeError(f"Expected 422 for forbidden field, got {response.status_code}")

    stressed = [stress_record(record) for record in records]
    for _ in range(10):
        response = client.post("/batch-score", json={"policies": stressed})
        response.raise_for_status()
    stress = client.get("/monitoring").json()

    shifts = disagreement_shift(baseline, stress)
    checks = {
        "cold_start_recorded_separately": cold_start_snapshot["request_count"] == 1,
        "baseline_privacy_boundary": baseline["privacy_boundary"] == "aggregate_non_pii_only",
        "stress_privacy_boundary": stress["privacy_boundary"] == "aggregate_non_pii_only",
        "baseline_alert_status": baseline["alert_status"],
        "baseline_records_scored": baseline["records_scored"],
        "stress_records_scored": stress["records_scored"],
        "stress_error_rate_alert": bool(stress["alerts"]["error_rate"]),
        "stress_unseen_category_alert": bool(stress["alerts"]["unseen_category_rate"]),
        "stress_unseen_category_rate": float(stress["unseen_category_rate"]),
        "frequency_relative_alert": bool(shifts["frequency_relative_alert"]),
        "pure_premium_relative_alert": bool(shifts["pure_premium_relative_alert"]),
    }
    if baseline["alert_status"] != "GREEN":
        raise RuntimeError(f"Steady-state baseline should be GREEN, got {baseline['alerts']}")
    if not checks["baseline_privacy_boundary"] or not checks["stress_privacy_boundary"]:
        raise RuntimeError("Monitoring snapshot violated aggregate-only privacy boundary")
    if not checks["stress_error_rate_alert"]:
        raise RuntimeError("Stress replay failed to trigger error-rate alert")
    if not checks["stress_unseen_category_alert"]:
        raise RuntimeError("Stress replay failed to trigger unseen-category alert")
    if not checks["frequency_relative_alert"] or not checks["pure_premium_relative_alert"]:
        raise RuntimeError("Stress replay failed to trigger relative disagreement-shift alerts")

    payload = {
        "status": "success",
        "interpretation": (
            "Synthetic replay validation only. Cold start is recorded separately from the "
            "steady-state baseline. Alerts demonstrate monitoring behaviour; they are not "
            "observed production incidents or insurer thresholds."
        ),
        "cold_start": cold_start_snapshot,
        "baseline": baseline,
        "stress": stress,
        "disagreement_shift": shifts,
        "checks": checks,
    }
    (OUTDIR / "monitoring_replay_summary.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(json.dumps({"status": "success", "checks": checks, "disagreement_shift": shifts}, indent=2))


if __name__ == "__main__":
    main()
