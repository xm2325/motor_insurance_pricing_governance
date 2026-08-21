from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from deployment.bundle import ShadowModelBundle
from deployment.contracts import BatchScoreRequest, PricingFeatures

app = FastAPI(
    title="Motor Pricing Shadow Scoring Service",
    version="0.21",
    description=(
        "Reference/challenger risk scoring for governance and shadow comparison only. "
        "The current model-family decision is HOLD; this service does not set customer premiums."
    ),
)


@lru_cache(maxsize=1)
def get_bundle() -> ShadowModelBundle:
    root = Path(os.environ.get("MODEL_BUNDLE_DIR", "deployment_artifacts"))
    return ShadowModelBundle.load(root)


@app.get("/health")
def health() -> dict[str, Any]:
    bundle = get_bundle()
    return {
        "status": "ok",
        "model_version": bundle.manifest["model_version"],
        "governance_status": bundle.manifest["governance_status"],
        "feature_contract_hash": bundle.manifest["feature_contract_hash"],
    }


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    bundle = get_bundle()
    return {
        "model_version": bundle.manifest["model_version"],
        "governance_status": bundle.manifest["governance_status"],
        "train_year": bundle.manifest["train_year"],
        "calibration_year": bundle.manifest["calibration_year"],
        "evaluation_year": bundle.manifest["evaluation_year"],
        "models": bundle.manifest["models"],
        "interpretation_boundary": bundle.manifest["interpretation_boundary"],
    }


@app.post("/score")
def score(policy: PricingFeatures) -> dict[str, Any]:
    return get_bundle().score_records([policy.as_model_record()])[0]


@app.post("/batch-score")
def batch_score(request: BatchScoreRequest) -> dict[str, Any]:
    records = [policy.as_model_record() for policy in request.policies]
    scores = get_bundle().score_records(records)
    return {
        "count": len(scores),
        "model_version": get_bundle().manifest["model_version"],
        "governance_status": get_bundle().manifest["governance_status"],
        "scores": scores,
    }
