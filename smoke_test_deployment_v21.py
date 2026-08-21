from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

os.environ.setdefault("MODEL_BUNDLE_DIR", "deployment_artifacts")

from deployment.app import app, get_bundle  # noqa: E402

OUTDIR = Path(os.environ["MODEL_BUNDLE_DIR"])


def main() -> None:
    parity = json.loads((OUTDIR / "parity_reference.json").read_text(encoding="utf-8"))
    client = TestClient(app)
    get_bundle.cache_clear()

    health = client.get("/health")
    health.raise_for_status()
    assert health.json()["governance_status"] == "HOLD_SHADOW_ONLY"

    info = client.get("/model-info")
    info.raise_for_status()
    assert info.json()["evaluation_year"] == 2024

    response = client.post("/batch-score", json={"policies": parity["records"]})
    response.raise_for_status()
    online = response.json()["scores"]
    assert len(online) == len(parity["scores"])

    score_fields = [
        "reference_frequency",
        "challenger_frequency",
        "reference_pure_premium",
        "challenger_pure_premium",
    ]
    max_abs_error = 0.0
    for expected, observed in zip(parity["scores"], online):
        for field in score_fields:
            error = abs(float(expected[field]) - float(observed[field]))
            max_abs_error = max(max_abs_error, error)
            assert np.isclose(expected[field], observed[field], rtol=1e-10, atol=1e-10)

    repeated = client.post("/batch-score", json={"policies": parity["records"]})
    repeated.raise_for_status()
    assert repeated.json()["scores"] == online

    forbidden = dict(parity["records"][0])
    forbidden["total_claims"] = 99
    rejected = client.post("/score", json=forbidden)
    assert rejected.status_code == 422

    unseen = dict(parity["records"][0])
    unseen["vehicle_brand"] = "UNSEEN_V21_BRAND"
    unseen_response = client.post("/score", json=unseen)
    unseen_response.raise_for_status()
    assert any(
        warning.startswith("unseen_category:vehicle_brand=")
        for warning in unseen_response.json()["warnings"]
    )

    benchmark_policy = parity["records"][0]
    benchmark_payload = {"policies": [benchmark_policy] * 1000}
    timings_ms = []
    for _ in range(5):
        start = time.perf_counter()
        benchmark = client.post("/batch-score", json=benchmark_payload)
        benchmark.raise_for_status()
        timings_ms.append((time.perf_counter() - start) * 1000.0)
        assert benchmark.json()["count"] == 1000

    summary = {
        "status": "success",
        "governance_status": health.json()["governance_status"],
        "parity_records": len(parity["records"]),
        "offline_online_max_abs_error": max_abs_error,
        "forbidden_outcome_field_rejected": True,
        "unseen_category_warning_emitted": True,
        "batch_deterministic": True,
        "batch_size_tested": 1000,
        "testclient_batch_latency_ms": {
            "median": float(np.median(timings_ms)),
            "p95": float(np.quantile(timings_ms, 0.95)),
        },
    }
    (OUTDIR / "deployment_smoke_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    (OUTDIR / "openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
