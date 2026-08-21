from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi import FastAPI, Request

from deployment.bundle import ShadowModelBundle
from deployment.contracts import BatchScoreRequest, PricingFeatures
from deployment.monitoring import ShadowTelemetry

SERVICE_VERSION = "0.27"

app = FastAPI(
    title="Motor Pricing Shadow Scoring Service",
    version=SERVICE_VERSION,
    description=(
        "Reference/challenger risk scoring for governance and shadow comparison only. "
        "The current model-family decision is HOLD; this service does not set customer premiums."
    ),
)


@lru_cache(maxsize=1)
def get_bundle() -> ShadowModelBundle:
    root = Path(os.environ.get("MODEL_BUNDLE_DIR", "deployment_artifacts"))
    return ShadowModelBundle.load(root)


@lru_cache(maxsize=1)
def get_telemetry() -> ShadowTelemetry:
    bundle = get_bundle()
    return ShadowTelemetry(monitoring_baseline=bundle.manifest.get("monitoring_baseline"))


@app.middleware("http")
async def scoring_telemetry(request: Request, call_next):
    if request.url.path not in {"/score", "/batch-score"}:
        return await call_next(request)
    start = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        get_telemetry().record_request((perf_counter() - start) * 1000.0, error=True)
        raise
    get_telemetry().record_request(
        (perf_counter() - start) * 1000.0,
        error=response.status_code >= 400,
    )
    return response


def _integrity_payload(bundle: ShadowModelBundle) -> dict[str, Any]:
    if bundle.bundle_integrity is None:
        return {
            "status": "LEGACY_UNLOCKED_BUNDLE",
            "lock_digest_sha256": None,
            "artifact_count": None,
        }
    return bundle.bundle_integrity.as_dict()


@app.get("/health")
def health() -> dict[str, Any]:
    bundle = get_bundle()
    integrity = _integrity_payload(bundle)
    return {
        "status": "ok",
        "service_version": SERVICE_VERSION,
        "model_version": bundle.manifest["model_version"],
        "governance_status": bundle.manifest["governance_status"],
        "feature_contract_hash": bundle.manifest["feature_contract_hash"],
        "environment_compatibility": bundle.environment_compatibility.status,
        "bundle_integrity": integrity["status"],
        "bundle_lock_digest_sha256": integrity["lock_digest_sha256"],
    }


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    bundle = get_bundle()
    return {
        "service_version": SERVICE_VERSION,
        "bundle_contract_version": bundle.manifest.get("bundle_contract_version"),
        "model_version": bundle.manifest["model_version"],
        "governance_status": bundle.manifest["governance_status"],
        "train_year": bundle.manifest["train_year"],
        "calibration_year": bundle.manifest["calibration_year"],
        "evaluation_year": bundle.manifest["evaluation_year"],
        "models": bundle.manifest["models"],
        "serialization": bundle.manifest.get("serialization"),
        "integrity_contract": bundle.manifest.get("integrity"),
        "bundle_integrity": _integrity_payload(bundle),
        "environment_compatibility": bundle.environment_compatibility.as_dict(),
        "monitoring_baseline_source": bundle.manifest.get("monitoring_baseline", {}).get("source"),
        "interpretation_boundary": bundle.manifest["interpretation_boundary"],
    }


@app.get("/monitoring")
def monitoring() -> dict[str, Any]:
    bundle = get_bundle()
    return {
        "service_version": SERVICE_VERSION,
        "model_version": bundle.manifest["model_version"],
        "governance_status": bundle.manifest["governance_status"],
        **get_telemetry().snapshot(),
    }


@app.post("/score")
def score(policy: PricingFeatures) -> dict[str, Any]:
    records = [policy.as_model_record()]
    scores = get_bundle().score_records(records)
    get_telemetry().record_scores(scores, records)
    return scores[0]


@app.post("/batch-score")
def batch_score(request: BatchScoreRequest) -> dict[str, Any]:
    records = [policy.as_model_record() for policy in request.policies]
    scores = get_bundle().score_records(records)
    get_telemetry().record_scores(scores, records)
    return {
        "count": len(scores),
        "model_version": get_bundle().manifest["model_version"],
        "governance_status": get_bundle().manifest["governance_status"],
        "scores": scores,
    }
